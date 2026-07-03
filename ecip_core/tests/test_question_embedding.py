from ecip_core.embedding.embedding_service import EmbeddingService


def main():

    service = EmbeddingService()

    vector = service.embed_question(
        "Where is getUserById implemented?"
    )

    print()

    print("Dimension :", len(vector))


if __name__ == "__main__":
    main()