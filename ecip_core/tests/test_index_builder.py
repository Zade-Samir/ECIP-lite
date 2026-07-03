from ecip_core.indexing.index_builder import IndexBuilder


def main():

    builder = IndexBuilder()

    store = builder.build(
        "projects/sampleProject"
    )

    print()

    print("Indexed vectors:", store.index.ntotal)


if __name__ == "__main__":
    main()