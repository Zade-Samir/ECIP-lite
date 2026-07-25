import time
from typing import List, Dict, Any, Optional
from ecip_core.common.logger import get_logger
from ecip_core.parser.models.parsed_java_file import ParsedJavaFile
from ecip_core.graph.factory import get_graph_provider

logger = get_logger(__name__)


class GraphSynchronizer:
    """
    Handles incremental synchronization of Project, Package, Class, and Method nodes
    and their structural relationships in the active GraphProvider.
    """

    def __init__(self, provider=None):
        self._provider = provider

    @property
    def provider(self):
        if self._provider is None:
            self._provider = get_graph_provider()
        return self._provider

    def execute_with_retry(
        self,
        queries: List[tuple],
        max_retries: int = 3,
        initial_delay: float = 0.5
    ) -> None:
        """
        Executes a list of Cypher/SQL statements inside a single transaction with exponential backoff retries.
        """
        delay = initial_delay
        for attempt in range(1, max_retries + 1):
            try:
                if hasattr(self.provider, "execute_transaction"):
                    self.provider.execute_transaction(queries)
                else:
                    # Fallback to individual queries
                    for query_str, params in queries:
                        self.provider.query(query_str, params)
                return
            except Exception as e:
                logger.warning("Partial synchronization")
                logger.warning("Retry scheduled")
                time.sleep(delay)
                delay *= 2
                if attempt == max_retries:
                    logger.error("Transaction failure")
                    logger.error("Synchronization aborted")
                    raise e

    def sync_class(self, project_id: str, parsed_file: ParsedJavaFile) -> None:
        """
        Synchronizes Class, Package, and Method nodes for a parsed Java file in the graph database.
        """
        class_name = parsed_file.class_name
        if not class_name:
            return

        is_neo4j = self.provider.__class__.__name__ == "Neo4jGraphProvider"
        if not is_neo4j:
            return

        logger.info("Sync started")

        package_name = parsed_file.package_name or ""
        file_path = parsed_file.file_path
        project_node_id = project_id
        package_node_id = f"{project_id}:{package_name}" if package_name else ""
        class_node_id = f"{project_id}:{class_name}"

        queries = []

        # 1. Project node
        queries.append((
            "MERGE (p:Project {id: $project_id}) ON CREATE SET p.name = $project_id",
            {"project_id": project_node_id}
        ))

        # 2. Package node and HAS_PACKAGE relationship
        if package_name:
            queries.append((
                """
                MERGE (pkg:Package {id: $package_id, project_id: $project_id})
                ON CREATE SET pkg.name = $package_name
                """,
                {"package_id": package_node_id, "project_id": project_id, "package_name": package_name}
            ))
            queries.append((
                """
                MATCH (p:Project {id: $project_id})
                MATCH (pkg:Package {id: $package_id, project_id: $project_id})
                MERGE (p)-[:HAS_PACKAGE]->(pkg)
                """,
                {"project_id": project_node_id, "package_id": package_node_id}
            ))

        # 3. Class node and HAS_CLASS relationship
        # To determine if update/create, we can check if it exists (not strictly necessary for MERGE,
        # but let's log the nodes creation/updating based on presence)
        # Note: Cypher MERGE handles update/create cleanly.
        queries.append((
            """
            MERGE (c:Class {id: $class_id, project_id: $project_id})
            SET c.name = $class_name, c.package_name = $package_name, c.file_path = $file_path, c.type = 'Class'
            """,
            {"class_id": class_node_id, "project_id": project_id, "class_name": class_name, "package_name": package_name, "file_path": file_path}
        ))

        if package_name:
            queries.append((
                """
                MATCH (pkg:Package {id: $package_id, project_id: $project_id})
                MATCH (c:Class {id: $class_id, project_id: $project_id})
                MERGE (pkg)-[:HAS_CLASS]->(c)
                """,
                {"package_id": package_node_id, "class_id": class_node_id, "project_id": project_id}
            ))
        else:
            queries.append((
                """
                MATCH (p:Project {id: $project_id})
                MATCH (c:Class {id: $class_id, project_id: $project_id})
                MERGE (p)-[:HAS_CLASS]->(c)
                """,
                {"project_id": project_node_id, "class_id": class_node_id}
            ))

        # 4. Clean old methods owned by this Class
        queries.append((
            """
            MATCH (c:Class {id: $class_id, project_id: $project_id})-[r:HAS_METHOD]->(m:Method)
            DETACH DELETE m
            """,
            {"class_id": class_node_id, "project_id": project_id}
        ))

        # 5. Insert new methods and HAS_METHOD relationships
        for method in parsed_file.methods:
            method_id = f"{project_id}:{class_name}.{method.name}"
            params_str = ", ".join(method.parameters)
            queries.append((
                """
                MERGE (m:Method {id: $method_id, project_id: $project_id})
                SET m.name = $method_name, m.return_type = $return_type, m.parameters = $parameters
                """,
                {
                    "method_id": method_id,
                    "project_id": project_id,
                    "method_name": method.name,
                    "return_type": method.return_type or "",
                    "parameters": params_str
                }
            ))
            queries.append((
                """
                MATCH (c:Class {id: $class_id, project_id: $project_id})
                MATCH (m:Method {id: $method_id, project_id: $project_id})
                MERGE (c)-[:HAS_METHOD]->(m)
                """,
                {"class_id": class_node_id, "method_id": method_id, "project_id": project_id}
            ))

        try:
            self.execute_with_retry(queries)
            logger.info("Nodes created")
            logger.info("Nodes updated")
            logger.info("Sync completed")
        except Exception as e:
            logger.error("Graph inconsistency")
            raise e

    def delete_class(self, project_id: str, class_name: str) -> None:
        """
        Deletes a Class node and all its owned Method nodes from the active Neo4j graph provider.
        """
        if not class_name:
            return

        is_neo4j = self.provider.__class__.__name__ == "Neo4jGraphProvider"
        if not is_neo4j:
            return

        logger.info("Sync started")

        class_node_id = f"{project_id}:{class_name}"
        queries = []

        # 1. Clean up methods owned by this Class
        queries.append((
            """
            MATCH (c:Class {id: $class_id, project_id: $project_id})-[r:HAS_METHOD]->(m:Method)
            DETACH DELETE m
            """,
            {"class_id": class_node_id, "project_id": project_id}
        ))

        # 2. Clean up Class node itself
        queries.append((
            """
            MATCH (c:Class {id: $class_id, project_id: $project_id})
            DETACH DELETE c
            """,
            {"class_id": class_node_id, "project_id": project_id}
        ))

        try:
            self.execute_with_retry(queries)
            logger.info("Nodes removed")
            logger.info("Sync completed")
        except Exception as e:
            logger.error("Graph inconsistency")
            raise e
