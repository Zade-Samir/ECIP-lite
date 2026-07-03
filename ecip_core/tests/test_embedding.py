from ecip_core.chunking.java_chunker import JavaChunker
from ecip_core.embedding.embedding_service import EmbeddingService


def main():

    chunker = JavaChunker()
    service = EmbeddingService()

    chunk = chunker.chunk(
        "projects/sampleProject/UserService.java"
    )[0]

    embedding = service.generate(chunk)

    print(f"Embedding Dimension : {len(embedding.vector)}")
    print(f"File Name           : {embedding.file_name}")


if __name__ == "__main__":
    main()