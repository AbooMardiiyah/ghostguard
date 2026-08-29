"""Payroll Auditor Agent — runs 5-layer engine, produces Exceptions Pack."""

import csv
from decimal import Decimal
from pathlib import Path

from app.agents.base import BaseAgent
from app.engine.rule_engine import score_employee, compute_verdict
from app.models.schemas import Anomaly, Verdict


SEED_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "seed"


def _load_csv(filename: str) -> list[dict]:
    path = SEED_DIR / filename
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class AuditorAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Auditor", agent_id="auditor")

    async def process(self, input_data: dict) -> dict:
        """Run 5-layer scan on all employees in a payroll run.

        input_data: {
            "employees": list[dict],
            "run_id": str,
        }
        """
        employees = input_data["employees"]
        run_id = input_data.get("run_id", "RUN-UNKNOWN")

        # Load reference data for cross-checks
        hr_register = _load_csv("hr_register.csv")
        hr_register_ids = {r["employee_id"] for r in hr_register}

        leavers = _load_csv("leavers.csv")
        leaver_ids = {r["employee_id"] for r in leavers}

        attendance = _load_csv("attendance_aug2026.csv")

        anomalies = []
        for emp in employees:
            findings = score_employee(
                emp, employees, attendance, hr_register_ids, leaver_ids
            )

            if not findings:
                continue

            total_score, verdict = compute_verdict(findings)

            if verdict == Verdict.CLEAR:
                continue

            anomaly_id = f"ANM-{run_id}-{emp['employee_id']}"
            salary = Decimal(str(emp.get("monthly_salary", 0)))

            # Generate explanation
            explanation = await self._generate_explanation(emp, findings)

            anomaly = Anomaly(
                anomaly_id=anomaly_id,
                employee_id=emp["employee_id"],
                employee_name=emp.get("full_name", "Unknown"),
                run_id=run_id,
                findings=findings,
                total_score=total_score,
                verdict=verdict,
                monthly_exposure=salary,
                explanation=explanation,
                status="open",
            )
            anomalies.append(anomaly)

        return {
            "run_id": run_id,
            "anomalies_found": len(anomalies),
            "anomalies": [a.model_dump(mode="json") for a in anomalies],
        }

    async def _generate_explanation(self, employee: dict, findings: list) -> str:
        """Generate plain-English explanation using LLM or fallback."""
        name = employee.get("full_name", "this employee")
        finding_descs = "; ".join(f.description for f in findings)
        prompt = (
            f"Given these findings for employee {name}, write a 2-sentence "
            f"plain-English explanation of why this employee was flagged. "
            f"Do not accuse — use the word 'anomaly', not 'fraud'. Cite specific evidence.\n\n"
            f"Findings: {finding_descs}"
        )
        try:
            return await self.call_llm(prompt)
        except Exception:
            return f"Anomalies detected: {finding_descs}"

    def get_status_dict(self) -> dict:
        d = super().get_status_dict()
        d["summary_metric"] = f"{self.metrics.tasks_completed} scans"
        return d
