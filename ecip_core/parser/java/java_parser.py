from pathlib import Path
import javalang

from ecip_core.common.logger import get_logger
from ecip_core.parser.models.method_info import MethodInfo
from ecip_core.parser.models.parsed_java_file import ParsedJavaFile
from ecip_core.parser.models.field_info import FieldInfo
from ecip_core.parser.models.constructor_info import ConstructorInfo
from ecip_core.parser.models.dependency_metadata import DependencyMetadata

logger = get_logger(__name__)

SUPPORTED_ANNOTATIONS = {
    "@RestController", "@Controller", "@Service", "@Repository", "@Component", "@Configuration", "@Entity", "@Table",
    "@GetMapping", "@PostMapping", "@PutMapping", "@DeleteMapping", "@PatchMapping", "@RequestMapping", "@Transactional",
    "@Id", "@Column", "@Autowired", "@Value"
}


def extract_annotations(node) -> list[str]:
    annotations = []
    if hasattr(node, 'annotations') and node.annotations:
        for ann in node.annotations:
            name = f"@{ann.name}"
            if name in SUPPORTED_ANNOTATIONS:
                logger.info("Annotation extracted")
            else:
                logger.warning(f"Unsupported annotation: {name}")
            annotations.append(name)
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
        if "//" in line:
            line = line.split("//")[0]
        
        for char in line:
            if char == '{':
                brace_count += 1
                started = True
            elif char == '}':
                brace_count -= 1
                if started and brace_count <= 0:
                    return i + 1
                    
    return len(lines)


JAVA_MODIFIER_ORDER = [
    "public", "protected", "private", "abstract", "static", "final",
    "transient", "volatile", "synchronized", "native", "strictfp"
]


def sort_modifiers(modifiers) -> list[str]:
    return sorted(list(modifiers), key=lambda m: JAVA_MODIFIER_ORDER.index(m) if m in JAVA_MODIFIER_ORDER else 999)


