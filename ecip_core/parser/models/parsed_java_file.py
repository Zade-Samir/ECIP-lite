
from pydantic import BaseModel, Field
from ecip_core.parser.models.method_info import MethodInfo


class ParsedJavaFile(BaseModel):
    """
    Represents the parsed information extracted from a Java source file.
    """

    file_name: str
    file_path: str

    package_name: str | None = None
    imports: list[str] = Field(default_factory=list)
    class_name: str | None = None
    methods: list[MethodInfo] = Field(default_factory=list)