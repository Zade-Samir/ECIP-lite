from ecip_core.common.logger import get_logger
from ecip_core.parser.models.parsed_java_file import ParsedJavaFile
from ecip_core.storage.sqlite.repository import JavaRepository

logger = get_logger(__name__)


class DependencyGraphBuilder:
    """
    Builds the dependency graph from parser metadata and persists it in SQLite.
    """

    def __init__(self):
        self.repository = JavaRepository()

    def build_class_edges(
        self,
        project_id: str,
        parsed_file: ParsedJavaFile,
        project_classes: set[str]
    ):
        """
        Extracts edges for a parsed Java class and persists them in SQLite.
        """
        source = parsed_file.class_name
        if not source:
            logger.error("Invalid metadata: class_name is missing")
            return

        logger.info("Graph generation started")

        # Clean existing edges for this source class
        self.repository.delete_class_edges(project_id, source)

        # 1. EXTENDS relationship
        if parsed_file.superclass:
            target = parsed_file.superclass
            if target in project_classes:
                if source != target:
                    success = self.repository.save_edge(project_id, source, target, "EXTENDS")
                    if success:
                        logger.info(f"Edge created: {source} -> EXTENDS -> {target}")
                    else:
                        logger.warning("Duplicate edge skipped")
                else:
                    logger.warning(f"Self dependency ignored for {source}")
            else:
                logger.warning(f"Unresolved dependency: {target}")

        # 2. IMPLEMENTS relationships
        interfaces = set(parsed_file.implemented_interfaces + parsed_file.interfaces)
        for target in sorted(interfaces):
            if target in project_classes:
                if source != target:
                    success = self.repository.save_edge(project_id, source, target, "IMPLEMENTS")
                    if success:
                        logger.info(f"Edge created: {source} -> IMPLEMENTS -> {target}")
                    else:
                        logger.warning("Duplicate edge skipped")
                else:
                    logger.warning(f"Self dependency ignored for {source}")
            else:
                logger.warning(f"Unresolved dependency: {target}")

        # 3. DEPENDS_ON relationships
        depends_on_targets = set()
        for constructor in parsed_file.constructors:
            if constructor.injected_dependency_types:
                depends_on_targets.update(constructor.injected_dependency_types)

        for dep in parsed_file.dependencies:
            if dep.injection_type == "CONSTRUCTOR":
                depends_on_targets.add(dep.target_class)

        for target in sorted(depends_on_targets):
            if target in project_classes:
                if source != target:
                    success = self.repository.save_edge(project_id, source, target, "DEPENDS_ON")
                    if success:
                        logger.info(f"Edge created: {source} -> DEPENDS_ON -> {target}")
                    else:
                        logger.warning("Duplicate edge skipped")
                else:
                    logger.warning(f"Self dependency ignored for {source}")
            else:
                logger.warning(f"Unresolved dependency: {target}")

        logger.info("Graph persisted")
        stats = self.get_stats(project_id)
        logger.info(f"Total edges: {stats['total_edges']}")

    def get_stats(self, project_id: str) -> dict:
        try:
            return self.repository.get_graph_stats(project_id)
        except Exception as e:
            logger.error(f"Graph persistence failure: {e}")
            raise
