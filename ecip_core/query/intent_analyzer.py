import re
from ecip_core.common.logger import get_logger
from ecip_core.query.intent import QueryIntent
from ecip_core.query.models.intent_result import IntentResult

logger = get_logger(__name__)


class IntentAnalyzer:
    """
    Classifies user queries into semantic intent categories with confidence scores.
    """

    def __init__(self):
        # Rules format: (intent_name, list_of_regexes, list_of_keywords, base_confidence)
        self.rules = [
            (
                "explain_code",
                [
                    r"\b(?:explain|describe|overview of|summarize|what is|how does)\s+(?:class|file|interface|enum|module|code)\b",
                    r"\b(?:explain|describe|overview of|summarize|what is)\s+[A-Z][a-zA-Z0-9_]*\b",
                ],
                ["explain", "describe", "overview", "summarize", "about class", "explain class"],
                0.8
            ),
            (
                "explain_method",
                [
                    r"\b(?:explain|describe|show|how does)\s+(?:method|function|endpoint)\s+[a-z0-9_]+\b",
                    r"\b(?:explain|describe|show)\s+(?!all\b|endpoints\b|routes\b|apis\b)[a-z][a-zA-Z0-9_]*\b",
                ],
                ["explain", "explain method", "what does method", "how does method", "show method", "method"],
                0.8
            ),
            (
                "dependency_analysis",
                [
                    r"\b(?:what|who|which)\s+(?:depends on|uses|imports|calls)\b",
                    r"\b(?:dependencies of|dependency|dependency graph)\b",
                ],
                ["depends on", "dependencies", "imports", "calls", "uses", "what depends on", "who uses"],
                0.8
            ),
            (
                "impact_analysis",
                [
                    r"\b(?:what breaks|impact of|affected by|if i change|changing)\b",
                    r"\b(?:impact|affect|breaks|breaking)\b",
                ],
                ["impact", "affect", "breaks", "changing", "if i change", "what breaks", "side effects"],
                0.8
            ),
            (
                "endpoint_lookup",
                [
                    r"\b(?:show|find|list|get|post|delete|put|patch)\s+(?:endpoints|routes|apis|controllers)\b",
                    r"\b(?:mapping|restcontroller|getmapping|postmapping|requestmapping)\b",
                ],
                ["endpoints", "routes", "apis", "controllers", "rest", "mapping", "getmapping", "postmapping"],
                0.85
            ),
            (
                "navigation",
                [
                    r"\b(?:open|show|find|locate|where is|go to|view)\s+(?:file|class|code)\b",
                    r"\b(?:where is|locate|open)\s+[A-Za-z0-9_\-\./\\]+\.java\b",
                ],
                ["open", "show", "find", "locate", "where is", "go to", "view file"],
                0.8
            ),
            (
                "semantic_question",
                [
                    r"\b(?:how to|how do we|how does|why does|what happens when|explain how|what is)\b",
                    r"\b(?:handled|implemented|configured|designed)\b",
                ],
                ["how to", "how do we", "why does", "what happens when", "how is", "how do I", "what is"],
                0.6
            )
        ]

    def analyze(self, query: str) -> IntentResult:
        """
        Normalized analysis of a user question returning IntentResult.
        """
        logger.info("Intent analysis started")

        if not query or not query.strip():
            logger.info("Empty query classified as unknown intent")
            return IntentResult(
                intent="unknown",
                confidence=0.0,
                matched_patterns=[],
                normalized_query=""
            )

        # Normalize query
        normalized = query.strip().lower()
        normalized = re.sub(r"\s+", " ", normalized)

        best_intent = "unknown"
        best_confidence = 0.0
        best_matches = []

        # Find matching rules
        for intent, patterns, keywords, base_conf in self.rules:
            matched_patterns = []

            for pattern in patterns:
                if "[A-Z]" in pattern:
                    if re.search(pattern, query):
                        matched_patterns.append(pattern)
                else:
                    if re.search(pattern, query, re.IGNORECASE):
                        matched_patterns.append(pattern)

            for keyword in keywords:
                if keyword in normalized:
                    matched_patterns.append(keyword)

            if matched_patterns:
                confidence = base_conf
                # Increment confidence score for extra matched patterns
                extra_matches = len(set(matched_patterns)) - 1
                confidence += extra_matches * 0.1
                confidence = min(1.0, confidence)

                if confidence > best_confidence:
                    best_confidence = confidence
                    best_intent = intent
                    best_matches = list(set(matched_patterns))

        if best_intent == "unknown" or best_confidence == 0.0:
            best_intent = "unknown"
            best_confidence = 0.0
            best_matches = []

        logger.info(f"Intent detected: {best_intent}")
        logger.info(f"Confidence score: {best_confidence:.4f}")

        if 0.0 < best_confidence < 0.5:
            logger.warning(f"Low confidence intent: {best_intent}")

        return IntentResult(
            intent=best_intent,
            confidence=best_confidence,
            matched_patterns=best_matches,
            normalized_query=normalized
        )

    def detect(self, question: str) -> QueryIntent:
        """
        Backward compatible detector for older QueryCoordinator.
        """
        q = question.lower()

        if "list" in q and "file" in q:
            return QueryIntent.LIST_FILES

        if "methods" in q:
            return QueryIntent.FIND_METHODS

        if "class" in q:
            return QueryIntent.FIND_CLASS

        if "where is" in q:
            return QueryIntent.FIND_FILE_BY_METHOD

        return QueryIntent.LLM