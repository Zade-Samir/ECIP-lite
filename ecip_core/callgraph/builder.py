import re
import datetime
from typing import List, Dict, Any, Optional

from ecip_core.common.logger import get_logger
from ecip_core.graph.factory import get_graph_provider

logger = get_logger(__name__)


class CallGraphBuilder:
    """
    Statically analyzes parsed Java metadata to build a method-to-method call graph
    for navigation, impact analysis, and dead code detection.
    """

    def __init__(self):
        self.provider = get_graph_provider()

    def build(self, project_id: str, parsed_files: List[Any]) -> None:
        """
        Builds the call graph from a list of ParsedJavaFile objects and persists it.
        """
        logger.info("Call graph generation started")

        # Map to find classes by name
        class_by_name = {
            f.class_name: f for f in parsed_files if f.class_name
        }

        # List to track created edges for batch/duplicate prevention
        relationships_to_create = []

        # 1. Resolve method overrides & interface implementations
        for f in parsed_files:
            if not f.class_name:
                continue

            # Override matching (Superclass)
            if f.superclass and f.superclass in class_by_name:
                super_file = class_by_name[f.superclass]
                for m in f.methods:
                    for super_m in super_file.methods:
                        if m.name == super_m.name:
                            relationships_to_create.append({
                                "source_id": f"{f.class_name}.{m.name}",
                                "target_id": f"{f.superclass}.{super_m.name}",
                                "type": "OVERRIDES",
                                "properties": {"project_id": project_id}
                            })

            # Interface method implementations
            interfaces = f.implemented_interfaces or getattr(f, "interfaces", [])
            for interface_name in interfaces:
                if interface_name in class_by_name:
                    interface_file = class_by_name[interface_name]
                    for m in f.methods:
                        for inter_m in interface_file.methods:
                            if m.name == inter_m.name:
                                relationships_to_create.append({
                                    "source_id": f"{f.class_name}.{m.name}",
                                    "target_id": f"{interface_name}.{inter_m.name}",
                                    "type": "IMPLEMENTS_METHOD",
                                    "properties": {"project_id": project_id}
                                })

        # 2. Resolve method invocations
        for f in parsed_files:
            if not f.class_name:
                continue

            # Clean old class edges in the graph for incremental updates compatibility
            try:
                self.provider.delete_class_edges(project_id, f.class_name)
            except Exception as e:
                logger.warning(f"Could not delete stale edges for {f.class_name}: {e}")

            for m in f.methods:
                source_fqn = f"{f.class_name}.{m.name}"

                for inv in m.invocations:
                    method_name = inv["method_name"]
                    qualifier = inv["qualifier"]

                    target_class = None

                    # Resolve qualifier to class name
                    if not qualifier or qualifier == "this":
                        # Local call within same class
                        target_class = f.class_name
                    elif qualifier == "super" and f.superclass:
                        target_class = f.superclass
                    else:
                        # 1. Resolve via Field type
                        for field in f.fields:
                            if field.name == qualifier:
                                target_class = field.type
                                break

                        # 2. Resolve via Method parameters
                        if not target_class:
                            for param in m.parameters:
                                parts = param.split()
                                if len(parts) >= 2 and parts[1] == qualifier:
                                    target_class = parts[0]
                                    break

                        # 3. Resolve via Class Static calls / Constructor calls
                        if not target_class and qualifier in class_by_name:
                            target_class = qualifier

                        # 4. Resolve via imports wildcard or exact match
                        if not target_class:
                            for imp in f.imports:
                                if imp.endswith(f".{qualifier}"):
                                    target_class = qualifier
                                    break

                    if not target_class:
                        logger.warning(f"Unresolved invocation: {qualifier}.{method_name}")
                        continue

                    # Confirm target class exists in indexed codebase (ignore external libs)
                    if target_class in class_by_name:
                        target_file = class_by_name[target_class]
                        
                        # Match target method in target class
                        target_methods = [
                            tm for tm in target_file.methods if tm.name == method_name
                        ]

                        if not target_methods:
                            logger.warning(f"Ambiguous target: method {method_name} not found in {target_class}")
                            continue

                        # Add CALLS relationship
                        for tm in target_methods:
                            target_fqn = f"{target_class}.{tm.name}"
                            relationships_to_create.append({
                                "source_id": source_fqn,
                                "target_id": target_fqn,
                                "type": "CALLS",
                                "properties": {"project_id": project_id}
                            })

        logger.info("Methods resolved")

        # 3. Persist relationships to the graph provider (avoiding duplicates)
        persisted_count = 0
        seen_rels = set()
        for r in relationships_to_create:
            key = (r["source_id"], r["target_id"], r["type"])
            if key in seen_rels:
                continue
            seen_rels.add(key)

            try:
                # Add node labels for Method identifier resolution
                props = r.get("properties", {}).copy()
                props.update({
                    "source_label": "Method",
                    "target_label": "Method",
                    "project_id": project_id
                })
                self.provider.create_relationship(
                    source_id=r["source_id"],
                    target_id=r["target_id"],
                    rel_type=r["type"],
                    properties=props
                )
                persisted_count += 1
            except Exception as e:
                logger.error("Graph write failure")
                logger.error(f"Failed to persist call graph relationship {key}: {e}")

        logger.info(f"Edges persisted: {persisted_count}")

    def get_incoming_calls(self, project_id: str, method_fqn: str) -> List[Dict[str, Any]]:
        """
        Retrieves incoming calls targeting this method.
        """
        if hasattr(self.provider, "get_incoming_method_calls"):
            return self.provider.get_incoming_method_calls(project_id, method_fqn)
        
        # Fallback to general Cypher if Neo4j
        try:
            query_str = """
            MATCH (a:Method)-[r:CALLS]->(b:Method {id: $method_fqn, project_id: $project_id})
            RETURN a.id as source_method, b.id as target_method, type(r) as relationship_type
            """
            return self.provider.query(query_str, {"method_fqn": method_fqn, "project_id": project_id})
        except Exception:
            return []

    def get_outgoing_calls(self, project_id: str, method_fqn: str) -> List[Dict[str, Any]]:
        """
        Retrieves outgoing calls made by this method.
        """
        if hasattr(self.provider, "get_outgoing_method_calls"):
            return self.provider.get_outgoing_method_calls(project_id, method_fqn)

        # Fallback to general Cypher if Neo4j
        try:
            query_str = """
            MATCH (a:Method {id: $method_fqn, project_id: $project_id})-[r:CALLS]->(b:Method)
            RETURN a.id as source_method, b.id as target_method, type(r) as relationship_type
            """
            return self.provider.query(query_str, {"method_fqn": method_fqn, "project_id": project_id})
        except Exception:
            return []
