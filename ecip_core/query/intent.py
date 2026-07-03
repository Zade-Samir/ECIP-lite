from enum import Enum


class QueryIntent(str, Enum):

    LIST_FILES = "LIST_FILES"

    FIND_CLASS = "FIND_CLASS"

    FIND_METHODS = "FIND_METHODS"

    FIND_FILE_BY_METHOD = "FIND_FILE_BY_METHOD"

    LLM = "LLM"