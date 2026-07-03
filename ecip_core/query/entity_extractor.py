import re


class EntityExtractor:

    def extract_class_name(self, question: str) -> str | None:

        matches = re.findall(
            r"\b([A-Z][A-Za-z0-9_]*)\b",
            question
        )

        ignore = {
            "Explain",
            "Show",
            "List",
            "Find",
            "Where",
            "What",
            "Which",
            "Give",
            "Get",
            "Display",
            "How",
            "Why",
            "When",
        }

        for word in matches:
            if word not in ignore:
                return word

        return None

    def extract_method_name(self, question: str) -> str | None:

        match = re.search(r"\b([a-z][A-Za-z0-9_]*)\b", question)

        if match:
            return match.group(1)

        return None