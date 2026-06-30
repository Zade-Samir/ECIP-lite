from pathlib import Path

from ecip_core.chunking.code_chunk import CodeChunk


class JavaChunker:

    def chunk(
        self,
        file_path: str
    ) -> list[CodeChunk]:

        path = Path(file_path)

        with open(path, "r", encoding="utf-8") as file:
            source = file.read()

        return [
            CodeChunk(
                file_name=path.name,
                class_name="Unknown",
                method_name="WholeFile",
                source_code=source,
            )
        ]