"""
FastAPI Application Entrypoint for AmazonHelp AI Support Platform
"""

import logging
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("amazonhelp_api")

from src.api.models import (
    AgentRespondRequest,
    AgentRespondResponse,
    AnalyzeRequest,
    AnalyzeResponse,
    ClassifyRequest,
    ClassifyResponse,
    ConfusionMatrixResponse,
    DraftReplyRequest,
    DraftReplyResponse,
    HealthResponse,
    TicketDetail,
    TicketsResponse,
)
from src.api.services import (
    AgentService,
    EvaluationService,
    TicketService,
    RETRIEVAL_INDEX_PATH,
    GOLDEN_EXCLUSIONS_PATH,
    EVAL_RESULTS_PATH,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("[Startup] Preloading AmazonHelp Agent & Retrieval Index...")
    AgentService.get_agent()
    logger.info("[Startup] Preloading real customer tickets...")
    TicketService.initialize(max_threads=150)
    logger.info("[Startup] Preloading evaluation benchmarks & confusion matrix cache...")
    EvaluationService.get_summary()
    EvaluationService.get_confusion_matrix()
    logger.info("[Startup] All subsystems initialized and operational.")
    yield
    logger.info("[Shutdown] Clean shutdown completed.")


app = FastAPI(
    title="AmazonHelp AI Support Platform API",
    description="Production REST API serving the AmazonHelp AI agent, support queue, and evaluation benchmarks.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for API clients and web dashboards
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/dashboard", include_in_schema=False)
def dashboard():
    """Serve the dependency-free live demo dashboard."""
    return FileResponse(ROOT_DIR / "dashboard.html")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Logs incoming request, outgoing response, and execution latency."""
    start_time = time.perf_counter()
    path = request.url.path
    method = request.method
    logger.info(f"--> {method} {path}")

    try:
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.info(f"<-- {method} {path} {response.status_code} ({duration_ms:.2f}ms)")
        response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"
        return response
    except Exception as e:
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.error(f"<-- {method} {path} ERROR: {str(e)} ({duration_ms:.2f}ms)")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"Internal server error: {str(e)}"},
        )


# =====================================================================
# SYSTEM & HEALTH ENDPOINTS
# =====================================================================

@app.get("/health", response_model=HealthResponse, tags=["System"])
def health_check():
    """Returns backend health, retrieval index status, and evaluation readiness."""
    index_loaded = RETRIEVAL_INDEX_PATH.exists()
    exclusions_count = 0
    if GOLDEN_EXCLUSIONS_PATH.exists():
        import json
        with open(GOLDEN_EXCLUSIONS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            exclusions_count = len(data.get("excluded_tweet_ids", []))

    return HealthResponse(
        status="healthy",
        retrieval_index_loaded=index_loaded,
        retrieval_records_count=20000 if index_loaded else 0,
        exclusions_active_count=exclusions_count,
        evaluation_artifacts_ready=EVAL_RESULTS_PATH.exists(),
        version="1.0.0",
    )


# =====================================================================
# AGENT INFERENCE & CLASSIFICATION ENDPOINTS
# =====================================================================

@app.post("/classify", response_model=ClassifyResponse, tags=["AI Agent"])
@app.post("/api/classify", response_model=ClassifyResponse, tags=["AI Agent"], include_in_schema=False)
def classify_message(payload: ClassifyRequest):
    """
    Classifies an incoming customer message into the locked 10-intent taxonomy,
    language code, and conversation state.
    """
    clean_text = payload.text.strip()
    if not clean_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Customer message text cannot be empty",
        )

    try:
        res = AgentService.classify_message(clean_text)
        return ClassifyResponse(**res)
    except Exception as e:
        logger.error(f"Classification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Classification failed: {str(e)}",
        )


@app.post("/agent/respond", response_model=AgentRespondResponse, tags=["AI Agent"])
@app.post("/api/agent/respond", response_model=AgentRespondResponse, tags=["AI Agent"], include_in_schema=False)
@app.post("/api/analyze", response_model=AgentRespondResponse, tags=["AI Agent"], include_in_schema=False)
def agent_respond(payload: AgentRespondRequest):
    """
    Full agent pipeline execution:
    1. Classifies customer intent across 10 locked classes.
    2. Detects language and conversation state.
    3. Retrieves top-k nearest historical AmazonHelp resolution evidence.
    4. Evaluates deterministic escalation rules (P0 security, high severity, low confidence).
    5. Drafts a grounded response anchored in retrieved historical guidance.
    """
    clean_text = payload.text.strip()
    if not clean_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Customer message text cannot be empty",
        )

    try:
        result = AgentService.analyze_message(clean_text, top_k=3, conversation_id=payload.conversation_id)
        return AgentRespondResponse(**result)
    except TimeoutError as te:
        logger.warning(f"Upstream LLM timeout: {te}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Upstream model call timed out. Fallback escalated to human.",
        )
    except Exception as e:
        logger.error(f"Agent pipeline execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent response pipeline failed: {str(e)}",
        )


# =====================================================================
# EVALUATION & BENCHMARK ENDPOINTS
# =====================================================================

@app.get("/evaluation/summary", tags=["Evaluation"])
@app.get("/api/evaluation/summary", tags=["Evaluation"], include_in_schema=False)
def get_evaluation_summary():
    """
    Returns actual measured benchmark metrics comparing Main Agent vs Baselines,
    including accuracy, Macro F1, escalation precision/recall, and judge ratings.
    """
    return EvaluationService.get_summary()


@app.get("/evaluation/confusion-matrix", response_model=ConfusionMatrixResponse, tags=["Evaluation"])
@app.get("/api/evaluation/confusion-matrix", response_model=ConfusionMatrixResponse, tags=["Evaluation"], include_in_schema=False)
def get_confusion_matrix():
    """
    Returns the 10x10 intent confusion matrix, per-intent precision/recall/F1,
    and top boundary confusion pairs calculated from the 200-case evaluation set.
    """
    return EvaluationService.get_confusion_matrix()


@app.get("/api/evaluation/errors", tags=["Evaluation"])
def get_evaluation_errors():
    """Returns diagnostic error categorization, P0 security audit list, and multilingual cases."""
    return EvaluationService.get_errors()


# =====================================================================
# SUPPORT TICKET QUEUE ENDPOINTS
# =====================================================================

@app.get("/api/tickets", response_model=TicketsResponse, tags=["Tickets"])
def get_tickets(
    search: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    intent: Optional[str] = None,
    language: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """Retrieves paginated, filterable support tickets from genuine AmazonHelp dialogue trees."""
    tickets, total = TicketService.list_tickets(
        search=search,
        status=status,
        priority=priority,
        intent=intent,
        language=language,
        page=page,
        limit=limit,
    )
    return TicketsResponse(
        total=total,
        page=page,
        limit=limit,
        tickets=tickets,
    )


@app.get("/api/tickets/{conversation_id}", response_model=TicketDetail, tags=["Tickets"])
def get_ticket_detail(conversation_id: str):
    """Retrieves full conversation turns, customer context, and cached AI copilot analysis."""
    ticket = TicketService.get_ticket(conversation_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket with conversation ID {conversation_id} not found",
        )
    return ticket


@app.post("/api/reply/draft", response_model=DraftReplyResponse, tags=["Composer"])
def handle_draft_action(payload: DraftReplyRequest):
    """Simulates local support agent ticket workflow actions."""
    action_map = {
        "approve": "resolved",
        "resolve": "resolved",
        "mark_human": "awaiting_human",
        "edit": "in_progress",
    }
    new_status = action_map.get(payload.action, "in_progress")
    success = TicketService.update_status(payload.conversation_id, new_status, notes=payload.notes)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation ID {payload.conversation_id} not found",
        )

    return DraftReplyResponse(
        success=True,
        conversation_id=payload.conversation_id,
        new_status=new_status,
        message=f"Action '{payload.action}' applied successfully in local simulation workspace.",
    )


@app.get("/api/search", tags=["Search"])
def search_messages(q: str = Query(..., min_length=2)):
    """Searches tickets and returns top matches."""
    tickets, total = TicketService.list_tickets(search=q, limit=10)
    return {"query": q, "total_matches": total, "results": tickets}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="127.0.0.1", port=8000, reload=True)
