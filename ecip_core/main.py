from ecip_core.parser.java.project_parser import JavaProjectParser
from ecip_core.storage.sqlite.repository import JavaRepository
from ecip_core.storage.sqlite.schema import SchemaManager

SchemaManager().create_tables()

repository = JavaRepository()

parser = JavaProjectParser()

files = parser.parse_project(
    "projects/sampleProject"
)

for parsed in files:

    repository.save(parsed)

print("Done")