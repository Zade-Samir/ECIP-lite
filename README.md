from pydantic import BaseModel


class CodeChunk(BaseModel):
    """
    Represents a chunk of Java source code.
    """

    file_name: str

    class_name: str

    method_name: str

    source_code: str


from pathlib import Path

from ecip_core.chunking.code_chunk import CodeChunk


class JavaChunker:

    def chunk(
        self,
        file_path: str
    ) -> list[CodeChunk]:

        path = Path(file_path)

        with open(path, "r", encoding="utf-8") as file:
            source = file.read()

        return [
            CodeChunk(
                file_name=path.name,
                class_name="Unknown",
                method_name="WholeFile",
                source_code=source,
            )
        ]


import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger instance.
    Every ECIP module should use this logger.
    """

    logger = logging.getLogger(name)

    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    return logger


from ecip_core.inference.inference_service import InferenceService
from ecip_core.models.request import InferenceRequest
from ecip_core.models.response import InferenceResponse

from ecip_core.common.logger import get_logger

logger = get_logger(__name__)

class QueryCoordinator:
    """
    Main workflow coordinator of ECIP.

    Responsibilities:
    - Receive user requests.
    - Coordinate the complete processing pipeline.
    - Delegate inference to InferenceService.

    Future Responsibilities:
    - Project validation
    - Parser execution
    - Chunk retrieval
    - Project Memory
    - Graph Traversal
    - Context Assembly
    """

    def __init__(self):
        self.inference_service = InferenceService()

    def process(
        self,
        request: InferenceRequest
    ) -> InferenceResponse:

        logger.info("Received new query.")

        return self.inference_service.ask(request)

        logger.info("Query processed successfully.")


