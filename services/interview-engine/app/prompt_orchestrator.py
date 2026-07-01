# services/interview-engine/app/prompt_orchestrator.py
import os
import requests
import json
from typing import Dict, Any, List

class PromptOrchestrator:
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY", "")
        self.api_url = os.getenv("LLM_API_URL", "https://api.openai.com/v1/chat/completions")
        self.model = os.getenv("LLM_MODEL", "gpt-4")

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """
        Sends requests to target LLM provider API.
        If no API Key is configured, fallbacks to generating detailed mock evaluation outputs.
        """
        if not self.api_key:
            return self._mock_llm_response(user_prompt)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2
        }
        try:
            res = requests.post(self.api_url, headers=headers, json=payload, timeout=10)
            if res.status_code == 200:
                return res.json()["choices"][0]["message"]["content"]
            return "Error calling LLM gateway."
        except Exception as e:
            return f"Exception in LLM bridge: {str(e)}"

    def _mock_llm_response(self, user_prompt: str) -> str:
        # Generate clean JSON templates based on prompt keywords to simulate LLM responses offline
        if "plan" in user_prompt.lower():
            return json.dumps({
                "stages": ["MCQ", "CODING", "SYSTEM_DESIGN"],
                "focus_areas": ["Concurrency", "Resource limits", "Caching patterns"],
                "custom_behavioral_notes": "Probe applicant regarding production scale experience."
            })
        elif "evaluate" in user_prompt.lower():
            return json.dumps({
                "score": 8.0,
                "feedback": "Code implementation has sound time complexity but lacks parameter boundary safety validations.",
                "difficulty_adjustment": "UP",
                "followup_question": "Explain how you would optimize this solution to handle large parallel streams."
            })
        return "Generic prompt parsed."

    def generate_personalized_plan(self, candidate_skills: List[str], job_description: str) -> Dict[str, Any]:
        system_prompt = (
            "You are a Staff Software Architect designing a personalized interview plan. "
            "Identify skill gaps between candidate resume coordinates and target JD requirements. "
            "Output your plan in pure JSON format: "
            '{"stages": ["MCQ", "CODING", "SYSTEM_DESIGN"], "focus_areas": ["skill1", "skill2"]}'
        )
        user_prompt = f"Candidate Skills: {candidate_skills}. Job Description: {job_description}."
        raw_res = self._call_llm(system_prompt, user_prompt)
        try:
            return json.loads(raw_res)
        except Exception:
            return {"stages": ["MCQ", "CODING", "SYSTEM_DESIGN"], "focus_areas": candidate_skills}

    def evaluate_answer_adaptively(self, question: str, response: str, language: str = None) -> Dict[str, Any]:
        system_prompt = (
            "You are an expert AI Tech Interviewer. Evaluate the candidate's answer against the prompt. "
            "Provide quantitative score (1.0 to 10.0), summary feedback, difficulty step directive ('UP', 'DOWN', or 'MAINTAIN'), "
            "and synthesize the next contextual follow-up question. "
            "Return response as a pure JSON object: "
            '{"score": 7.5, "feedback": "Explanation", "difficulty_adjustment": "UP", "followup_question": "..."}'
        )
        user_prompt = f"Question: {question}\nCandidate Response: {response}"
        if language:
            user_prompt += f"\nCode Language: {language}"

        raw_res = self._call_llm(system_prompt, user_prompt)
        try:
            return json.loads(raw_res)
        except Exception:
            return {
                "score": 5.0,
                "feedback": "Failed to parse evaluation, defaulting.",
                "difficulty_adjustment": "MAINTAIN",
                "followup_question": "Tell me more about your experience."
            }
        
    def generate_final_verdict(self, transcript_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        system_prompt = (
            "Summarize the complete interview transcript. Evaluate technical skill indexes, behavioral indicators, and proctor anomalies. "
            "Return JSON matching structure: "
            '{"overall_score": 8.0, "technical_skills_matrix": {}, "behavioral_skills_matrix": {}, "summary_verdict": "STRONG_HIRE"}'
        )
        user_prompt = f"Transcript logs: {json.dumps(transcript_history)}"
        raw_res = self._call_llm(system_prompt, user_prompt)
        try:
            return json.loads(raw_res)
        except Exception:
            return {
                "overall_score": 5.0,
                "technical_skills_matrix": {},
                "behavioral_skills_matrix": {},
                "summary_verdict": "HIRE"
            }
