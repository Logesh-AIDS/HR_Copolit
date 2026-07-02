# services/interview-engine/app/main.py
import json
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from services.common import settings, configure_logging, register_exception_handlers, redis_cache
from services.common.middleware import RateLimitMiddleware, RequestLoggingMiddleware
from app.state_machine import InterviewStateMachine
from app.prompt_orchestrator import PromptOrchestrator

# Initialize structured logging
configure_logging()
logger = logging.getLogger(__name__)

# Base application with configuration settings loaded
app = FastAPI(
    title="HR-Copilot Live Interview Engine",
    description="WebSocket-driven conversational engine delivering adaptive interview plans.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Centralized exception handlers registration
register_exception_handlers(app)

from app.delivery.http.orchestrator_router import router as orchestrator_router
app.include_router(orchestrator_router, prefix="/api/v1")

from app.delivery.http.execution_router import router as execution_router
app.include_router(execution_router, prefix="/api/v1")

from app.delivery.http.webrtc_router import router as webrtc_router
app.include_router(webrtc_router, prefix="/api/v1")

# Security and request logs middlewares
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engine sub-components using production Redis cache client
redis_client = redis_cache.get_client()
fsm = InterviewStateMachine(redis_client=redis_client)
orchestrator = PromptOrchestrator()

from services.common.database import SessionLocal
from app.adapter.db.execution_repo import ExecutionRepository
from app.adapter.db.interview_repo import InterviewRepository
from app.domain.services.execution_service import ExecutionService
from app.domain.services.orchestrator_service import OrchestratorService

# In-memory connection tracker mapping active sessions
# Key: session_token -> WebSocket connection
active_connections = {}

# WebRTC signaling active sockets room tracker
# Key: session_id -> Set[WebSocket]
webrtc_rooms_websockets = {}

from app.adapter.db.webrtc_repo import WebRTCRepository
from app.domain.services.webrtc_service import WebRTCService

class ConnectionManager:
    async def connect(self, websocket: WebSocket, token: str):
        await websocket.accept()
        active_connections[token] = websocket
        logger.info(f"WebSocket session established for token: {token}")

    def disconnect(self, token: str):
        if token in active_connections:
            del active_connections[token]
            logger.info(f"WebSocket session disconnected for token: {token}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

manager = ConnectionManager()

@app.websocket("/api/v1/interview/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    db = SessionLocal()
    repo = ExecutionRepository(db)
    plan_repo = InterviewRepository(db)
    exec_service = ExecutionService(repo, plan_repo)
    orch_service = OrchestratorService(plan_repo)
    
    try:
        session = repo.get_session_by_token(token)
    except Exception as e:
        logger.error(f"Error loading session token: {token}. Exception: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        db.close()
        return

    if not session:
        logger.warning(f"WebSocket connection rejected. Invalid session token: {token}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        db.close()
        return

    session_id = str(session.id)

    # Accept connection and register session
    await manager.connect(websocket, token)
    
    if session_id not in webrtc_rooms_websockets:
        webrtc_rooms_websockets[session_id] = set()
    webrtc_rooms_websockets[session_id].add(websocket)
    
    # Handle reconnect logic if disconnected previously
    try:
        if session.status == "DISCONNECTED" or session.status == "PAUSED":
            exec_service.reconnect_session(token)
    except Exception as e:
        logger.error(f"Error reconnecting session: {e}")

    # Notify user connection is established
    remaining = session.runtime_state.remaining_time_seconds if session.runtime_state else 3600
    await manager.send_personal_message({
        "event": "session_status",
        "status": "connected",
        "remaining_seconds": remaining,
        "state": session.status
    }, websocket)

    try:
        while True:
            # Handle incoming messages
            data = await websocket.receive_text()
            payload = json.loads(data)
            
            event = payload.get("event")
            
            if event == "heartbeat":
                # Deduct 5 seconds for timer ticks in real-time execution
                exec_service.record_timer_tick(session_id, 5)
                remaining = session.runtime_state.remaining_time_seconds if session.runtime_state else 3600
                await manager.send_personal_message({
                    "event": "heartbeat_ack",
                    "remaining_seconds": remaining
                }, websocket)
                
            elif event in {"webrtc_offer", "webrtc_answer", "webrtc_ice_candidate"}:
                peer_id = payload.get("peer_id", "CANDIDATE")
                webrtc_service = WebRTCService(WebRTCRepository(db))
                webrtc_service.log_event(
                    session_id=session_id,
                    peer_id=peer_id,
                    event_type=event,
                    details=f"Forwarding SDP/ICE handshake event: {event}"
                )
                
                # Relay to peer
                sockets = webrtc_rooms_websockets.get(session_id, set())
                for client_ws in sockets:
                    if client_ws != websocket:
                        try:
                            await client_ws.send_json(payload)
                        except Exception as e:
                            logger.error(f"Failed to relay WebRTC packet: {e}")

            elif event == "submit_answer":
                answer = payload.get("answer")
                # Advance status and adapt question difficulty dynamically
                # Award dummy score based on answer length for mock evaluations
                score = min(10.0, float(len(str(answer)) / 5.0))
                
                # Update orchestrator state & evaluate adaptive triggers
                if session.interview_plan_id:
                    orch_service.submit_answer_and_adapt(
                        plan_id=str(session.interview_plan_id),
                        question_score=score
                    )
                
                # Check for completion
                is_completed = session.runtime_state.is_completed if session.runtime_state else False
                if is_completed:
                    await manager.send_personal_message({
                        "event": "session_completed",
                        "verdict": "Interview completed successfully. Report compiled."
                    }, websocket)
                    break
                
                # Fetch next question indices from adjusted state
                round_idx = session.runtime_state.current_round_index if session.runtime_state else 0
                quest_idx = session.runtime_state.current_question_index if session.runtime_state else 0
                
                # Trigger question running state in execution engine
                try:
                    exec_service.start_question(session_id, quest_idx)
                except Exception:
                    pass
                
                await manager.send_personal_message({
                    "event": "next_question",
                    "stage": round_idx,
                    "index": quest_idx,
                    "question": f"Detail your solution for round {round_idx} question {quest_idx}.",
                    "score_summary": score,
                    "feedback_tip": "Focus on scalability."
                }, websocket)
                
            elif event == "client_log":
                logger.info(f"[Telemetry][{token}]: {payload.get('log')}")
                
    except WebSocketDisconnect:
        manager.disconnect(token)
        if session_id in webrtc_rooms_websockets:
            webrtc_rooms_websockets[session_id].discard(websocket)
        # Pause elapsed timer dynamically on socket disconnect (grace period)
        exec_service.disconnect_session(session_id)
        logger.info(f"WebSocket connection closed for token: {token}")
    finally:
        db.close()


# System Health and Probe Endpoints
@app.get("/health", tags=["System"])
@app.get("/live", tags=["System"])
def liveness_check():
    """
    Liveness probe ensuring the web server process is running.
    """
    return {"status": "healthy", "service": "interview-engine"}


@app.get("/ready", tags=["System"])
def readiness_check():
    """
    Readiness probe validating underlying resource availability (Redis).
    """
    try:
        # Check Redis connection
        redis_client.ping()
    except Exception as e:
        logger.error(f"Readiness check failed: Redis unreachable. Exception: {e}")
        raise HTTPException(status_code=503, detail="Redis server is unreachable")
        
    return {"status": "ready", "service": "interview-engine"}


@app.get("/version", tags=["System"])
def version():
    """
    Returns API version.
    """
    return {"version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8003, reload=True)
