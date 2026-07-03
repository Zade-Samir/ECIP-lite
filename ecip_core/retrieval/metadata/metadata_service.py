from ecip_core.storage.sqlite.repository import JavaRepository


class MetadataService:

    def __init__(self):

        self.repository = JavaRepository()

    def get_all_files(self):

        return self.repository.get_all_files()

    def get_class(self, class_name: str):

        return self.repository.find_by_class_name(class_name)

    def get_methods(self, class_name: str):

        return self.repository.find_methods(class_name)

    def get_file_by_method(self, method_name: str):

        return self.repository.find_file_by_method(method_name)