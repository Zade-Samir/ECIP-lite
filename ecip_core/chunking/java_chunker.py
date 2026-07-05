from pathlib import Path

from ecip_core.chunking.code_chunk import CodeChunk
from ecip_core.parser.java.java_parser import JavaParser


class JavaChunker:

    def __init__(self):
        self.parser = JavaParser()

    def chunk(
        self,
        file_path: str
    ) -> list[CodeChunk]:
        parsed = self.parser.parse(file_path)

        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()

        chunks = []
        for method in parsed.methods:
            source = "".join(
                lines[
                    method.start_line - 1:
                    method.end_line
                ]
            )
            chunks.append(
                CodeChunk(
                    file_name=parsed.file_name,
                    class_name=parsed.class_name or "Unknown",
                    method_name=method.name,
                    source_code=source,
                )
            )

        return chunks