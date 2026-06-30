from ecip_core.parser.java.project_parser import JavaProjectParser

parser = JavaProjectParser()

files = parser.parse_project(
    "projects/sampleProject"
)

for file in files:
    print(file.model_dump())