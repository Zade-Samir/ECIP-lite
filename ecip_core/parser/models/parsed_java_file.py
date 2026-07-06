from pydantic import BaseModel, Field
from ecip_core.parser.models.method_info import MethodInfo
from ecip_core.parser.models.field_info import FieldInfo
from ecip_core.parser.models.constructor_info import ConstructorInfo
from ecip_core.parser.models.dependency_metadata import DependencyMetadata


class ParsedJavaFile(BaseModel):
    """
    Represents the parsed information extracted from a Java source file.
    """

    file_name: str
    file_path: str

    package_name: str | None = None
    imports: list[str] = Field(default_factory=list)
    class_name: str | None = None
    class_annotations: list[str] = Field(default_factory=list)
    superclass: str | None = None
    implemented_interfaces: list[str] = Field(default_factory=list)
    interfaces: list[str] = Field(default_factory=list)
    constructors: list[ConstructorInfo] = Field(default_factory=list)
    fields: list[FieldInfo] = Field(default_factory=list)
    methods: list[MethodInfo] = Field(default_factory=list)
    dependencies: list[DependencyMetadata] = Field(default_factory=list)
    source_code: str | None = None