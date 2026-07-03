from ecip_core.query.entity_extractor import EntityExtractor
from ecip_core.retrieval.metadata.metadata_service import MetadataService


class ContextBuilder:
    """
    Builds project context for the LLM using project metadata.
    """

    def __init__(self):

        self.metadata = MetadataService()
        self.extractor = EntityExtractor()

    def build(self, question: str) -> str:

        class_name = self.extractor.extract_class_name(question)

        if class_name is None:
            return ""

        java_class = self.metadata.get_class(class_name)

        if java_class is None:
            return ""

        methods = self.metadata.get_methods(class_name)

        return f"""
Project Context

Class:
{java_class["class_name"]}

Package:
{java_class["package_name"]}

Methods:
{", ".join(methods)}
"""