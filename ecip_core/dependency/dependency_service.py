from collections import deque
from ecip_core.common.logger import get_logger
from ecip_core.dependency.models.relationship import Relationship
from ecip_core.storage.sqlite.repository import JavaRepository

logger = get_logger(__name__)


class DependencyQueryService:
    """
    Service for querying the SQLite dependency graph.
    """

    def __init__(self, project_id: str = None):
        self.repository = JavaRepository()
        self.project_id = project_id

    def _resolve_project_id(self, project_id: str = None) -> str:
        p_id = project_id or self.project_id
        if p_id:
            return p_id
        projects = self.repository.get_projects()
        if projects:
            return projects[0]["project_id"]
        return "sample-project"

    def _check_class_exists(self, project_id: str, class_name: str) -> bool:
        try:
            res = self.repository.search_classes(class_name, exact=True)
            if not res:
                # Also check if it exists in dependency_edges
                cursor = self.repository.connection.cursor()
                cursor.execute(
                    "SELECT 1 FROM dependency_edges WHERE project_id = ? AND (source_class = ? OR target_class = ?) LIMIT 1",
                    (project_id, class_name, class_name)
                )
                if cursor.fetchone():
                    return True
                return False
            return True
        except Exception as e:
            logger.error(f"Database failure: {e}")
            raise

    def get_dependencies(self, class_name: str, project_id: str = None) -> list[Relationship]:
        """
        Returns direct dependencies (outgoing relationships) of the class (depth=1).
        """
        logger.info("Dependency query started")
        p_id = self._resolve_project_id(project_id)

        if not self._check_class_exists(p_id, class_name):
            logger.warning(f"Unknown class: {class_name}")
            return []

        try:
            edges = self.repository.get_outgoing_edges(p_id, class_name)
            if not edges:
                logger.warning(f"No relationships found for class: {class_name}")
                return []

            results = []
            for edge in edges:
                results.append(
                    Relationship(
                        source_class=edge["source_class"],
                        target_class=edge["target_class"],
                        relationship_type=edge["relationship_type"],
                        depth=1,
                        project_id=p_id
                    )
                )

            results.sort(key=lambda r: (r.depth, r.source_class, r.target_class, r.relationship_type))
            logger.info("Query completed")
            return results
        except Exception as e:
            logger.error(f"Database failure: {e}")
            raise

    def get_dependents(self, class_name: str, project_id: str = None) -> list[Relationship]:
        """
        Returns direct dependents (incoming relationships) of the class (depth=1).
        """
        logger.info("Dependency query started")
        p_id = self._resolve_project_id(project_id)

        if not self._check_class_exists(p_id, class_name):
            logger.warning(f"Unknown class: {class_name}")
            return []

        try:
            edges = self.repository.get_incoming_edges(p_id, class_name)
            if not edges:
                logger.warning(f"No relationships found for class: {class_name}")
                return []

            results = []
            for edge in edges:
                results.append(
                    Relationship(
                        source_class=edge["source_class"],
                        target_class=edge["target_class"],
                        relationship_type=edge["relationship_type"],
                        depth=1,
                        project_id=p_id
                    )
                )

            results.sort(key=lambda r: (r.depth, r.source_class, r.target_class, r.relationship_type))
            logger.info("Query completed")
            return results
        except Exception as e:
            logger.error(f"Database failure: {e}")
            raise

    def get_relationships(self, class_name: str, project_id: str = None) -> list[Relationship]:
        """
        Returns all direct incoming and outgoing relationships of the class (depth=1).
        """
        logger.info("Dependency query started")
        p_id = self._resolve_project_id(project_id)

        if not self._check_class_exists(p_id, class_name):
            logger.warning(f"Unknown class: {class_name}")
            return []

        try:
            edges = self.repository.get_all_class_edges(p_id, class_name)
            if not edges:
                logger.warning(f"No relationships found for class: {class_name}")
                return []

            results = []
            for edge in edges:
                results.append(
                    Relationship(
                        source_class=edge["source_class"],
                        target_class=edge["target_class"],
                        relationship_type=edge["relationship_type"],
                        depth=1,
                        project_id=p_id
                    )
                )

            unique_results = {}
            for r in results:
                key = (r.source_class, r.target_class, r.relationship_type, r.depth)
                unique_results[key] = r

            sorted_results = list(unique_results.values())
            sorted_results.sort(key=lambda r: (r.depth, r.source_class, r.target_class, r.relationship_type))
            logger.info("Query completed")
            return sorted_results
        except Exception as e:
            logger.error(f"Database failure: {e}")
            raise

    def get_dependency_tree(self, class_name: str, depth: int = 2, project_id: str = None) -> list[Relationship]:
        """
        Returns dependencies (outgoing relationships) traversing recursively up to a certain depth.
        """
        logger.info("Dependency query started")
        p_id = self._resolve_project_id(project_id)

        if depth < 1:
            logger.error("Invalid traversal")
            raise ValueError("Traversal depth must be at least 1")

        if not self._check_class_exists(p_id, class_name):
            logger.warning(f"Unknown class: {class_name}")
            return []

        try:
            results = []
            seen_edges = set()
            
            queue = deque([(class_name, 1)])
            visited_classes = {class_name}

            while queue:
                curr, curr_depth = queue.popleft()
                if curr_depth > depth:
                    continue

                edges = self.repository.get_outgoing_edges(p_id, curr)
                for edge in edges:
                    src = edge["source_class"]
                    tgt = edge["target_class"]
                    rel = edge["relationship_type"]

                    edge_key = (src, tgt, rel, curr_depth)
                    if edge_key not in seen_edges:
                        seen_edges.add(edge_key)
                        results.append(
                            Relationship(
                                source_class=src,
                                target_class=tgt,
                                relationship_type=rel,
                                depth=curr_depth,
                                project_id=p_id
                            )
                        )

                    if tgt not in visited_classes:
                        visited_classes.add(tgt)
                        queue.append((tgt, curr_depth + 1))

            results.sort(key=lambda r: (r.depth, r.source_class, r.target_class, r.relationship_type))
            logger.info("Query completed")
            return results
        except Exception as e:
            logger.error(f"Database failure: {e}")
            raise
