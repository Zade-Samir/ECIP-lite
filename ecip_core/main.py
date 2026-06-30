from ecip_core.parser.java.java_parser import JavaParser

parser = JavaParser()

result = parser.parse(
    "projects/sampleProject/UserService.java"
)

print(result.model_dump())