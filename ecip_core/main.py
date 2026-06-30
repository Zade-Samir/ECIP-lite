from ecip_core.chunking.java_chunker import JavaChunker

chunker = JavaChunker()

chunks = chunker.chunk(
    "projects/sampleProject/UserService.java"
)

for chunk in chunks:
    print(chunk.model_dump())