from pydantic import BaseModel, Field


class DatabaseSettings(BaseModel):
    db_path: str = Field(default="data/ecip.db", description="Path to the SQLite database file.")


class FAISSSettings(BaseModel):
    index_path: str = Field(default=".ecip/faiss.index", description="Path to the FAISS index file.")
    metadata_path: str = Field(default=".ecip/faiss_metadata.json", description="Path to the FAISS metadata JSON file.")


class EmbeddingSettings(BaseModel):
    provider: str = Field(default="ollama", description="Embedding provider type (e.g. ollama).")
    model: str = Field(default="nomic-embed-text", description="Name of the embedding model.")
    dimension: int = Field(default=768, description="Dimension size of the embedding vectors.")
    batch_size: int = Field(default=8, description="Batch size for embedding generation.")


class InferenceSettings(BaseModel):
    provider: str = Field(default="ollama", description="Inference provider type (e.g. ollama).")
    model: str = Field(default="qwen2.5-coder:3b", description="Name of the LLM inference model.")
    temperature: float = Field(default=0.2, description="Temperature for generation.")
    top_p: float = Field(default=0.9, description="Top-p value for generation.")
    max_tokens: int = Field(default=4096, description="Max tokens for generation.")
    stream: bool = Field(default=False, description="Whether to stream response generation.")
    system_prompt: str = Field(
        default="You are ECIP, an expert Java and Spring Boot Architect.",
        description="System prompt used for context generation."
    )
    ollama_base_url: str = Field(default="http://localhost:11434", description="Base URL of the Ollama server.")


class LoggingSettings(BaseModel):
    level: str = Field(default="INFO", description="Global log level (DEBUG, INFO, WARNING, ERROR).")
    format: str = Field(
        default="[%(asctime)s] %(levelname)s | %(name)s | %(message)s",
        description="Log message format pattern."
    )


class APISettings(BaseModel):
    host: str = Field(default="127.0.0.1", description="FastAPI server host.")
    port: int = Field(default=8000, description="FastAPI server port.")


class CLISettings(BaseModel):
    ansi_colors: bool = Field(default=True, description="Whether to enable ANSI color coding in terminal.")


class ProjectStorageSettings(BaseModel):
    base_dir: str = Field(default="projects", description="Base directory for project source files.")


class CacheSettings(BaseModel):
    enabled: bool = Field(default=True, description="Whether storage/retrieval cache is enabled.")
    ttl_seconds: int = Field(default=3600, description="Cache TTL in seconds.")


class ExperimentalSettings(BaseModel):
    enable_new_parser: bool = Field(default=False, description="Enable experimental parser updates.")


class GraphSettings(BaseModel):
    provider: str = Field(default="sqlite", description="Graph provider ('sqlite' or 'neo4j').")
    neo4j_uri: str = Field(default="bolt://localhost:7687", description="Neo4j bolt URI.")
    neo4j_username: str = Field(default="neo4j", description="Neo4j username.")
    neo4j_password: str = Field(default="password", description="Neo4j password.")
