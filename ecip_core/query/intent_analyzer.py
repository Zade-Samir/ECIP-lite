from ecip_core.query.intent import QueryIntent


class IntentAnalyzer:

    def detect(self, question: str) -> QueryIntent:

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