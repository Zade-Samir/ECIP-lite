from collections import deque
from ecip_core.common.logger import get_logger
from ecip_core.dependency.dependency_service import DependencyQueryService
from ecip_core.dependency.models.impact_report import ImpactReport
from ecip_core.dependency.models.relationship import Relationship

logger = get_logger(__name__)


class ImpactAnalysisEngine:
    """
    Analyses the blast radius of changes to a class using the dependency graph.
    Traverses INCOMING edges to determine which classes would be affected.
    """

    def __init__(self, project_id: str = None):
        self.dependency_service = DependencyQueryService(project_id)
        self.project_id = project_id

    def _resolve_project_id(self, project_id: str = None) -> str:
        return project_id or self.project_id or "sample-project"

    def analyze(
        self,
        target_class: str,
        depth: int = 3,
        project_id: str = None
    ) -> ImpactReport:
        """
        Produces an ImpactReport showing which classes are affected
        if the target_class changes. Uses reverse BFS (incoming edges).
        """
        p_id = self._resolve_project_id(project_id)
        logger.info("Analysis started")

        warnings = []
        dependency_tree: list[Relationship] = []
        affected_classes_ordered: list[str] = []
        visited_classes: set[str] = {target_class}
        visited_edges: set[tuple] = set()

        # Check class existence
        exists = self.dependency_service._check_class_exists(p_id, target_class)
        if not exists:
            logger.warning(f"Unknown class: {target_class}")
            warnings.append(f"Unknown class: {target_class}")
            return ImpactReport(
                project_id=p_id,
                target_class=target_class,
                affected_classes=[],
                dependency_tree=[],
                traversal_depth=depth,
                total_affected=0,
                warnings=warnings
            )

        queue: deque[tuple[str, int]] = deque([(target_class, 1)])

        while queue:
            curr_class, curr_depth = queue.popleft()

            if curr_depth > depth:
                continue

            try:
                incoming = self.dependency_service.get_dependents(curr_class, p_id)
            except Exception as e:
                logger.error(f"Traversal failure: {e}")
                warnings.append(f"Traversal failure at depth {curr_depth}: {e}")
                continue

            for rel in incoming:
                src = rel.source_class
                tgt = rel.target_class
                rel_type = rel.relationship_type

                edge_key = (src, tgt, rel_type, curr_depth)

                if edge_key in visited_edges:
                    continue
                visited_edges.add(edge_key)

                dependency_tree.append(
                    Relationship(
                        source_class=src,
                        target_class=tgt,
                        relationship_type=rel_type,
                        depth=curr_depth,
                        project_id=p_id
                    )
                )

                if src != target_class:
                    if src not in affected_classes_ordered:
                        affected_classes_ordered.append(src)

                if src in visited_classes:
                    logger.warning(f"Circular dependency detected: {src} -> {tgt}")
                    warnings.append(f"Circular dependency detected: {src} -> {tgt}")
                    continue

                visited_classes.add(src)
                queue.append((src, curr_depth + 1))

        logger.info("Dependencies traversed")

        # Deterministic ordering
        dependency_tree.sort(
            key=lambda r: (r.depth, r.source_class, r.target_class, r.relationship_type)
        )
        affected_classes_ordered.sort()

        logger.info("Report generated")

        return ImpactReport(
            project_id=p_id,
            target_class=target_class,
            affected_classes=affected_classes_ordered,
            dependency_tree=dependency_tree,
            traversal_depth=depth,
            total_affected=len(affected_classes_ordered),
            warnings=warnings
        )