class JavaParser:
    """
    Parses a Java source file and extracts metadata using javalang AST.
    """

    def parse(self, file_path: str) -> ParsedJavaFile:
        path = Path(file_path)
        logger.info("Parsing started")
        logger.info("Model upgraded")
        
        try:
            with open(path, "r", encoding="utf-8") as file:
                source_code = file.read()
        except FileNotFoundError as e:
            logger.error("Parser failure")
            logger.error("Mapping failure")
            logger.error("AST mapping failure")
            logger.error(f"File skipped: {path}")
            raise e

        if not source_code.strip():
            logger.error("Parser failure")
            logger.error("Mapping failure")
            logger.error("AST mapping failure")
            logger.error(f"File skipped: {path}")
            raise ValueError("Empty file")

        lines = source_code.splitlines()

        try:
            tree = javalang.parse.parse(source_code)
            logger.info("AST created")
            logger.info(f"File parsed: {path.name}")
        except javalang.parser.JavaSyntaxError as e:
            logger.error("Syntax error")
            logger.error("Mapping failure")
            logger.error("AST mapping failure")
            logger.error(f"File skipped: {path}")
            raise e
        except Exception as e:
            logger.error("Parser failure")
            logger.error("Mapping failure")
            logger.error("AST mapping failure")
            logger.error(f"File skipped: {path}")
            raise e

        try:
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
            superclass = None
            implemented_interfaces = []
            constructors = []
            fields = []
            dependencies = []

            if primary_class:
                class_name = primary_class.name
                logger.info("Class discovered")
                class_annotations = extract_annotations(primary_class)
                
                # Extract superclass
                if isinstance(primary_class, javalang.tree.ClassDeclaration) and primary_class.extends:
                    superclass = format_type(primary_class.extends)
                
                # Extract interfaces
                if isinstance(primary_class, javalang.tree.ClassDeclaration):
                    if primary_class.implements:
                        for impl in primary_class.implements:
                            implemented_interfaces.append(format_type(impl))
                elif isinstance(primary_class, javalang.tree.InterfaceDeclaration):
                    if primary_class.extends:
                        if isinstance(primary_class.extends, list):
                            for ext in primary_class.extends:
                                implemented_interfaces.append(format_type(ext))
                        else:
                            implemented_interfaces.append(format_type(primary_class.extends))
            else:
                logger.warning("Partial metadata")

            # Logging warnings for optional metadata availability
            if not superclass or not package_name:
                logger.warning("Optional metadata unavailable")

            # Extract constructors
            for _, node in tree.filter(javalang.tree.ConstructorDeclaration):
                start_line = node.position.line if node.position else 1
                end_line = find_end_line(lines, start_line)
                
                mods = sort_modifiers(node.modifiers)
                anns = extract_annotations(node)
                params = []
                injected_deps = []
                for p in node.parameters:
                    param_type = format_type(p.type)
                    params.append(f"{param_type} {p.name}")
                    injected_deps.append(param_type)
                
                constructors.append(
                    ConstructorInfo(
                        parameters=params,
                        annotations=anns,
                        modifiers=mods,
                        start_line=start_line,
                        end_line=end_line,
                        injected_dependency_types=injected_deps
                    )
                )
                logger.info("Constructor parsed")

            # Extract fields
            for _, node in tree.filter(javalang.tree.FieldDeclaration):
                mods = sort_modifiers(node.modifiers)
                anns = extract_annotations(node)
                type_str = format_type(node.type)
                for dec in node.declarators:
                    fields.append(
                        FieldInfo(
                            name=dec.name,
                            type=type_str,
                            modifiers=mods,
                            annotations=anns
                        )
                    )

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
                mods_list = sort_modifiers(node.modifiers)
                ann_list = extract_annotations(node)
                
                params_list = []
                for p in node.parameters:
                    p_type = format_type(p.type)
                    params_list.append(f"{p_type} {p.name}")
                    
                throws_list = []
                if hasattr(node, 'throws') and node.throws:
                    throws_list = list(node.throws)

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
                        throws=throws_list,
                        start_line=start_line,
                        end_line=end_line
                    )
                )

            logger.info("Methods extracted")
            
            # Extract dependencies
            if class_name:
                # 1. Constructor dependencies
                for c in constructors:
                    for p in c.parameters:
                        parts = p.split()
                        if len(parts) >= 2:
                            target_type = parts[0]
                            param_name = parts[1]
                            dependencies.append(
                                DependencyMetadata(
                                    source_class=class_name,
                                    target_class=target_type,
                                    injection_type="CONSTRUCTOR",
                                    parameter_name=param_name
                                )
                            )
                            logger.info("Dependency discovered")
                            
                # 2. Field dependencies
                for f in fields:
                    if "@Autowired" in f.annotations or "@Value" in f.annotations:
                        dependencies.append(
                            DependencyMetadata(
                                source_class=class_name,
                                target_class=f.type,
                                injection_type="FIELD",
                                parameter_name=None
                            )
                        )
                        logger.info("Dependency discovered")

            # Check for record types or other unsupported type constructs
            if tree.types and not primary_class:
                logger.warning(f"Unsupported construct: {type(tree.types[0]).__name__}")
                logger.warning("Partial metadata")

            logger.info("Parser mapping complete")
            logger.info(f"Completion summary: Class {class_name} successfully parsed with {len(methods)} methods")
            logger.info("Parsing completed")
            
            return ParsedJavaFile(
                file_name=path.name,
                file_path=str(path.resolve()),
                package_name=package_name,
                imports=imports,
                class_name=class_name,
                class_annotations=class_annotations,
                superclass=superclass,
                implemented_interfaces=implemented_interfaces,
                interfaces=implemented_interfaces,
                constructors=constructors,
                fields=fields,
                methods=methods,
                dependencies=dependencies,
                source_code=source_code
            )

        except Exception as e:
            logger.error("AST mapping failure")
            logger.error("Mapping failure")
            logger.error(f"Parser failure: {e}")
            raise e