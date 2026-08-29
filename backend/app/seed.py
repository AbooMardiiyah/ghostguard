"""Seed loader — populates SQLite with CSV data on first startup."""

import csv
import logging
from pathlib import Path

import aiosqlite

logger = logging.getLogger(__name__)

# Resolve seed directory relative to backend/
SEED_DIR = Path(__file__).resolve().parent.parent / "data" / "seed"


async def seed_database(db: aiosqlite.Connection) -> None:
    """Load seed CSVs into the database if tables are empty.

    Inserts employees, payroll run + entries, and leavers.
    hr_register.csv and attendance_aug2026.csv are read at scan time
    directly from CSV by the rule engine.
    """
    # --- Guard: skip if already seeded ---
    cursor = await db.execute("SELECT COUNT(*) FROM employees")
    (count,) = await cursor.fetchone()
    if count > 0:
        logger.info("Database already seeded (%d employees). Skipping.", count)
        return

    logger.info("Seeding database from %s ...", SEED_DIR)

    # --- 1. Employees ---
    emp_path = SEED_DIR / "employees.csv"
    if not emp_path.exists():
        logger.warning("employees.csv not found at %s — skipping seed.", emp_path)
        return

    emp_count = 0
    with open(emp_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            await db.execute(
                """INSERT INTO employees (
                    employee_id, full_name, nin, bvn, bank_account, bank_code,
                    phone, address, next_of_kin, department, position,
                    date_hired, date_terminated, monthly_salary, status,
                    created_by, approved_by, ncvs_credential_number,
                    identity_verified, verification_date, verification_source
                ) VALUES (
                    :employee_id, :full_name, :nin, :bvn, :bank_account, :bank_code,
                    :phone, :address, :next_of_kin, :department, :position,
                    :date_hired, :date_terminated, :monthly_salary, :status,
                    :created_by, :approved_by, :ncvs_credential_number,
                    :identity_verified, :verification_date, :verification_source
                )""",
                {
                    "employee_id": row["employee_id"],
                    "full_name": row["full_name"],
                    "nin": row["nin"] or None,
                    "bvn": row["bvn"] or None,
                    "bank_account": row["bank_account"] or None,
                    "bank_code": row["bank_code"] or None,
                    "phone": row["phone"] or None,
                    "address": row["address"] or None,
                    "next_of_kin": row["next_of_kin"] or None,
                    "department": row["department"],
                    "position": row["position"],
                    "date_hired": row["date_hired"] or None,
                    "date_terminated": row["date_terminated"] or None,
                    "monthly_salary": float(row["monthly_salary"])
                    if row["monthly_salary"]
                    else 0,
                    "status": row["status"],
                    "created_by": row["created_by"],
                    "approved_by": row["approved_by"] or None,
                    "ncvs_credential_number": row["ncvs_credential_number"] or None,
                    "identity_verified": 1
                    if row["identity_verified"].lower() == "true"
                    else 0,
                    "verification_date": row["verification_date"] or None,
                    "verification_source": row["verification_source"] or None,
                },
            )
            emp_count += 1
    logger.info("Inserted %d employees.", emp_count)

    # --- 2. Payroll run ---
    await db.execute(
        """INSERT INTO payroll_runs (run_id, period, run_date, total_headcount, total_amount, status)
           VALUES (:run_id, :period, :run_date, :headcount, :total, :status)""",
        {
            "run_id": "RUN-2026-08",
            "period": "2026-08",
            "run_date": "2026-08-25",
            "headcount": emp_count,
            "total": 0,  # will be summed below
            "status": "draft",
        },
    )

    # --- 3. Payroll entries ---
    pay_path = SEED_DIR / "payroll_aug2026.csv"
    total_amount = 0.0
    pay_count = 0
    if pay_path.exists():
        with open(pay_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                amount = float(row["amount"])
                total_amount += amount
                await db.execute(
                    """INSERT INTO payroll_entries (
                        entry_id, run_id, employee_id, amount,
                        bank_account, bank_code, allowances, deductions
                    ) VALUES (
                        :entry_id, :run_id, :employee_id, :amount,
                        :bank_account, :bank_code, :allowances, :deductions
                    )""",
                    {
                        "entry_id": row["entry_id"],
                        "run_id": row["run_id"],
                        "employee_id": row["employee_id"],
                        "amount": amount,
                        "bank_account": row["bank_account"],
                        "bank_code": row["bank_code"],
                        "allowances": float(row["allowances"]),
                        "deductions": float(row["deductions"]),
                    },
                )
                pay_count += 1

        # Update total_amount on payroll run
        await db.execute(
            "UPDATE payroll_runs SET total_amount = :total WHERE run_id = :run_id",
            {"total": total_amount, "run_id": "RUN-2026-08"},
        )
        logger.info(
            "Inserted %d payroll entries (total: %.2f).", pay_count, total_amount
        )
    else:
        logger.warning("payroll_aug2026.csv not found — skipping payroll entries.")

    # --- 4. Leavers ---
    leavers_path = SEED_DIR / "leavers.csv"
    leaver_count = 0
    if leavers_path.exists():
        with open(leavers_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                await db.execute(
                    """INSERT INTO leavers (
                        employee_id, full_name, department, date_terminated, reason
                    ) VALUES (
                        :employee_id, :full_name, :department, :date_terminated, :reason
                    )""",
                    {
                        "employee_id": row["employee_id"],
                        "full_name": row["full_name"],
                        "department": row["department"],
                        "date_terminated": row["date_terminated"],
                        "reason": row["reason"],
                    },
                )
                leaver_count += 1
        logger.info("Inserted %d leavers.", leaver_count)
    else:
        logger.warning("leavers.csv not found — skipping leavers.")

    await db.commit()
    logger.info(
        "Seed complete: %d employees, %d payroll entries, %d leavers.",
        emp_count,
        pay_count,
        leaver_count,
    )
