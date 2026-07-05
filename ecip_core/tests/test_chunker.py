from ecip_core.chunking.java_chunker import JavaChunker


def main():
    chunker = JavaChunker()
    chunks = chunker.chunk(
        "projects/sampleProject/UserService.java"
    )
    for chunk in chunks:
        print("-" * 50)
        print(chunk.model_dump())


if __name__ == "__main__":
    main()
