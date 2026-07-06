import hashlib
from pathlib import Path

from ecip_core.chunking.models.code_chunk import CodeChunk
from ecip_core.parser.java.java_parser import JavaParser
from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


def compute_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def compute_chunk_id(project_id: str, file_path: str, class_name: str, method_name: str | None, chunk_type: str) -> str:
    m_name = method_name or "OVERVIEW"
    raw_str = f"{project_id}:{file_path}:{class_name}:{m_name}:{chunk_type}"
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()


def build_class_overview(parsed) -> str:
    lines = []
    
    # 1. Package
    if parsed.package_name:
        lines.append(f"package {parsed.package_name};")
        
    # 2. Annotations
    if parsed.class_annotations:
        for ann in parsed.class_annotations:
            lines.append(ann)
            
    # 3. Class declaration and interfaces
    decl = f"class {parsed.class_name}"
    if parsed.superclass:
        decl += f" extends {parsed.superclass}"
    if parsed.implemented_interfaces:
        decl += f" implements {', '.join(parsed.implemented_interfaces)}"
    lines.append(decl)
    
    # 4. Constructor summary
    lines.append("\nConstructors:")
    if parsed.constructors:
        for c in parsed.constructors:
            mods = " ".join(c.modifiers)
            params = ", ".join(c.parameters)
            lines.append(f"- {mods} {parsed.class_name}({params})".strip())
    else:
        lines.append("- None")
        
    # 5. Field summary
    lines.append("\nFields:")
    if parsed.fields:
        for f in parsed.fields:
            mods = " ".join(f.modifiers)
            lines.append(f"- {mods} {f.type} {f.name}".strip())
    else:
        lines.append("- None")
        
    return "\n".join(lines)


class JavaChunker:

    def __init__(self):
        self.parser = JavaParser()

    def chunk(self, file_path: str, project_id: str = "default") -> list[CodeChunk]:
        logger.info("Chunking started")
        
        try:
            parsed = self.parser.parse(file_path)
        except Exception as e:
            logger.error("Chunk generation failure")
            raise e

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                lines = file.readlines()
        except Exception as e:
            logger.error("Chunk generation failure")
            raise e

        chunks = []
        class_name = parsed.class_name or "Unknown"

        # 1. Generate Class Overview Chunk
        if parsed.class_name:
            # Check for Empty Class
            if not parsed.methods and not parsed.fields and not parsed.constructors:
                logger.warning("Empty class")
                
            overview_content = build_class_overview(parsed)
            o_hash = compute_hash(overview_content)
            o_id = compute_chunk_id(project_id, file_path, class_name, None, "CLASS_OVERVIEW")
            
            chunks.append(
                CodeChunk(
                    chunk_id=o_id,
                    project_id=project_id,
                    file_path=str(Path(file_path).resolve()),
                    class_name=class_name,
                    method_name=None,
                    chunk_type="CLASS_OVERVIEW",
                    content=overview_content,
                    source_code=overview_content,
                    start_line=1,
                    end_line=len(lines) if lines else 1,
                    content_hash=o_hash
                )
            )
            logger.info("Overview chunk created")
        else:
            logger.warning("Empty class")

        # 2. Generate Chunks for each Method
        for method in parsed.methods:
            # Validate line range
            if method.start_line < 1 or method.end_line > len(lines) or method.start_line > method.end_line:
                logger.error("Invalid line range")
                logger.error("Chunk generation failure")
                raise ValueError(f"Invalid line range: {method.start_line} - {method.end_line}")

            source = "".join(lines[method.start_line - 1 : method.end_line])
            
            # Check for Empty Method Body
            if not source.strip() or ("{" not in source and "}" not in source):
                logger.warning("Empty method body")

            m_hash = compute_hash(source)
            m_id = compute_chunk_id(project_id, file_path, class_name, method.name, "METHOD")

            chunks.append(
                CodeChunk(
                    chunk_id=m_id,
                    project_id=project_id,
                    file_path=str(Path(file_path).resolve()),
                    class_name=class_name,
                    method_name=method.name,
                    chunk_type="METHOD",
                    content=source,
                    source_code=source,
                    start_line=method.start_line,
                    end_line=method.end_line,
                    content_hash=m_hash
                )
            )
            logger.info("Method chunk created")

        logger.info(f"Total chunks generated: {len(chunks)}")
        return chunks