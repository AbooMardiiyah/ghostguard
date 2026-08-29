"""Guardian Agent — prompt injection, impersonation, and urgency-pressure screening.

Deterministic pattern matching for security decisions. LLM only for explanation.
"""

import re
from app.agents.base import BaseAgent

# Injection patterns — SQL, prompt injection, command injection
INJECTION_PATTERNS = [
    (
        r"(?i)(ignore|disregard|forget)\s+(all\s+)?(previous|prior|above)\s+(instructions|rules|prompts)",
        "prompt_injection",
        "Attempt to override system instructions",
    ),
    (
        r"(?i)(you\s+are|act\s+as|pretend\s+to\s+be|roleplay\s+as)\s+",
        "role_hijack",
        "Attempt to change AI role/persona",
    ),
    (
        r"(?i)(system\s*:?\s*|<\|system\|>|<system>)",
        "system_prompt_inject",
        "Attempt to inject system-level prompt",
    ),
    (
        r"(?i)(DROP\s+TABLE|DELETE\s+FROM|UPDATE\s+\w+\s+SET|INSERT\s+INTO|;\s*--)",
        "sql_injection",
        "SQL injection attempt detected",
    ),
    (
        r"(?i)(\$\{|\{\{|<script|javascript:|onerror=|onload=)",
        "code_injection",
        "Code/template injection attempt",
    ),
    (
        r"(?i)(base64_decode|eval\(|exec\(|os\.system|subprocess|__import__)",
        "code_execution",
        "Code execution attempt detected",
    ),
]

# Impersonation patterns
IMPERSONATION_PATTERNS = [
    (
        r"(?i)(this\s+is\s+(the\s+)?(CEO|MD|director|chairman|CFO|CTO))",
        "executive_impersonation",
        "Claimed executive identity without verification",
    ),
    (
        r"(?i)(on\s+behalf\s+of|authorized\s+by|instructed\s+by)\s+(the\s+)?(CEO|MD|director|board)",
        "authority_claim",
        "Unverified authority claim",
    ),
    (
        r"(?i)(i\s+am\s+(the|your)\s+(boss|manager|supervisor|director|CEO))",
        "direct_impersonation",
        "Direct impersonation of authority figure",
    ),
]

# Urgency/pressure patterns
URGENCY_PATTERNS = [
    (
        r"(?i)(do\s+it\s+now|immediately|right\s+now|urgent|asap|emergency|critical)",
        "urgency_pressure",
        "Urgency pressure tactics detected",
    ),
    (
        r"(?i)(don'?t\s+tell\s+anyone|keep\s+this\s+(quiet|secret|between\s+us)|confidential)",
        "secrecy_pressure",
        "Secrecy pressure tactics detected",
    ),
    (
        r"(?i)(skip\s+(the\s+)?(approval|verification|review|check)|bypass|override)",
        "bypass_attempt",
        "Attempt to bypass controls",
    ),
    (
        r"(?i)(or\s+else|consequences|fired|terminated|your\s+job)",
        "threat_pressure",
        "Threat/coercion language detected",
    ),
]


class GuardianAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Guardian", agent_id="guardian")

    async def process(self, input_data: dict) -> dict:
        """Screen text content for injection, impersonation, and urgency attacks.

        input_data: {"text": str, "context": str (optional)}
        """
        text = input_data.get("text", "")
        context = input_data.get("context", "general")
        threats = []

        # Run all pattern checks
        for patterns, category in [
            (INJECTION_PATTERNS, "injection"),
            (IMPERSONATION_PATTERNS, "impersonation"),
            (URGENCY_PATTERNS, "urgency"),
        ]:
            for pattern, signal, desc in patterns:
                if re.search(pattern, text):
                    threats.append(
                        {
                            "category": category,
                            "signal": signal,
                            "description": desc,
                            "pattern_matched": True,
                        }
                    )

        safe = len(threats) == 0
        verdict = "SAFE" if safe else "BLOCKED"
        recommendation = ""

        explanation = ""
        if not safe:
            threat_types = set(t["category"] for t in threats)
            if "injection" in threat_types:
                recommendation = (
                    "Content contains injection attempts. Reject and log for review."
                )
            elif "impersonation" in threat_types:
                recommendation = "Unverified identity claim. Demand verified sign-off before proceeding."
            elif "urgency" in threat_types:
                recommendation = (
                    "Pressure tactics detected. Follow standard approval process."
                )

            # LLM explanation is supplementary — recommendation stays deterministic
            try:
                threat_descs = "; ".join(t["description"] for t in threats)
                prompt = (
                    f"A message was flagged by our security system. Threats found: {threat_descs}. "
                    f"Write a 1-sentence explanation of why this was blocked. Be professional."
                )
                explanation = await self.call_llm(prompt)
            except Exception:
                explanation = "; ".join(t["description"] for t in threats)

        return {
            "safe": safe,
            "threats": threats,
            "verdict": verdict,
            "recommendation": recommendation,
            "explanation": explanation,
            "context": context,
        }

    def get_status_dict(self) -> dict:
        d = super().get_status_dict()
        d["state"] = "armed"
        d["summary_metric"] = f"{self.metrics.tasks_completed} screened"
        return d
