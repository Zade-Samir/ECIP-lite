import re
from ecip_core.common.logger import get_logger
from ecip_core.query.models.entity_result import EntityResult

logger = get_logger(__name__)


class EntityExtractor:
    """
    Identifies project-specific entities from a user query before retrieval begins.
    """

    def __init__(self):
        self.class_ignore = {
            "Explain", "Show", "List", "Find", "Where", "What", "Which",
            "Give", "Get", "Display", "How", "Why", "When", "Java", "Spring",
            "Entity", "Service", "Repository", "Controller", "REST", "Endpoint",
            "Search", "Open", "View", "Create", "Update", "Delete",
            "GET", "POST", "PUT", "PATCH"
        }

        self.method_ignore = {
            "explain", "show", "list", "find", "where", "what", "which",
            "give", "get", "display", "how", "why", "when", "java", "spring",
            "dependency", "depends", "impact", "controller", "service",
            "repository", "entity", "rest", "endpoint", "open", "view",
            "file", "method", "class", "package", "all", "in", "on", "at", "to", "for"
        }

    def extract_entities(self, query: str) -> list[EntityResult]:
        """
        Extracts multiple project-specific entities from the query in order.
        """
        logger.info("Entity extraction started")

        if not query or not query.strip():
            logger.info("Empty query, returning 0 entities")
            return []

        try:
            results: list[EntityResult] = []
            seen_entities = set()

            raw_tokens = query.split()

            for idx, raw_token in enumerate(raw_tokens):
                token = raw_token.strip(".,;:?!'\"()")
                if not token:
                    continue

                entity_type = None
                entity_name = token
                confidence = 0.0
                matched_text = token
                normalized_value = token.lower()

                # 1. REST Endpoint match
                if token.startswith("/") or ("/" in token and not token.endswith(".java") and not re.search(r"\b[a-z0-9]+(?:\.[a-z0-9]+)+\b", token)):
                    entity_type = "rest_endpoint"
                    confidence = 1.0 if token.startswith("/") else 0.8

                # 2. Package Name match (lowercase dotted string)
                elif "." in token and re.match(r"^[a-z0-9]+(?:\.[a-z0-9]+)+$", token):
                    entity_type = "package_name"
                    confidence = 1.0

                # 3. Class Name matches (CamelCase starting with uppercase)
                elif re.match(r"^[A-Z][A-Za-z0-9_]*$", token):
                    if token in self.class_ignore:
                        continue

                    # Sub-categorization
                    if token.endswith("Repository"):
                        entity_type = "repository_name"
                        confidence = 1.0
                    elif token.endswith("Service"):
                        entity_type = "service_name"
                        confidence = 1.0
                    elif token.endswith("Controller"):
                        entity_type = "controller_name"
                        confidence = 1.0
                    elif token.endswith("DTO") or token.endswith("Entity") or token.endswith("Model") or token.endswith("VO"):
                        entity_type = "entity_name"
                        confidence = 1.0
                    else:
                        entity_type = "class_name"
                        confidence = 0.9

                # 4. Method Name match (camelCase starting with lowercase)
                elif re.match(r"^[a-z][A-Za-z0-9_]*$", token):
                    if token in self.method_ignore:
                        continue

                    preceded_by_method = idx > 0 and raw_tokens[idx - 1].strip(".,;:?!'\"()").lower() == "method"
                    is_camel_case = re.match(r"^[a-z]+[A-Z][a-zA-Z0-9_]*$", token) is not None

                    if preceded_by_method or is_camel_case:
                        entity_type = "method_name"
                        if preceded_by_method:
                            confidence = 1.0
                            matched_text = f"{raw_tokens[idx - 1]} {raw_token}"
                        else:
                            confidence = 0.8

                if entity_type:
                    dup_key = (entity_type, entity_name)
                    if dup_key not in seen_entities:
                        seen_entities.add(dup_key)
                        res = EntityResult(
                            entity_type=entity_type,
                            entity_name=entity_name,
                            confidence=confidence,
                            matched_text=matched_text,
                            normalized_value=normalized_value
                        )
                        results.append(res)
                        logger.info(f"Entity detected: type={entity_type}, name={entity_name}")

                        if confidence < 0.9:
                            logger.warning(f"Ambiguous entity: type={entity_type}, name={entity_name}")

            logger.info(f"Total entities: {len(results)}")
            return results

        except Exception as e:
            logger.error(f"Extraction failure: {e}")
            raise

    def extract_class_name(self, question: str) -> str | None:
        """
        Backward compatible helper to extract the first class-like name.
        """
        class_types = {"class_name", "service_name", "repository_name", "controller_name", "entity_name"}
        entities = self.extract_entities(question)
        for ent in entities:
            if ent.entity_type in class_types:
                return ent.entity_name
        return None

    def extract_method_name(self, question: str) -> str | None:
        """
        Backward compatible helper to extract the first method-like name.
        """
        entities = self.extract_entities(question)
        for ent in entities:
            if ent.entity_type == "method_name":
                return ent.entity_name
        return None