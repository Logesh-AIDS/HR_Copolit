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

# In-memory connection tracker mapping active sessions
# Key: session_token -> WebSocket connection
active_connections = {}

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
    # Verify token
    try:
        state = fsm.load_session(token)
    except Exception as e:
        logger.error(f"Error loading session token: {token}. Exception: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        return

    if not state:
        logger.warning(f"WebSocket connection rejected. Invalid session token: {token}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Accept connection and register session
    await manager.connect(websocket, token)
    
    # Start timer / Handle reconnection
    state = fsm.start_timer(token)
    
    # Notify user connection is established
    await manager.send_personal_message({
        "event": "session_status",
        "status": "connected",
        "remaining_seconds": fsm.get_remaining_time(token),
        "state": state
    }, websocket)

    try:
        while True:
            # Handle incoming messages
            data = await websocket.receive_text()
            payload = json.loads(data)
            
            event = payload.get("event")
            
            if event == "heartbeat":
                await manager.send_personal_message({
                    "event": "heartbeat_ack",
                    "remaining_seconds": fsm.get_remaining_time(token)
                }, websocket)
                
            elif event == "submit_answer":
                answer = payload.get("answer")
                # Advance FSM state
                updated_state = fsm.submit_answer(token, answer)
                
                # Check for completion
                if updated_state["completed"]:
                    await manager.send_personal_message({
                        "event": "session_completed",
                        "verdict": "Interview finalized. Evaluators compiling summary report."
                    }, websocket)
                    break
                
                # Dynamic next question generation
                stage = updated_state["current_stage"]
                idx = updated_state["current_question_index"]
                
                # Fetch next question template mock
                question_prompt = f"Identify next step for stage {stage} index {idx}."
                eval_res = orchestrator.evaluate_answer_adaptively(question_prompt, str(answer))
                
                await manager.send_personal_message({
                    "event": "next_question",
                    "stage": stage,
                    "index": idx,
                    "question": eval_res.get("followup_question", "Explain your design decisions."),
                    "score_summary": eval_res.get("score"),
                    "feedback_tip": eval_res.get("feedback")
                }, websocket)
                
            elif event == "client_log":
                # WebRTC media alerts or proctor tracking frame drops
                logger.info(f"[Telemetry][{token}]: {payload.get('log')}")
                
    except WebSocketDisconnect:
        manager.disconnect(token)
        # Pause elapsed timer dynamically on socket disconnect (grace period)
        fsm.pause_session(token)
        logger.info(f"WebSocket connection closed for token: {token}")


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
