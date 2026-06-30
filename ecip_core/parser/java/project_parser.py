from pathlib import Path

from ecip_core.parser.java.java_parser import JavaParser
from ecip_core.parser.models.parsed_java_file import ParsedJavaFile


class JavaProjectParser:

    def __init__(self):
        self.parser = JavaParser()

    def parse_project(
        self,
        project_path: str
    ) -> list[ParsedJavaFile]:

        parsed_files = []

        project = Path(project_path)

        for java_file in project.rglob("*.java"):

            parsed = self.parser.parse(
                str(java_file)
            )

            parsed_files.append(parsed)

        return parsed_files