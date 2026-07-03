from ecip_core.chunking.java_chunker import JavaChunker
from ecip_core.embedding.embedding_service import EmbeddingService
from ecip_core.vectorstore.faiss_store import FAISSStore


def main():

    chunker = JavaChunker()
    embedding_service = EmbeddingService()
    store = FAISSStore()

    chunk = chunker.chunk(
        "projects/sampleProject/UserService.java"
    )[0]

    embedding = embedding_service.generate(
        chunk
    )

    store.add(
        embedding
    )

    results = store.search(
        embedding.vector
    )

    print()

    print("Search Results")

    for result in results:

        print(result.file_name)


if __name__ == "__main__":
    main()