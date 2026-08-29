"""Tests for hash-chained audit trail integrity."""

import pytest
import pytest_asyncio
import aiosqlite

from app.audit.audit_store import append_event, verify_chain, get_all_events
from app.models.schemas import AuditVerdict


@pytest_asyncio.fixture
async def db(tmp_path):
    """Create a fresh in-memory-like SQLite DB with schema."""
    db_path = tmp_path / "test.db"
    db = await aiosqlite.connect(str(db_path))
    db.row_factory = aiosqlite.Row
    await db.executescript("""
        CREATE TABLE audit_trail (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT UNIQUE NOT NULL,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            actor TEXT NOT NULL,
            action TEXT NOT NULL,
            target TEXT,
            verdict TEXT,
            detail TEXT,
            payload_json TEXT,
            evidence_hash TEXT NOT NULL,
            chain_hash TEXT NOT NULL
        );
        CREATE TRIGGER audit_no_update BEFORE UPDATE ON audit_trail
        BEGIN SELECT RAISE(ABORT, 'Audit trail is append-only'); END;
        CREATE TRIGGER audit_no_delete BEFORE DELETE ON audit_trail
        BEGIN SELECT RAISE(ABORT, 'Audit trail is append-only'); END;
    """)
    yield db
    await db.close()


@pytest.mark.asyncio
async def test_chain_valid_after_multiple_events(db):
    """Chain should be valid after inserting multiple events."""
    for i in range(5):
        await append_event(
            db, "test", "tester", f"Action {i}", verdict=AuditVerdict.INFO
        )

    valid, count, latest = await verify_chain(db)
    assert valid is True
    assert count == 5
    assert len(latest) == 64  # SHA-256 hex


@pytest.mark.asyncio
async def test_empty_chain_is_valid(db):
    """Empty chain should verify as valid."""
    valid, count, latest = await verify_chain(db)
    assert valid is True
    assert count == 0


@pytest.mark.asyncio
async def test_events_are_append_only(db):
    """Cannot update or delete audit events."""
    event = await append_event(db, "test", "tester", "Original action")

    with pytest.raises(Exception, match="append-only"):
        await db.execute(
            "UPDATE audit_trail SET action = 'tampered' WHERE event_id = ?",
            (event.event_id,),
        )

    with pytest.raises(Exception, match="append-only"):
        await db.execute(
            "DELETE FROM audit_trail WHERE event_id = ?",
            (event.event_id,),
        )


@pytest.mark.asyncio
async def test_chain_links_events(db):
    """Each event's chain_hash depends on the previous one."""
    e1 = await append_event(db, "test", "tester", "First")
    e2 = await append_event(db, "test", "tester", "Second")

    assert e1.chain_hash != e2.chain_hash
    assert len(e1.chain_hash) == 64
    assert len(e2.chain_hash) == 64


@pytest.mark.asyncio
async def test_events_returned_newest_first(db):
    """get_all_events returns newest first."""
    await append_event(db, "test", "tester", "First")
    await append_event(db, "test", "tester", "Second")
    await append_event(db, "test", "tester", "Third")

    events = await get_all_events(db)
    assert events[0].action == "Third"
    assert events[2].action == "First"
