"""GhostGuard FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models.database import get_db, close_db
from app.seed import seed_database
from app.api import (
    dashboard,
    employees,
    payroll,
    verify,
    defense,
    redteam,
    audit,
    integrations,
    approvals,
    scheduler,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: init DB + load seed data
    db = await get_db()
    await seed_database(db)
    yield
    # Shutdown
    await close_db()


app = FastAPI(
    title="GhostGuard",
    description="Agentic payroll-integrity layer — ghost worker detection, identity verification, tamper-proof audit",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(dashboard.router, prefix="/api", tags=["Dashboard"])
app.include_router(employees.router, prefix="/api", tags=["Employees"])
app.include_router(payroll.router, prefix="/api", tags=["Payroll"])
app.include_router(verify.router, prefix="/api", tags=["Verify"])
app.include_router(defense.router, prefix="/api", tags=["Defense"])
app.include_router(redteam.router, prefix="/api", tags=["Red Team"])
app.include_router(audit.router, prefix="/api", tags=["Audit"])
app.include_router(integrations.router, prefix="/api", tags=["Integrations"])
app.include_router(approvals.router, prefix="/api", tags=["Approvals"])
app.include_router(scheduler.router, prefix="/api", tags=["Scheduler"])


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "ghostguard"}
