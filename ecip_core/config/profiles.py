from typing import Dict, Any

PROFILE_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "development": {
        "database": {"db_path": "data/ecip.db"},
        "faiss": {
            "index_path": ".ecip/faiss.index",
            "metadata_path": ".ecip/faiss_metadata.json",
        },
        "logging": {"level": "INFO"},
        "api": {"host": "127.0.0.1", "port": 8000},
        "cli": {"ansi_colors": True},
    },
    "testing": {
        "database": {"db_path": "data/ecip_test.db"},
        "faiss": {
            "index_path": ".ecip/faiss_test.index",
            "metadata_path": ".ecip/faiss_metadata_test.json",
        },
        "logging": {"level": "WARNING"},
        "api": {"host": "127.0.0.1", "port": 8001},
        "cli": {"ansi_colors": False},
        "cache": {"enabled": False},
    },
    "production": {
        "database": {"db_path": "data/ecip_prod.db"},
        "faiss": {
            "index_path": ".ecip/faiss_prod.index",
            "metadata_path": ".ecip/faiss_metadata_prod.json",
        },
        "logging": {"level": "ERROR"},
        "api": {"host": "0.0.0.0", "port": 80},
        "cli": {"ansi_colors": True},
    },
}
