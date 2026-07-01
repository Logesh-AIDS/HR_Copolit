# services/interview-engine/app/state_machine.py
import json
import time
from typing import Dict, Any, Optional

class MockRedis:
    def __init__(self):
        self.store = {}
    def get(self, key):
        return self.store.get(key)
    def set(self, key, val, ex=None):
        self.store[key] = val
        return True

from services.common.redis_client import redis_cache

class InterviewStateMachine:
    def __init__(self, redis_client=None):
        self.redis = redis_client if redis_client is not None else redis_cache.get_client()

    def _get_session_key(self, token: str) -> str:
        return f"interview_session:{token}"

    def initialize_session(self, token: str, application_id: str, duration: int = 3600) -> Dict[str, Any]:
        state = {
            "application_id": application_id,
            "token": token,
            "status": "PLANNING",
            "current_stage": "MCQ",
            "current_question_index": 0,
            "questions_sequence": [],
            "answers": {},
            "start_time": None,
            "paused_time": None,
            "accumulated_pause_duration": 0,
            "total_duration_seconds": duration,
            "completed": False
        }
        self.redis.set(self._get_session_key(token), json.dumps(state))
        return state

    def load_session(self, token: str) -> Optional[Dict[str, Any]]:
        data = self.redis.get(self._get_session_key(token))
        if data:
            if isinstance(data, bytes):
                data = data.decode('utf-8')
            return json.loads(data)
        return None

    def save_session(self, token: str, state: Dict[str, Any]):
        self.redis.set(self._get_session_key(token), json.dumps(state))

    def start_timer(self, token: str) -> Dict[str, Any]:
        state = self.load_session(token)
        if not state:
            raise ValueError("Session not found")
        
        now = time.time()
        if state["status"] == "PLANNING":
            state["status"] = "ACTIVE"
            state["start_time"] = now
        elif state["status"] == "PAUSED":
            state["status"] = "ACTIVE"
            # Calculate how long the user was disconnected / paused
            if state["paused_time"]:
                pause_duration = now - state["paused_time"]
                state["accumulated_pause_duration"] += pause_duration
                state["paused_time"] = None
                
        self.save_session(token, state)
        return state

    def pause_session(self, token: str) -> Dict[str, Any]:
        state = self.load_session(token)
        if not state:
            raise ValueError("Session not found")
        
        if state["status"] == "ACTIVE":
            state["status"] = "PAUSED"
            state["paused_time"] = time.time()
            
        self.save_session(token, state)
        return state

    def get_remaining_time(self, token: str) -> int:
        state = self.load_session(token)
        if not state:
            return 0
        if not state["start_time"]:
            return state["total_duration_seconds"]

        now = time.time()
        elapsed = now - state["start_time"] - state["accumulated_pause_duration"]
        if state["status"] == "PAUSED" and state["paused_time"]:
            elapsed -= (now - state["paused_time"])

        remaining = int(state["total_duration_seconds"] - elapsed)
        return max(0, remaining)

    def submit_answer(self, token: str, answer_payload: Any) -> Dict[str, Any]:
        state = self.load_session(token)
        if not state or state["completed"]:
            raise ValueError("Session unavailable or completed")

        idx = state["current_question_index"]
        stage = state["current_stage"]
        
        # Save response
        key = f"{stage}_{idx}"
        state["answers"][key] = answer_payload
        
        # Advance index or stage
        state["current_question_index"] += 1
        
        # Check if we should transition stages
        # Mock simple stage limits: 2 MCQs, 1 Coding, 1 Behavioral
        max_questions_for_stage = {
            "MCQ": 2,
            "CODING": 1,
            "SYSTEM_DESIGN": 1
        }
        
        current_limit = max_questions_for_stage.get(stage, 1)
        if state["current_question_index"] >= current_limit:
            # Transition to next stage
            state["current_question_index"] = 0
            if stage == "MCQ":
                state["current_stage"] = "CODING"
            elif stage == "CODING":
                state["current_stage"] = "SYSTEM_DESIGN"
            else:
                state["completed"] = True
                state["status"] = "COMPLETED"

        self.save_session(token, state)
        return state
