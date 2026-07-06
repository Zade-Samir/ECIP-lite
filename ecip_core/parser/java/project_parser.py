from pathlib import Path

from ecip_core.parser.java.java_parser import JavaParser
from ecip_core.parser.models.parsed_java_file import ParsedJavaFile
from ecip_core.scanner.project_scanner import ProjectScanner
from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


class JavaProjectParser:

    def __init__(self):
        self.parser = JavaParser()

    def parse_project(
        self,
        project_path: str
    ) -> list[ParsedJavaFile]:

        logger.info("Project parsing started")
        parsed_files = []

        self.scanner = ProjectScanner()

        try:
            raw_files = self.scanner.scan(project_path)
            java_files = sorted(raw_files)
        except Exception as e:
            logger.error("Parser failure")
            logger.error(f"File path: {project_path}")
            logger.error(f"Exception message: {e}")
            logger.info("Parsing completed")
            logger.info("Total parsed files: 0")
            return parsed_files

        for java_file in java_files:
            java_file_path = Path(java_file)
            if not java_file_path.name.endswith(".java"):
                logger.warning(f"Unsupported file skipped: {java_file_path}")
                continue

            logger.info(f"Parsing file: {java_file_path}")
            try:
                parsed = self.parser.parse(str(java_file_path))
                parsed_files.append(parsed)
            except Exception as e:
                logger.error("Parser failure")
                logger.error(f"File path: {java_file_path}")
                logger.error(f"Exception message: {e}")

        logger.info("Parsing completed")
        logger.info(f"Total parsed files: {len(parsed_files)}")

        return parsed_files