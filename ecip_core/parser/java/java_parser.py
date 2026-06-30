from pathlib import Path

from ecip_core.common.logger import get_logger
from ecip_core.parser.models.parsed_java_file import ParsedJavaFile

logger = get_logger(__name__)


class JavaParser:

    def parse(self, file_path: str) -> ParsedJavaFile:

        path = Path(file_path)

        package_name: str | None = None
        imports: list[str] = []
        class_name: str | None = None
        methods: list[str] = []

        logger.info(f"Parsing file: {path.name}")

        try:

            source_code = ""
            with open(path, "r", encoding="utf-8") as file:

                source_code = file.read()

                for line in source_code.splitlines():

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

                        methods.append(method_name)

        except FileNotFoundError:

            logger.error(f"File not found: {path}")

            raise

        logger.info(f"Successfully parsed {path.name}")

        return ParsedJavaFile(
            file_name=path.name,
            file_path=str(path.resolve()),
            source_code=source_code,
            package_name=package_name,
            imports=imports,
            class_name=class_name,
            methods=methods,
        )