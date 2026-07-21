import time
from fastapi import APIRouter, HTTPException, Depends
from ecip_core.common.logger import get_logger
from ecip_core.api.models.query import QueryRequest, QueryResponse, CitationModel
from ecip_core.models.request import InferenceRequest
from ecip_core.coordinator.query_coordinator import QueryCoordinator
from ecip_core.storage.sqlite.repository import JavaRepository
from ecip_core.workspace.manager import workspace_manager

logger = get_logger(__name__)

router = APIRouter()

_coordinator = None


def get_coordinator() -> QueryCoordinator:
    global _coordinator
    if _coordinator is None:
        _coordinator = QueryCoordinator()
    return _coordinator


@router.post("/query", response_model=QueryResponse)
async def query_pipeline(
    request: QueryRequest,
    coordinator: QueryCoordinator = Depends(get_coordinator)
):
    logger.info("Request received")

    # 1. Input validations
    if not request.question or not request.question.strip():
        logger.warning("Empty question")
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    if not request.project_id or not request.project_id.strip():
        logger.warning("Unknown project")
        raise HTTPException(status_code=400, detail="Project ID cannot be empty")

    # 2. Resolve project — check against registered workspaces
    try:
        workspace = workspace_manager.get_workspace(request.project_id)
        if not workspace:
            # Also allow "default" as a fallback — check if any project is indexed
            if request.project_id != "default":
                logger.warning(f"Unknown workspace: {request.project_id}")
                raise HTTPException(status_code=404, detail=f"Project '{request.project_id}' not found. Register it first via POST /api/v1/workspaces")
        workspace_manager.set_active_workspace(request.project_id)
        logger.info("Project resolved and activated")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Workspace lookup error: {e}")
        raise HTTPException(status_code=500, detail="Workspace lookup failed")

    # Verify project index is not empty
    try:
        repo = JavaRepository()
        files = repo.get_all_file_paths()
        if not files:
            logger.warning("No indexed project")
            raise HTTPException(status_code=404, detail="No indexed project found. Run POST /api/v1/index first")
        logger.info("Index verified")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pipeline failure: database lookup error: {e}")
        raise HTTPException(status_code=500, detail="Database access error")

    # 3. Execute QA pipeline
    start_time = time.perf_counter()
    
    history_list = [h.model_dump() for h in request.history] if request.history else None

    if request.stream:
        import queue
        import threading
        import json
        from fastapi.responses import StreamingResponse

        token_queue = queue.Queue()

        def callback(token: str):
            token_queue.put({"type": "token", "text": token})

        def run_pipeline():
            try:
                inference_req = InferenceRequest(
                    question=request.question,
                    project_id=request.project_id,
                    history=history_list
                )
                coordinator_res = coordinator.process(inference_req, callback=callback)
                
                # Map citations
                citations = []
                if coordinator_res.citations:
                    for c in coordinator_res.citations:
                        citations.append({
                            "file_path": c.file_path,
                            "class_name": c.class_name,
                            "method_name": c.method_name or "",
                            "start_line": c.start_line or 0,
                            "end_line": c.end_line or 0
                        })
                
                duration_ms = int((time.perf_counter() - start_time) * 1000)
                token_queue.put({
                    "type": "done",
                    "citations": citations,
                    "model_name": coordinator_res.model or "local-llm",
                    "duration_ms": duration_ms
                })
            except ConnectionError as e:
                logger.error(f"Provider unavailable: {e}")
                token_queue.put({"type": "error", "message": "Inference Provider Unavailable"})
            except TimeoutError as e:
                logger.error(f"Pipeline failure: inference timeout: {e}")
                token_queue.put({"type": "error", "message": "Inference Provider Unavailable"})
            except Exception as e:
                logger.error(f"Unexpected exception: {e}")
                token_queue.put({"type": "error", "message": "Internal Server Error"})
            finally:
                token_queue.put(None)

        # Start thread
        thread = threading.Thread(target=run_pipeline)
        thread.start()

        def event_generator():
            while True:
                item = token_queue.get()
                if item is None:
                    break
                yield json.dumps(item) + "\n"

        return StreamingResponse(event_generator(), media_type="application/x-ndjson")
    else:
        try:
            inference_req = InferenceRequest(
                question=request.question,
                project_id=request.project_id,
                history=history_list
            )
            coordinator_res = coordinator.process(inference_req)
        except ConnectionError as e:
            logger.error(f"Provider unavailable: {e}")
            raise HTTPException(status_code=503, detail="Inference Provider Unavailable")
        except TimeoutError as e:
            logger.error(f"Pipeline failure: inference timeout: {e}")
            raise HTTPException(status_code=503, detail="Inference Provider Unavailable")
        except Exception as e:
            logger.error(f"Unexpected exception: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

        duration_ms = int((time.perf_counter() - start_time) * 1000)
        logger.info("Query completed")

        # Map citations
        citations = []
        if coordinator_res.citations:
            for c in coordinator_res.citations:
                citations.append(
                    CitationModel(
                        file_path=c.file_path,
                        class_name=c.class_name,
                        method_name=c.method_name or "",
                        start_line=c.start_line or 0,
                        end_line=c.end_line or 0
                    )
                )

        response = QueryResponse(
            answer=coordinator_res.answer,
            citations=citations,
            model_name=coordinator_res.model or "local-llm",
            duration_ms=duration_ms
        )
        logger.info("Response returned")
        return response
