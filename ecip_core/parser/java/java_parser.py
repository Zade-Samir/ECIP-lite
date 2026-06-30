from ecip_core.parser.models import parsed_java_file
from ecip_core.parser.models import parsed_java_file
from ecip_core.parser.models import parsed_java_file
from ecip_core.parser.models import parsed_java_file
from pathlib import Path

from ecip_core.parser.models.parsed_java_file import ParsedJavaFile

from ecip_core.common.logger import get_logger

logger = get_logger(__name__)

class JavaParser:

    def parse(self, file_path: str) -> ParsedJavaFile:

        path = Path(file_path)

        package_name = None
        imports = []
        class_name = None
        methods = []

        logger.info(f"Parsing file: {path}")

        with open(path, "r", encoding="utf-8") as file:

            logger.info(f"Parsing {file}")

            for line in file:

                line = line.strip()

                if line.startswith("package "):
                    package_name = line.replace(
                        "package ",
                        ""
                    ).replace(";", "")

                elif line.startswith("import "):
                    imports.append(
                        line.replace(
                            "import ",
                            ""
                        ).replace(";", "")
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
                    )

                    methods.append(method_name)

        return ParsedJavaFile(
            file_name=path.name,
            file_path=str(path.resolve()),
            package_name=package_name,
            imports=imports,
            class_name=class_name,
            methods=methods,
        )