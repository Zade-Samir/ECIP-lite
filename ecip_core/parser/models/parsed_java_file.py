
from pydantic import BaseModel


class ParsedJavaFile(BaseModel):
    """
    Represents extracted information from a Java source file.
    """

    package_name: str | None = None

    imports: list[str] = []

    class_name: str | None = None

    methods: list[str] = []