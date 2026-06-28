from ecip_core.inference.inference_service import InferenceService
from ecip_core.models.request import InferenceRequest
from ecip_core.models.response import InferenceResponse


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

        return self.inference_service.ask(request)