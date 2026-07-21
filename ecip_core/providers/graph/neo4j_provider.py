import datetime
from typing import List, Dict, Any, Optional

from ecip_core.graph.provider import GraphProvider
from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


class Neo4jGraphProvider(GraphProvider):
    """
    Neo4j Graph Database implementation of GraphProvider.
    """

    def __init__(self, uri: str = "bolt://localhost:7687", username: str = "neo4j", password: str = "password"):
        self.uri = uri
        self.username = username
        self.password = password
        self.driver = None

    def connect(self) -> None:
        """Establishes connection to the Neo4j instance."""
        try:
            from neo4j import GraphDatabase
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password)
            )
            self.driver.verify_connectivity()
            logger.info("Neo4j connected")
        except Exception as e:
            logger.error(f"Connection failure to Neo4j: {e}")
            raise RuntimeError(f"Neo4j connection failed: {e}")

    def close(self) -> None:
        """Closes the connection driver."""
        if self.driver:
            self.driver.close()
            self.driver = None

    def _ensure_connected(self):
        if self.driver is None:
            self.connect()

    def create_node(self, label: str, properties: Dict[str, Any]) -> None:
        """Creates or updates a single node in the graph."""
        if label not in {"Project", "Package", "Class", "Interface", "Method", "Field"}:
            raise ValueError(f"Unsupported node type: {label}")
        
        self._ensure_connected()
        node_id = properties.get("id")
        project_id = properties.get("project_id", "default")
        
        if not node_id:
            raise ValueError("Node properties must contain 'id'")
            
        with self.driver.session() as session:
            query = f"""
            MERGE (n:{label} {{id: $node_id, project_id: $project_id}})
            SET n += $properties
            """
            session.run(query, node_id=node_id, project_id=project_id, properties=properties)

    def create_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> None:
        """Creates a relationship between two nodes."""
        if rel_type not in {"DEPENDS_ON", "IMPLEMENTS", "EXTENDS", "CALLS", "REFERENCES"}:
            raise ValueError(f"Unsupported relationship type: {rel_type}")

        self._ensure_connected()
        props = properties or {}
        project_id = props.get("project_id", "default")

        with self.driver.session() as session:
            query = f"""
            MERGE (a:Class {{id: $source_id, project_id: $project_id}})
            MERGE (b:Class {{id: $target_id, project_id: $project_id}})
            MERGE (a)-[r:{rel_type}]->(b)
            SET r += $properties
            """
            session.run(query, source_id=source_id, target_id=target_id, project_id=project_id, properties=props)

    def batch_insert_nodes(self, nodes: List[Dict[str, Any]]) -> None:
        """Optimized insertion of multiple nodes using Cypher UNWIND."""
        if not nodes:
            return

        self._ensure_connected()
        by_label = {}
        for n in nodes:
            lbl = n.get("type", "Class")
            if lbl not in {"Project", "Package", "Class", "Interface", "Method", "Field"}:
                lbl = "Class"
            props = n.get("properties") or {}
            if "id" not in props or "project_id" not in props:
                continue
            by_label.setdefault(lbl, []).append(props)

        with self.driver.session() as session:
            for lbl, props_list in by_label.items():
                query = f"""
                UNWIND $batch as props
                MERGE (n:{lbl} {{id: props.id, project_id: props.project_id}})
                SET n += props
                """
                session.run(query, batch=props_list)
        logger.info("Batch committed: nodes synchronized")

    def batch_insert_relationships(self, relationships: List[Dict[str, Any]]) -> None:
        """Optimized insertion of multiple relationships using Cypher UNWIND."""
        if not relationships:
            return

        self._ensure_connected()
        by_type = {}
        for r in relationships:
            rel_type = r.get("type", "DEPENDS_ON")
            if rel_type not in {"DEPENDS_ON", "IMPLEMENTS", "EXTENDS", "CALLS", "REFERENCES"}:
                rel_type = "DEPENDS_ON"
            
            props = r.get("properties") or {}
            project_id = props.get("project_id", "default")
            
            by_type.setdefault(rel_type, []).append({
                "source_id": r.get("source_id"),
                "target_id": r.get("target_id"),
                "properties": props,
                "project_id": project_id
            })

        with self.driver.session() as session:
            for rel_type, rels_list in by_type.items():
                query = f"""
                UNWIND $batch as row
                MERGE (a:Class {{id: row.source_id, project_id: row.project_id}})
                MERGE (b:Class {{id: row.target_id, project_id: row.project_id}})
                MERGE (a)-[r:{rel_type}]->(b)
                SET r += row.properties
                """
                session.run(query, batch=rels_list)
        logger.info("Batch committed: relationships synchronized")

    def execute_transaction(self, queries: List[tuple]) -> None:
        """Executes multiple Cypher statements inside a single ACID transaction transaction block."""
        self._ensure_connected()
        with self.driver.session() as session:
            with session.begin_transaction() as tx:
                try:
                    for query_str, params in queries:
                        tx.run(query_str, params or {})
                except Exception as e:
                    logger.error(f"Transaction rollback: {e}")
                    raise e

    def query(self, query_str: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Run custom query statement and return rows."""
        self._ensure_connected()
        with self.driver.session() as session:
            result = session.run(query_str, parameters or {})
            return [dict(record) for record in result]

    def save_edge(
        self,
        project_id: str,
        source_class: str,
        target_class: str,
        relationship_type: str
    ) -> bool:
        """Save a class edge for backward compatibility."""
        if relationship_type not in {"DEPENDS_ON", "IMPLEMENTS", "EXTENDS", "CALLS", "REFERENCES"}:
            relationship_type = "DEPENDS_ON"

        self._ensure_connected()
        with self.driver.session() as session:
            # Check duplicate
            dup_query = f"""
            MATCH (a:Class {{id: $source_class, project_id: $project_id}})-[r:{relationship_type}]->(b:Class {{id: $target_class, project_id: $project_id}})
            RETURN r LIMIT 1
            """
            res = session.run(dup_query, source_class=source_class, target_class=target_class, project_id=project_id)
            if res.peek():
                return False

            discovered_at = datetime.datetime.utcnow().isoformat() + "Z"
            query = f"""
            MERGE (a:Class {{id: $source_class, project_id: $project_id}})
            MERGE (b:Class {{id: $target_class, project_id: $project_id}})
            MERGE (a)-[r:{relationship_type}]->(b)
            SET r.discovered_at = $discovered_at
            """
            session.run(query, source_class=source_class, target_class=target_class, project_id=project_id, discovered_at=discovered_at)
            return True

    def get_edges(self, project_id: str) -> List[Dict[str, Any]]:
        self._ensure_connected()
        with self.driver.session() as session:
            query = """
            MATCH (a:Class {project_id: $project_id})-[r]->(b:Class {project_id: $project_id})
            RETURN a.id AS source_class, b.id AS target_class, type(r) AS relationship_type, r.discovered_at AS discovered_at
            """
            result = session.run(query, project_id=project_id)
            return [dict(record) for record in result]

    def get_outgoing_edges(self, project_id: str, class_name: str) -> List[Dict[str, Any]]:
        self._ensure_connected()
        with self.driver.session() as session:
            query = """
            MATCH (a:Class {id: $class_name, project_id: $project_id})-[r]->(b:Class {project_id: $project_id})
            RETURN a.id AS source_class, b.id AS target_class, type(r) AS relationship_type, r.discovered_at AS discovered_at
            """
            result = session.run(query, class_name=class_name, project_id=project_id)
            return [dict(record) for record in result]

    def get_incoming_edges(self, project_id: str, class_name: str) -> List[Dict[str, Any]]:
        self._ensure_connected()
        with self.driver.session() as session:
            query = """
            MATCH (a:Class {project_id: $project_id})-[r]->(b:Class {id: $class_name, project_id: $project_id})
            RETURN a.id AS source_class, b.id AS target_class, type(r) AS relationship_type, r.discovered_at AS discovered_at
            """
            result = session.run(query, class_name=class_name, project_id=project_id)
            return [dict(record) for record in result]

    def get_all_class_edges(self, project_id: str, class_name: str) -> List[Dict[str, Any]]:
        self._ensure_connected()
        with self.driver.session() as session:
            query = """
            MATCH (a:Class {project_id: $project_id})-[r]->(b:Class {project_id: $project_id})
            WHERE a.id = $class_name OR b.id = $class_name
            RETURN a.id AS source_class, b.id AS target_class, type(r) AS relationship_type, r.discovered_at AS discovered_at
            """
            result = session.run(query, class_name=class_name, project_id=project_id)
            return [dict(record) for record in result]

    def get_graph_stats(self, project_id: str) -> Dict[str, Any]:
        self._ensure_connected()
        with self.driver.session() as session:
            query = """
            MATCH (a:Class {project_id: $project_id})-[r]->(b:Class {project_id: $project_id})
            RETURN count(r) AS total_edges
            """
            val = session.run(query, project_id=project_id).single()
            total_edges = val["total_edges"] if val else 0
            return {"total_edges": total_edges}

    def delete_class_edges(self, project_id: str, class_name: str) -> None:
        self._ensure_connected()
        with self.driver.session() as session:
            query = """
            MATCH (a:Class {id: $class_name, project_id: $project_id})-[r]->(b:Class {project_id: $project_id})
            DELETE r
            """
            session.run(query, class_name=class_name, project_id=project_id)

    def delete_project(self, project_id: str) -> None:
        self._ensure_connected()
        with self.driver.session() as session:
            query = """
            MATCH (n {project_id: $project_id})
            DETACH DELETE n
            """
            session.run(query, project_id=project_id)
            logger.info("Graph synchronized: project removed")
