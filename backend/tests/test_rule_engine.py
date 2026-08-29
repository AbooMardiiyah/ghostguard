"""Tests for the 5-layer deterministic rule engine."""

import csv
from pathlib import Path

import pytest

from app.engine.rule_engine import (
    score_employee,
    compute_verdict,
    check_identity,
    check_shared_attributes,
    check_existence,
    check_process,
    check_cross,
)
from app.models.schemas import Verdict

SEED_DIR = Path(__file__).resolve().parent.parent / "data" / "seed"


def load_employees() -> list[dict]:
    with open(SEED_DIR / "employees.csv", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_attendance() -> list[dict]:
    with open(SEED_DIR / "attendance_aug2026.csv", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_hr_register_ids() -> set[str]:
    with open(SEED_DIR / "hr_register.csv", newline="", encoding="utf-8") as f:
        return {r["employee_id"] for r in csv.DictReader(f)}


def load_leaver_ids() -> set[str]:
    with open(SEED_DIR / "leavers.csv", newline="", encoding="utf-8") as f:
        return {r["employee_id"] for r in csv.DictReader(f)}


@pytest.fixture
def employees():
    return load_employees()


@pytest.fixture
def attendance():
    return load_attendance()


@pytest.fixture
def hr_register_ids():
    return load_hr_register_ids()


@pytest.fixture
def leaver_ids():
    return load_leaver_ids()


class TestDeterminism:
    """Same input must always produce the same output."""

    def test_same_input_same_output(
        self, employees, attendance, hr_register_ids, leaver_ids
    ):
        emp = next(e for e in employees if e["employee_id"] == "EMP-036")
        r1 = score_employee(emp, employees, attendance, hr_register_ids, leaver_ids)
        r2 = score_employee(emp, employees, attendance, hr_register_ids, leaver_ids)

        assert len(r1) == len(r2)
        for f1, f2 in zip(r1, r2):
            assert f1.signal == f2.signal
            assert f1.points == f2.points


class TestGhostWorker:
    """EMP-036 Adaeze Okafor — ghost worker sharing bank account."""

    def test_ghost_detected(self, employees, attendance, hr_register_ids, leaver_ids):
        emp = next(e for e in employees if e["employee_id"] == "EMP-036")
        findings = score_employee(
            emp, employees, attendance, hr_register_ids, leaver_ids
        )
        total, verdict = compute_verdict(findings)

        assert verdict == Verdict.BLOCK
        signals = {f.signal for f in findings}
        assert "shared_bank_account" in signals
        assert "no_attendance_6m" in signals
        assert "unverified_identity" in signals


class TestTerminatedEmployee:
    """EMP-037 Musa Ibrahim — terminated but still on payroll."""

    def test_terminated_detected(
        self, employees, attendance, hr_register_ids, leaver_ids
    ):
        emp = next(e for e in employees if e["employee_id"] == "EMP-037")
        findings = score_employee(
            emp, employees, attendance, hr_register_ids, leaver_ids
        )
        total, verdict = compute_verdict(findings)

        assert verdict == Verdict.BLOCK
        signals = {f.signal for f in findings}
        assert "terminated_still_paid" in signals
        assert "not_in_hr_register" in signals


class TestSelfApproval:
    """EMP-039 Tunde Bakare — same user created and approved."""

    def test_self_approved_detected(
        self, employees, attendance, hr_register_ids, leaver_ids
    ):
        emp = next(e for e in employees if e["employee_id"] == "EMP-039")
        findings = score_employee(
            emp, employees, attendance, hr_register_ids, leaver_ids
        )
        total, verdict = compute_verdict(findings)

        assert verdict == Verdict.BLOCK
        signals = {f.signal for f in findings}
        assert "self_approved" in signals


class TestFalsePositive:
    """EMP-033/034 Yusuf & Fatima Bello — siblings, should FLAG not BLOCK."""

    def test_siblings_flagged_not_blocked(
        self, employees, attendance, hr_register_ids, leaver_ids
    ):
        for eid in ["EMP-033", "EMP-034"]:
            emp = next(e for e in employees if e["employee_id"] == eid)
            findings = score_employee(
                emp, employees, attendance, hr_register_ids, leaver_ids
            )
            total, verdict = compute_verdict(findings)

            assert verdict == Verdict.FLAG, f"{eid} should be FLAG, got {verdict}"
            signals = {f.signal for f in findings}
            assert "shared_address" in signals


class TestCleanEmployee:
    """Clean employees should have minimal or no findings."""

    def test_clean_employee(self, employees, attendance, hr_register_ids, leaver_ids):
        emp = next(e for e in employees if e["employee_id"] == "EMP-001")
        findings = score_employee(
            emp, employees, attendance, hr_register_ids, leaver_ids
        )
        total, verdict = compute_verdict(findings)

        # May have expired_verification but should still be CLEAR or at most low FLAG
        assert verdict in (Verdict.CLEAR, Verdict.FLAG)
        assert total < 70


class TestVerdictThresholds:
    """Verify verdict threshold logic."""

    def test_clear(self):
        from app.models.schemas import LayerFinding

        findings = [
            LayerFinding(
                layer="identity",
                signal="no_ncvs_credential",
                description="test",
                points=15,
            )
        ]
        total, verdict = compute_verdict(findings)
        assert total == 15
        assert verdict == Verdict.CLEAR

    def test_flag(self):
        from app.models.schemas import LayerFinding

        findings = [
            LayerFinding(
                layer="identity",
                signal="unverified_identity",
                description="test",
                points=30,
            )
        ]
        total, verdict = compute_verdict(findings)
        assert total == 30
        assert verdict == Verdict.FLAG

    def test_block(self):
        from app.models.schemas import LayerFinding

        findings = [
            LayerFinding(
                layer="identity",
                signal="unverified_identity",
                description="test",
                points=30,
            ),
            LayerFinding(
                layer="shared_attributes",
                signal="shared_bank_account",
                description="test",
                points=40,
            ),
        ]
        total, verdict = compute_verdict(findings)
        assert total == 70
        assert verdict == Verdict.BLOCK

    def test_hard_block_overrides(self):
        from app.models.schemas import LayerFinding

        findings = [
            LayerFinding(
                layer="cross_check",
                signal="terminated_still_paid",
                description="test",
                points=50,
            )
        ]
        total, verdict = compute_verdict(findings)
        assert verdict == Verdict.BLOCK  # Hard block even though score < 70

    def test_score_capped_at_100(self):
        from app.models.schemas import LayerFinding

        findings = [
            LayerFinding(
                layer="identity",
                signal="unverified_identity",
                description="t",
                points=30,
            ),
            LayerFinding(
                layer="shared_attributes",
                signal="shared_bank_account",
                description="t",
                points=40,
            ),
            LayerFinding(
                layer="existence", signal="no_attendance_6m", description="t", points=35
            ),
            LayerFinding(
                layer="process", signal="self_approved", description="t", points=50
            ),
        ]
        total, verdict = compute_verdict(findings)
        assert total == 100  # Capped
