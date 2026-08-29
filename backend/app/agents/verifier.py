"""Verifier Agent — identity verification via Dojah or MockAdapter."""

from app.agents.base import BaseAgent
from app.integrations.dojah.provider import VerificationProvider
from app.models.schemas import LayerFinding


class VerifierAgent(BaseAgent):
    def __init__(self, provider: VerificationProvider):
        super().__init__(name="Verifier", agent_id="verifier")
        self.provider = provider

    async def process(self, input_data: dict) -> dict:
        """Verify an employee's identity against NIN/BVN databases.

        input_data: employee dict with nin, bvn, full_name, bank_account, bank_code
        """
        employee = input_data
        eid = employee.get("employee_id", "unknown")
        name = employee.get("full_name", "")
        findings = []
        citations = {}

        # NIN verification
        nin = employee.get("nin")
        if nin:
            nin_result = await self.provider.verify_nin(nin)
            citations["nin"] = nin_result
            if nin_result.get("entity"):
                api_name = self._extract_name(nin_result["entity"])
                if not self._names_match(name, api_name):
                    findings.append(
                        LayerFinding(
                            layer="identity",
                            signal="nin_name_mismatch",
                            description=f"NIN verifies to '{api_name}', not '{name}'",
                            evidence={
                                "nin_last4": nin[-4:],
                                "api_name": api_name,
                                "record_name": name,
                            },
                            points=50,
                            source="dojah_api",
                        )
                    )

        # BVN verification
        bvn = employee.get("bvn")
        if bvn:
            bvn_result = await self.provider.verify_bvn(bvn)
            citations["bvn"] = bvn_result
            if bvn_result.get("entity"):
                api_name = self._extract_name(bvn_result["entity"])
                if not self._names_match(name, api_name):
                    findings.append(
                        LayerFinding(
                            layer="identity",
                            signal="bvn_name_mismatch",
                            description=f"BVN verifies to '{api_name}', not '{name}'",
                            evidence={
                                "bvn_last4": bvn[-4:],
                                "api_name": api_name,
                                "record_name": name,
                            },
                            points=50,
                            source="dojah_api",
                        )
                    )

        # Bank account resolution
        bank_account = employee.get("bank_account")
        bank_code = employee.get("bank_code")
        if bank_account and bank_code:
            acct_result = await self.provider.resolve_account(bank_account, bank_code)
            citations["bank"] = acct_result

        verified = len(findings) == 0

        return {
            "employee_id": eid,
            "verified": verified,
            "findings": [f.model_dump() for f in findings],
            "citations": citations,
        }

    def _extract_name(self, entity: dict) -> str:
        """Extract full name from Dojah entity response."""
        first = entity.get("first_name", "")
        last = entity.get("last_name", "")
        middle = entity.get("middle_name", "")
        parts = [p for p in [first, middle, last] if p]
        return " ".join(parts)

    def _names_match(self, name_a: str, name_b: str) -> bool:
        """Fuzzy name match — check if key name parts overlap."""
        parts_a = set(name_a.strip().lower().split())
        parts_b = set(name_b.strip().lower().split())
        # At least 2 matching name parts, or one is a subset of the other
        overlap = parts_a & parts_b
        return len(overlap) >= 2 or parts_a <= parts_b or parts_b <= parts_a

    def get_status_dict(self) -> dict:
        d = super().get_status_dict()
        d["summary_metric"] = f"{self.metrics.tasks_completed} verified"
        return d
