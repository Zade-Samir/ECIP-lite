import os
import re
from typing import List, Dict, Any, Optional
from ecip_core.common.logger import get_logger
from ecip_core.models.config_metadata import ConfigMetadata

logger = get_logger(__name__)


class ConfigParser:
    """
    Parses application.properties and application.yml configuration files
    and extracts structured properties and active profiles metadata.
    """

    def parse(self, file_path: str) -> ConfigMetadata:
        logger.info("Configuration parsed")
        metadata = ConfigMetadata(file_path=file_path)

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception as e:
            logger.error("Parse failure")
            raise e

        if not content.strip():
            return metadata

        _, ext = os.path.splitext(file_path.lower())

        properties = {}
        if ext in {".yml", ".yaml"}:
            properties = self._parse_yaml(content)
        elif ext == ".properties":
            properties = self._parse_properties(content)
        else:
            logger.warning(f"Unknown configuration key / format: {file_path}")

        metadata.properties = properties

        # Extract specific Spring profiles, server port, datasource url
        metadata.server_port = properties.get("server.port")
        metadata.datasource_url = properties.get("spring.datasource.url")

        # Profiles matching (active spring profile)
        active_profile = properties.get("spring.profiles.active") or properties.get("spring.profiles")
        if active_profile:
            # Handle list or comma-separated profile strings
            if "," in active_profile:
                metadata.profiles = [p.strip() for p in active_profile.split(",")]
            else:
                metadata.profiles = [active_profile.strip()]

        return metadata

    def _parse_properties(self, content: str) -> Dict[str, str]:
        flat = {}
        for line in content.splitlines():
            line = line.strip()
            # Ignore comments and blank lines
            if not line or line.startswith("#") or line.startswith("!"):
                continue

            if "=" in line:
                k, v = line.split("=", 1)
                flat[k.strip()] = v.strip().strip("'\"")
            elif ":" in line:
                k, v = line.split(":", 1)
                flat[k.strip()] = v.strip().strip("'\"")
        return flat

    def _parse_yaml(self, content: str) -> Dict[str, str]:
        """Custom simple line-by-line YAML parser that doesn't need external PyYAML."""
        documents = []
        current_doc = {}
        stack = [(-1, current_doc)]

        for line in content.splitlines():
            # Strip single-line comments
            if "#" in line:
                line = line.split("#")[0]

            stripped = line.strip()
            if not stripped:
                continue

            # Multi-document YAML separator
            if stripped == "---":
                if current_doc:
                    documents.append(current_doc)
                current_doc = {}
                stack = [(-1, current_doc)]
                continue

            # Check indentation depth
            indent = len(line) - len(line.lstrip())

            if ":" in stripped:
                parts = stripped.split(":", 1)
                key = parts[0].strip().strip("'\"")
                val = parts[1].strip().strip("'\"")

                # Maintain the indentation stack references
                while stack and stack[-1][0] >= indent:
                    stack.pop()

                if not stack:
                    # Fallback if indent parsing has anomalies
                    stack = [(-1, current_doc)]

                current_dict = stack[-1][1]

                if val == "":
                    # Nested block
                    new_dict = {}
                    current_dict[key] = new_dict
                    stack.append((indent, new_dict))
                else:
                    current_dict[key] = val
            elif stripped.startswith("-"):
                # Handle simple list items by treating them as comma-separated values or ignoring
                continue

        if current_doc:
            documents.append(current_doc)

        # Flatten nested dictionary to dotted properties format
        final_flat = {}
        for doc in documents:
            final_flat.update(self._flatten_dict(doc))
        return final_flat

    def _flatten_dict(self, d: Dict[str, Any], prefix: str = "") -> Dict[str, str]:
        flat = {}
        for k, v in d.items():
            key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                flat.update(self._flatten_dict(v, key))
            else:
                flat[key] = str(v)
        return flat
