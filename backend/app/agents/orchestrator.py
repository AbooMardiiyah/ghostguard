"""Orchestrator — singleton registry of all agents."""

from app.agents.verifier import VerifierAgent
from app.agents.auditor import AuditorAgent
from app.agents.guardian import GuardianAgent
from app.agents.redteam import RedTeamAgent
from app.integrations.dojah.provider import get_provider

_verifier: VerifierAgent | None = None
_auditor: AuditorAgent | None = None
_guardian: GuardianAgent | None = None
_redteam: RedTeamAgent | None = None


def get_verifier() -> VerifierAgent:
    global _verifier
    if _verifier is None:
        _verifier = VerifierAgent(provider=get_provider())
    return _verifier


def get_auditor() -> AuditorAgent:
    global _auditor
    if _auditor is None:
        _auditor = AuditorAgent()
    return _auditor


def get_guardian() -> GuardianAgent:
    global _guardian
    if _guardian is None:
        _guardian = GuardianAgent()
    return _guardian


def get_redteam() -> RedTeamAgent:
    global _redteam
    if _redteam is None:
        _redteam = RedTeamAgent(guardian=get_guardian())
    return _redteam


def get_all_agent_statuses() -> list[dict]:
    return [
        get_verifier().get_status_dict(),
        get_auditor().get_status_dict(),
        get_guardian().get_status_dict(),
        get_redteam().get_status_dict(),
    ]
