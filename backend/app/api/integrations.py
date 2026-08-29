"""Integrations API — CSV upload, Odoo connect, sample CSV download."""

from pathlib import Path

from fastapi import APIRouter, UploadFile, File
from fastapi.responses import FileResponse

from app.config import settings
from app.models.database import get_db
from app.models.schemas import AuditVerdict
from app.integrations.csv_importer import import_csv
from app.integrations.odoo.mock import MockOdooConnector
from app.integrations.odoo.connector import OdooConnector
from app.security.file_scanner import scan_upload
from app.audit.audit_store import append_event
from app.api.payroll import scan_payroll
from app.seed import seed_database

router = APIRouter()

# Use real Odoo connector when credentials are configured, otherwise mock
if settings.odoo_url and settings.odoo_db:
    _odoo = OdooConnector(
        url=settings.odoo_url,
        db=settings.odoo_db,
        username=settings.odoo_username,
        password=settings.odoo_password,
    )
    _odoo_provider = "live"
else:
    _odoo = MockOdooConnector()
    _odoo_provider = "mock"


@router.post("/integrations/csv/upload")
async def upload_csv(file: UploadFile = File(...)):
    db = await get_db()
    content = await file.read()

    # Security scan
    scan_result = scan_upload(file.filename, content)
    if not scan_result["safe"]:
        await append_event(
            db,
            "security",
            "File Scanner",
            f"Blocked upload: {file.filename} — {', '.join(scan_result['threats'])}",
            verdict=AuditVerdict.BLOCKED,
            payload=scan_result,
        )
        return {
            "success": False,
            "error": "File blocked by security scan",
            "threats": scan_result["threats"],
        }

    # Import
    result = await import_csv(db, content, file.filename)

    await append_event(
        db,
        "import",
        "CSV Importer",
        f"Imported {file.filename}: {result.get('rows', 0)} rows ({result.get('category', 'unknown')})",
        verdict=AuditVerdict.INFO,
        payload=result,
    )

    # Auto-trigger scan when payroll register is uploaded
    if result.get("success") and result.get("category") == "payroll_register":
        scan_result = await scan_payroll()
        result["scan_triggered"] = True
        result["scan_result"] = scan_result

    return result


@router.post("/integrations/odoo/connect")
async def connect_odoo():
    """Connect to Odoo and sync employee data into GhostGuard."""
    try:
        uid = await _odoo.authenticate()

        # Re-seed data if tables are empty (e.g. after disconnect)
        db = await get_db()
        await seed_database(db)

        cursor = await db.execute("SELECT COUNT(*) FROM employees")
        (emp_count,) = await cursor.fetchone()

        await append_event(
            db,
            "integration",
            "Odoo Connector",
            f"Connected to Odoo — {emp_count} employees synced",
            verdict=AuditVerdict.INFO,
            payload={"uid": uid, "employees": emp_count},
        )

        return {
            "connected": True,
            "provider": _odoo_provider,
            "uid": uid,
            "message": f"Connected — {emp_count} employees synced",
            "employee_count": emp_count,
        }
    except Exception as e:
        return {"connected": False, "provider": _odoo_provider, "error": str(e)}


@router.post("/integrations/odoo/disconnect")
async def disconnect_odoo():
    """Disconnect Odoo — clears synced employee and payroll data."""
    db = await get_db()

    await db.execute("DELETE FROM anomalies")
    await db.execute("DELETE FROM payroll_entries")
    await db.execute("DELETE FROM payroll_runs")
    await db.execute("DELETE FROM employees")
    await db.execute("DELETE FROM leavers")
    await db.commit()

    await append_event(
        db,
        "integration",
        "Odoo Connector",
        "Disconnected from Odoo — synced data cleared",
        verdict=AuditVerdict.INFO,
    )

    return {"disconnected": True, "message": "Odoo disconnected — data cleared"}


