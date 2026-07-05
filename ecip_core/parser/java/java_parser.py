from pathlib import Path

from ecip_core.common.logger import get_logger
from ecip_core.parser.models.method_info import MethodInfo
from ecip_core.parser.models.parsed_java_file import ParsedJavaFile

logger = get_logger(__name__)


class JavaParser:
    """
    Parses a Java source file and extracts metadata.
    """

    def parse(self, file_path: str) -> ParsedJavaFile:

        path = Path(file_path)

        package_name: str | None = None
        imports: list[str] = []
        class_name: str | None = None
        methods: list[MethodInfo] = []

        logger.info(f"Parsing file: {path.name}")

        try:

            with open(path, "r", encoding="utf-8") as file:

                for line_number, line in enumerate(file, start=1):

                    line = line.strip()

                    if line.startswith("package "):
                        package_name = (
                            line.replace("package ", "")
                            .replace(";", "")
                        )

                    elif line.startswith("import "):
                        imports.append(
                            line.replace("import ", "")
                            .replace(";", "")
                        )

                    elif " class " in line:
                        class_name = (
                            line.split("class")[1]
                            .split("{")[0]
                            .strip()
                        )

                    elif (
                        "(" in line
                        and ")" in line
                        and line.endswith("{")
                        and "class" not in line
                    ):

                        method_name = (
                            line.split("(")[0]
                            .split()[-1]
                            .strip()
                        )

                        methods.append(
                            MethodInfo(
                                name=method_name,
                                start_line=line_number,
                                end_line=line_number,  # Temporary
                            )
                        )

        except FileNotFoundError:

            logger.error(f"File not found: {path}")

            raise

        logger.info(f"Successfully parsed {path.name}")

        return ParsedJavaFile(
            file_name=path.name,
            file_path=str(path.resolve()),
            package_name=package_name,
            imports=imports,
            class_name=class_name,
            methods=methods,
        )