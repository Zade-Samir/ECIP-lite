from ecip_core.parser.java.java_parser import JavaParser


def main():

    parser = JavaParser()

    parsed = parser.parse(
        "projects/sampleProject/UserService.java"
    )

    print()

    print(parsed.model_dump())


if __name__ == "__main__":
    main()