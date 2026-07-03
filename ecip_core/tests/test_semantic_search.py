from ecip_core.indexing.index_builder import IndexBuilder
from ecip_core.embedding.embedding_service import EmbeddingService


def main():

    builder = IndexBuilder()

    store = builder.build(
        "projects/sampleProject"
    )

    embedding_service = EmbeddingService()

    results = store.search_question(
        "Where is getUserById implemented?",
        embedding_service,
    )

    print("\nSemantic Search Results\n")

    for result in results:

        print("----------------------")
        print(result.file_name)
        print(result.class_name)
        print(result.method_name)


if __name__ == "__main__":
    main()