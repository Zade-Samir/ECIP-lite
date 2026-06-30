from pathlib import Path

from ecip_core.parser.models.parsed_java_file import ParsedJavaFile


class JavaParser:

    def parse(self, file_path: str) -> ParsedJavaFile:

        package_name = None
        imports = []
        class_name = None
        methods = []

        with open(file_path, "r") as file:

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
            package_name=package_name,
            imports=imports,
            class_name=class_name,
            methods=methods,
        )