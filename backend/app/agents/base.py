"""BaseAgent ABC — state machine, metrics, LLM wrapper."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, field

from app.config import settings


class ProcessingState(str, Enum):
    IDLE = "idle"
    PROCESSING = "processing"
    VALIDATING = "validating"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class AgentMetrics:
    tasks_completed: int = 0
    tasks_failed: int = 0
    last_run: datetime | None = None


class BaseAgent(ABC):
    def __init__(self, name: str, agent_id: str):
        self.name = name
        self.agent_id = agent_id
        self.state = ProcessingState.IDLE
        self.metrics = AgentMetrics()

    def transition(self, new_state: ProcessingState) -> None:
        self.state = new_state

    @abstractmethod
    async def process(self, input_data: dict) -> dict: ...

    async def run(self, input_data: dict) -> dict:
        self.transition(ProcessingState.PROCESSING)
        try:
            result = await self.process(input_data)
            self.transition(ProcessingState.COMPLETE)
            self.metrics.tasks_completed += 1
            self.metrics.last_run = datetime.now(timezone.utc)
            return result
        except Exception:
            self.transition(ProcessingState.ERROR)
            self.metrics.tasks_failed += 1
            self.metrics.last_run = datetime.now(timezone.utc)
            raise
        finally:
            self.transition(ProcessingState.IDLE)

    async def call_llm(self, prompt: str) -> str:
        """LLM wrapper with fallback chain: configured provider → mock."""
        provider = settings.llm_provider

        # Try configured provider first
        try:
            if provider == "together" and settings.together_api_key:
                return await self._call_together(prompt)
            elif provider == "gemini" and settings.gemini_api_key:
                return await self._call_gemini(prompt)
            elif provider == "openai" and settings.openai_api_key:
                return await self._call_openai(prompt)
        except Exception:
            # Fall through to fallback chain
            pass

        # Fallback chain: Gemini → Together → mock
        if provider != "gemini" and settings.gemini_api_key:
            try:
                return await self._call_gemini(prompt)
            except Exception:
                pass
        if provider != "together" and settings.together_api_key:
            try:
                return await self._call_together(prompt)
            except Exception:
                pass

        # Final fallback
        return self._mock_llm(prompt)

    async def _call_together(self, prompt: str) -> str:
        import httpx

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.together.xyz/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.together_api_key}"},
                json={
                    "model": settings.together_model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a concise payroll fraud analyst. Write short, professional explanations. Never accuse — use 'anomaly', not 'fraud'. Cite specific evidence.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 150,
                    "temperature": 0.3,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    async def _call_gemini(self, prompt: str) -> str:
        import httpx

        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                url,
                params={"key": settings.gemini_api_key},
                json={"contents": [{"parts": [{"text": prompt}]}]},
            )
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    async def _call_openai(self, prompt: str) -> str:
        import httpx

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 200,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    def _mock_llm(self, prompt: str) -> str:
        """Extract finding descriptions from the prompt as a fallback explanation."""
        if "Findings:" in prompt:
            findings_text = prompt.split("Findings:", 1)[1].strip()
            return f"Anomalies detected: {findings_text}"
        if "Threats found:" in prompt:
            threats_text = prompt.split("Threats found:", 1)[1].strip().rstrip(".")
            return f"Blocked: {threats_text}"
        return (
            "Analysis completed. See detailed findings for specific anomalies detected."
        )

    def get_status_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "state": self.state.value
            if self.state == ProcessingState.IDLE
            else "active",
            "tasks_completed": self.metrics.tasks_completed,
            "tasks_failed": self.metrics.tasks_failed,
            "last_run": self.metrics.last_run.isoformat()
            if self.metrics.last_run
            else None,
            "summary_metric": None,
        }
