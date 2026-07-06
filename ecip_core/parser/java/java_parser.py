from pathlib import Path
import javalang

from ecip_core.common.logger import get_logger
from ecip_core.parser.models.method_info import MethodInfo
from ecip_core.parser.models.parsed_java_file import ParsedJavaFile

logger = get_logger(__name__)


def extract_annotations(node) -> list[str]:
    annotations = []
    if hasattr(node, 'annotations') and node.annotations:
        for ann in node.annotations:
            annotations.append(f"@{ann.name}")
    return annotations


def format_type(type_node) -> str:
    if not type_node:
        return "void"
    name = getattr(type_node, 'name', '')
    if hasattr(type_node, 'arguments') and type_node.arguments:
        args = []
        for arg in type_node.arguments:
            if hasattr(arg, 'type') and arg.type:
                args.append(format_type(arg.type))
        if args:
            name += f"<{', '.join(args)}>"
    if hasattr(type_node, 'dimensions') and type_node.dimensions:
        name += "[]" * len(type_node.dimensions)
    return name


def find_end_line(lines: list[str], start_line_1_based: int) -> int:
    start_idx = start_line_1_based - 1
    if start_idx < 0 or start_idx >= len(lines):
        return start_line_1_based

    brace_count = 0
    started = False
    
    for i in range(start_idx, len(lines)):
        line = lines[i]
        # Ignore braces inside comments
        if "//" in line:
            line = line.split("//")[0]
        
        # Count braces
        for char in line:
            if char == '{':
                brace_count += 1
                started = True
            elif char == '}':
                brace_count -= 1
                if started and brace_count <= 0:
                    return i + 1
                    
    return len(lines)


class JavaParser:
    """
    Parses a Java source file and extracts metadata using javalang AST.
    """

    def parse(self, file_path: str) -> ParsedJavaFile:
        path = Path(file_path)
        logger.info("Parsing started")
        
        try:
            with open(path, "r", encoding="utf-8") as file:
                source_code = file.read()
        except FileNotFoundError as e:
            logger.error("Parser failure")
            logger.error(f"File skipped: {path}")
            raise e

        lines = source_code.splitlines()

        try:
            tree = javalang.parse.parse(source_code)
            logger.info("AST created")
        except javalang.parser.JavaSyntaxError as e:
            logger.error("Syntax error")
            logger.error(f"File skipped: {path}")
            raise e
        except Exception as e:
            logger.error("Parser failure")
            logger.error(f"File skipped: {path}")
            raise e

        # Extract package_name
        package_name = tree.package.name if tree.package else None

        # Extract imports
        imports = []
        if tree.imports:
            for imp in tree.imports:
                path_str = imp.path
                if imp.wildcard:
                    path_str += ".*"
                if imp.static:
                    path_str = "static " + path_str
                imports.append(path_str)

        # Extract primary class/type matching the filename stem, or fallback
        primary_class = None
        stem = path.stem
        
        for _, node in tree.filter(javalang.tree.ClassDeclaration):
            if node.name == stem:
                primary_class = node
                break
        
        if not primary_class:
            for _, node in tree.filter(javalang.tree.ClassDeclaration):
                primary_class = node
                break
                
        if not primary_class:
            for _, node in tree.filter(javalang.tree.InterfaceDeclaration):
                primary_class = node
                break

        if not primary_class:
            for _, node in tree.filter(javalang.tree.EnumDeclaration):
                primary_class = node
                break

        class_name = None
        class_annotations = []
        interfaces = []
        constructors = []
        fields = []

        if primary_class:
            class_name = primary_class.name
            logger.info("Class discovered")
            class_annotations = extract_annotations(primary_class)
            
            # Extract interfaces
            if isinstance(primary_class, javalang.tree.ClassDeclaration):
                if primary_class.implements:
                    for impl in primary_class.implements:
                        interfaces.append(impl.name)
            elif isinstance(primary_class, javalang.tree.InterfaceDeclaration):
                if primary_class.extends:
                    if isinstance(primary_class.extends, list):
                        for ext in primary_class.extends:
                            interfaces.append(ext.name)
                    else:
                        interfaces.append(primary_class.extends.name)
        else:
            logger.warning("Partial metadata")

        # Extract constructors
        for _, node in tree.filter(javalang.tree.ConstructorDeclaration):
            constructors.append(node.name)

        # Extract fields
        for _, node in tree.filter(javalang.tree.FieldDeclaration):
            mods = " ".join(node.modifiers)
            type_name = format_type(node.type)
            for dec in node.declarators:
                field_str = f"{mods} {type_name} {dec.name}".strip()
                fields.append(field_str)

        # Extract methods
        methods = []
        for _, node in tree.filter(javalang.tree.MethodDeclaration):
            start_line = node.position.line if node.position else 1
            
            if node.body:
                end_line = find_end_line(lines, start_line)
            else:
                end_line = start_line
                for i in range(start_line - 1, len(lines)):
                    if ";" in lines[i]:
                        end_line = i + 1
                        break
                        
            ret_type = format_type(node.return_type)
            mods_list = list(node.modifiers)
            ann_list = extract_annotations(node)
            
            params_list = []
            for p in node.parameters:
                p_type = format_type(p.type)
                params_list.append(f"{p_type} {p.name}")
                
            mods_str = " ".join(mods_list)
            params_str = ", ".join(params_list)
            signature = f"{mods_str} {ret_type} {node.name}({params_str})".strip()
            
            methods.append(
                MethodInfo(
                    name=node.name,
                    signature=signature,
                    return_type=ret_type,
                    modifiers=mods_list,
                    annotations=ann_list,
                    parameters=params_list,
                    start_line=start_line,
                    end_line=end_line
                )
            )

        logger.info("Methods extracted")
        
        # Check for record types or other unsupported type constructs
        if tree.types and not primary_class:
            logger.warning(f"Unsupported construct: {type(tree.types[0]).__name__}")
            logger.warning("Partial metadata")

        logger.info("Parsing completed")
        
        return ParsedJavaFile(
            file_name=path.name,
            file_path=str(path.resolve()),
            package_name=package_name,
            imports=imports,
            class_name=class_name,
            class_annotations=class_annotations,
            interfaces=interfaces,
            constructors=constructors,
            fields=fields,
            methods=methods,
            source_code=source_code
        )