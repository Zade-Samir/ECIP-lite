import os
import sys
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from ecip_core.common.logger import get_logger
from ecip_core.config.domains import (
    DatabaseSettings,
    FAISSSettings,
    EmbeddingSettings,
    InferenceSettings,
    LoggingSettings,
    APISettings,
    CLISettings,
    ProjectStorageSettings,
    CacheSettings,
    ExperimentalSettings,
    GraphSettings,
)
from ecip_core.config.profiles import PROFILE_DEFAULTS

logger = get_logger(__name__)


class Settings(BaseSettings):
    """
    Centralized configuration for ECIP Lite.
    Exposes root-level fields for perfect backward compatibility and env overrides,
    and groups them into domain sub-models.
    """

    # Active profile: development, testing, or production
    ECIP_PROFILE: str = Field(default="development")

    # Database Domain
    DEFAULT_DB_PATH: str = Field(default="data/ecip.db", validation_alias="DB_PATH")

    # FAISS Domain
    DEFAULT_FAISS_INDEX_PATH: str = Field(default=".ecip/faiss.index", validation_alias="FAISS_INDEX_PATH")
    DEFAULT_FAISS_METADATA_PATH: str = Field(default=".ecip/faiss_metadata.json", validation_alias="FAISS_METADATA_PATH")

    # Embedding Domain
    EMBEDDING_PROVIDER: str = Field(default="ollama")
    EMBEDDING_MODEL: str = Field(default="nomic-embed-text")
    EMBEDDING_DIMENSION: int = Field(default=768)
    EMBEDDING_BATCH_SIZE: int = Field(default=8)

    # Inference Domain
    INFERENCE_PROVIDER: str = Field(default="ollama")
    MODEL_NAME: str = Field(default="qwen2.5-coder:3b")
    TEMPERATURE: float = Field(default=0.2)
    TOP_P: float = Field(default=0.9)
    MAX_TOKENS: int = Field(default=4096)
    STREAM: bool = Field(default=False)
    SYSTEM_PROMPT: str = Field(default="You are ECIP, an expert Java and Spring Boot Architect.")
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434")

    # Logging Domain
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(default="[%(asctime)s] %(levelname)s | %(name)s | %(message)s")

    # API Domain
    API_HOST: str = Field(default="127.0.0.1")
    API_PORT: int = Field(default=8000)

    # CLI Domain
    CLI_ANSI_COLORS: bool = Field(default=True)

    # Project Storage Domain
    PROJECT_STORAGE_BASE_DIR: str = Field(default="projects")

    # Cache Domain
    CACHE_ENABLED: bool = Field(default=True)
    CACHE_TTL_SECONDS: int = Field(default=3600)

    # Experimental Domain
    EXPERIMENTAL_ENABLE_NEW_PARSER: bool = Field(default=False)

    # Graph Domain
    GRAPH_PROVIDER: str = Field(default="sqlite")
    NEO4J_URI: str = Field(default="bolt://localhost:7687")
    NEO4J_USERNAME: str = Field(default="neo4j")
    NEO4J_PASSWORD: str = Field(default="password")

    # Validators
    @field_validator("ECIP_PROFILE")
    @classmethod
    def validate_profile(cls, v: str) -> str:
        valid_profiles = {"development", "testing", "production"}
        if v not in valid_profiles:
            logger.error(f"Invalid profile '{v}' requested, falling back to 'development'")
            return "development"
        return v

    @field_validator("DEFAULT_DB_PATH")
    @classmethod
    def validate_db_path(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Database path (DB_PATH) cannot be empty")
        return v

    @field_validator("OLLAMA_BASE_URL")
    @classmethod
    def validate_ollama_url(cls, v: str) -> str:
        if not v.startswith("http://") and not v.startswith("https://"):
            raise ValueError("OLLAMA_BASE_URL must start with http:// or https://")
        return v

    @field_validator("EMBEDDING_DIMENSION", "EMBEDDING_BATCH_SIZE", "MAX_TOKENS", "API_PORT", "CACHE_TTL_SECONDS")
    @classmethod
    def validate_positive_ints(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Numeric configuration values must be greater than 0")
        return v

    # Dynamic properties for workspace isolation
    @property
    def DB_PATH(self) -> str:
        from ecip_core.workspace.manager import workspace_manager
        active = workspace_manager.get_active_workspace()
        if active == "default":
            return self.DEFAULT_DB_PATH
        return f"data/ecip_{active}.db"

    @property
    def FAISS_INDEX_PATH(self) -> str:
        from ecip_core.workspace.manager import workspace_manager
        active = workspace_manager.get_active_workspace()
        if active == "default":
            return self.DEFAULT_FAISS_INDEX_PATH
        return f".ecip/faiss_{active}.index"

    @property
    def FAISS_METADATA_PATH(self) -> str:
        from ecip_core.workspace.manager import workspace_manager
        active = workspace_manager.get_active_workspace()
        if active == "default":
            return self.DEFAULT_FAISS_METADATA_PATH
        return f".ecip/faiss_metadata_{active}.json"

    # Domain Accessors
    @property
    def database(self) -> DatabaseSettings:
        return DatabaseSettings(db_path=self.DB_PATH)

    @property
    def faiss(self) -> FAISSSettings:
        return FAISSSettings(index_path=self.FAISS_INDEX_PATH, metadata_path=self.FAISS_METADATA_PATH)

    @property
    def embedding(self) -> EmbeddingSettings:
        return EmbeddingSettings(
            provider=self.EMBEDDING_PROVIDER,
            model=self.EMBEDDING_MODEL,
            dimension=self.EMBEDDING_DIMENSION,
            batch_size=self.EMBEDDING_BATCH_SIZE,
        )

    @property
    def inference(self) -> InferenceSettings:
        return InferenceSettings(
            provider=self.INFERENCE_PROVIDER,
            model=self.MODEL_NAME,
            temperature=self.TEMPERATURE,
            top_p=self.TOP_P,
            max_tokens=self.MAX_TOKENS,
            stream=self.STREAM,
            system_prompt=self.SYSTEM_PROMPT,
            ollama_base_url=self.OLLAMA_BASE_URL,
        )

    @property
    def logging(self) -> LoggingSettings:
        return LoggingSettings(level=self.LOG_LEVEL, format=self.LOG_FORMAT)

    @property
    def api(self) -> APISettings:
        return APISettings(host=self.API_HOST, port=self.API_PORT)

    @property
    def cli(self) -> CLISettings:
        return CLISettings(ansi_colors=self.CLI_ANSI_COLORS)

    @property
    def storage(self) -> ProjectStorageSettings:
        return ProjectStorageSettings(base_dir=self.PROJECT_STORAGE_BASE_DIR)

    @property
    def cache(self) -> CacheSettings:
        return CacheSettings(enabled=self.CACHE_ENABLED, ttl_seconds=self.CACHE_TTL_SECONDS)

    @property
    def experimental(self) -> ExperimentalSettings:
        return ExperimentalSettings(enable_new_parser=self.EXPERIMENTAL_ENABLE_NEW_PARSER)

    @property
    def graph(self) -> GraphSettings:
        return GraphSettings(
            provider=self.GRAPH_PROVIDER,
            neo4j_uri=self.NEO4J_URI,
            neo4j_username=self.NEO4J_USERNAME,
            neo4j_password=self.NEO4J_PASSWORD
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


def load_settings() -> Settings:
    """
    Loads centralized configuration based on active profile and env overrides.
    """
    profile = os.environ.get("ECIP_PROFILE", "development").lower()
    if profile not in {"development", "testing", "production"}:
        logger.error(f"Invalid profile '{profile}' requested.")
        profile = "development"

    # Pre-populate init dictionary with profile overrides mapped to flat names
    profile_data = PROFILE_DEFAULTS.get(profile, {})
    init_kwargs: Dict[str, Any] = {"ECIP_PROFILE": profile}

    # Map profile dictionary structured values to flat keys
    if "database" in profile_data:
        init_kwargs["DB_PATH"] = profile_data["database"].get("db_path")
    if "faiss" in profile_data:
        init_kwargs["FAISS_INDEX_PATH"] = profile_data["faiss"].get("index_path")
        init_kwargs["FAISS_METADATA_PATH"] = profile_data["faiss"].get("metadata_path")
    if "logging" in profile_data:
        init_kwargs["LOG_LEVEL"] = profile_data["logging"].get("level")
    if "api" in profile_data:
        init_kwargs["API_HOST"] = profile_data["api"].get("host")
        init_kwargs["API_PORT"] = profile_data["api"].get("port")
    if "cli" in profile_data:
        init_kwargs["CLI_ANSI_COLORS"] = profile_data["cli"].get("ansi_colors")
    if "cache" in profile_data:
        init_kwargs["CACHE_ENABLED"] = profile_data["cache"].get("enabled")

    # In pydantic settings, we want environment variables to take priority.
    # BaseSettings automatically loads env variables and dotenv file on top of init_kwargs,
    # but ONLY for fields NOT passed as kwargs. If they are in init_kwargs, kwargs take priority.
    # To fix this, we filter out any kwargs that are present in os.environ, allowing env vars to override.
    # We also load dotenv manually if it exists to allow dotenv overrides to override profile defaults.
    from dotenv import dotenv_values
    dotenv_data = dotenv_values(".env") if profile == "development" else {}

    # Remove keys from init_kwargs if they exist in env or dotenv, so env/dotenv overrides win
    flat_to_domain_mapping = {
        "DB_PATH": "database__db_path",
        "FAISS_INDEX_PATH": "faiss__index_path",
        "FAISS_METADATA_PATH": "faiss__metadata_path",
        "LOG_LEVEL": "logging__level",
        "API_HOST": "api__host",
        "API_PORT": "api__port",
        "CLI_ANSI_COLORS": "cli__ansi_colors",
        "CACHE_ENABLED": "cache__enabled",
        "GRAPH_PROVIDER": "graph__provider",
        "NEO4J_URI": "graph__neo4j_uri",
        "NEO4J_USERNAME": "graph__neo4j_username",
        "NEO4J_PASSWORD": "graph__neo4j_password",
    }

    keys_to_clear = []
    for k in init_kwargs.keys():
        # Check direct env name
        if k in os.environ:
            keys_to_clear.append(k)
            continue
        if k in dotenv_data:
            keys_to_clear.append(k)
            continue
        # Check mapped/nested env name
        mapped_env = flat_to_domain_mapping.get(k)
        if mapped_env and (mapped_env in os.environ or mapped_env.upper() in os.environ):
            keys_to_clear.append(k)
            continue

    for k in keys_to_clear:
        init_kwargs.pop(k, None)

    try:
        settings_instance = Settings(**init_kwargs)
        logger.info(f"Configuration loaded")
        logger.info(f"Active profile: {settings_instance.ECIP_PROFILE}")
        return settings_instance
    except Exception as e:
        logger.error(f"Invalid configuration: {e}")
        raise


# Initialize the settings singleton
settings = load_settings()

# Apply backward compatibility patches to external modules (including SQLite repository singleton)
try:
    from ecip_core.storage.sqlite.database import Database
    db_instance = Database()
    logger.info("Database singleton initialized using dynamic configuration paths")
except Exception as e:
    logger.warning(f"Could not initialize Database connection: {e}")

# Inject our settings singleton into the old settings module to keep all old imports working
try:
    import ecip_core.inference.config.settings as old_settings
    old_settings.settings = settings
    logger.info("Backward compatibility settings patch applied successfully")
except Exception as e:
    logger.warning(f"Could not patch backward compatibility settings: {e}")