@router.post("/integrations/odoo/seed")
async def seed_odoo():
    """Seed Odoo with sample employees and departments for demo."""
    if _odoo_provider != "live":
        return {
            "success": False,
            "error": "Odoo is in mock mode — no live instance to seed",
        }

    db = await get_db()
    try:
        # Check if already seeded
        existing = await _odoo.poll_employees()
        if len(existing) >= 5:
            return {
                "success": True,
                "message": f"Odoo already has {len(existing)} employees",
                "skipped": True,
            }

        # Create departments
        depts = {}
        for dept_name in ["Finance", "Operations", "Human Resources", "IT", "Sales"]:
            depts[dept_name] = await _odoo.create_department(dept_name)

        # Create sample employees (subset of our seed data)
        sample_employees = [
            {
                "name": "Amina Yusuf",
                "job_title": "Finance Manager",
                "dept": "Finance",
                "work_email": "amina.yusuf@sterling.ng",
                "work_phone": "08012345001",
            },
            {
                "name": "Chinedu Okafor",
                "job_title": "Operations Lead",
                "dept": "Operations",
                "work_email": "chinedu.okafor@sterling.ng",
                "work_phone": "08012345005",
            },
            {
                "name": "Fatima Bello",
                "job_title": "HR Officer",
                "dept": "Human Resources",
                "work_email": "fatima.bello@sterling.ng",
                "work_phone": "08012345034",
            },
            {
                "name": "Tunde Bakare",
                "job_title": "IT Administrator",
                "dept": "IT",
                "work_email": "tunde.bakare@sterling.ng",
                "work_phone": "08012345039",
            },
            {
                "name": "Kola Adeyemi",
                "job_title": "Sales Executive",
                "dept": "Sales",
                "work_email": "kola.adeyemi@sterling.ng",
                "work_phone": "08012345040",
            },
            {
                "name": "Adaeze Okafor",
                "job_title": "Data Entry Clerk",
                "dept": "Operations",
                "work_email": "adaeze.okafor@sterling.ng",
                "work_phone": "08012345036",
            },
            {
                "name": "Yusuf Bello",
                "job_title": "Logistics Officer",
                "dept": "Operations",
                "work_email": "yusuf.bello@sterling.ng",
                "work_phone": "08012345033",
            },
            {
                "name": "Ngozi Eze",
                "job_title": "Accountant",
                "dept": "Finance",
                "work_email": "ngozi.eze@sterling.ng",
                "work_phone": "08012345010",
            },
            {
                "name": "Ibrahim Musa",
                "job_title": "Operations Analyst",
                "dept": "Operations",
                "work_email": "ibrahim.musa@sterling.ng",
                "work_phone": "08012345037",
            },
            {
                "name": "Jane Smith",
                "job_title": "Contract Staff",
                "dept": "Operations",
                "work_email": "jane.smith@sterling.ng",
                "work_phone": "08012345038",
            },
        ]

        created = 0
        for emp in sample_employees:
            await _odoo.create_employee(
                name=emp["name"],
                job_title=emp["job_title"],
                department_id=depts.get(emp["dept"]),
                work_email=emp["work_email"],
                work_phone=emp["work_phone"],
            )
            created += 1

        await append_event(
            db,
            "integration",
            "Odoo Connector",
            f"Seeded Odoo with {created} employees and {len(depts)} departments",
            verdict=AuditVerdict.INFO,
            payload={"employees_created": created, "departments_created": len(depts)},
        )

        return {
            "success": True,
            "employees_created": created,
            "departments_created": len(depts),
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/integrations/odoo/poll")
async def poll_odoo_data():
    """Poll Odoo for employees and attendance."""
    db = await get_db()

    result = {"provider": _odoo_provider}

    try:
        if hasattr(_odoo, "poll_employees"):
            employees = await _odoo.poll_employees()
            result["employees"] = employees
            result["employee_count"] = len(employees)
        else:
            expenses = await _odoo.poll_expenses("2026-08-01")
            result["expenses"] = expenses
            result["expense_count"] = len(expenses)
    except Exception as e:
        result["error"] = str(e)

    try:
        if hasattr(_odoo, "poll_attendance"):
            attendance = await _odoo.poll_attendance("2026-08-01")
            result["attendance"] = attendance
            result["attendance_count"] = len(attendance)
    except Exception:
        pass

    await append_event(
        db,
        "integration",
        "Odoo Connector",
        f"Polled Odoo ({_odoo_provider}): {result.get('employee_count', 0)} employees, {result.get('attendance_count', 0)} attendance records",
        verdict=AuditVerdict.INFO,
        payload=result,
    )

    return result


SEED_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "seed"


@router.get("/integrations/csv/sample")
async def download_sample_csv():
    """Download the sample payroll register CSV for demo uploads."""
    path = SEED_DIR / "employees.csv"
    if not path.exists():
        return {"error": "Sample CSV not found"}
    return FileResponse(
        path,
        media_type="text/csv",
        filename="sample-payroll-register.csv",
    )
