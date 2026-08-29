"""Tests for MockAdapter — verifies canned responses match expected data."""

import pytest
from app.integrations.dojah.mock import MockAdapter


@pytest.fixture
def adapter():
    return MockAdapter()


@pytest.mark.asyncio
async def test_nin_known_value(adapter):
    """NIN 70123456789 should return JOHN DOE SMITH (for ghost onboarding demo)."""
    result = await adapter.verify_nin("70123456789")
    entity = result["entity"]
    assert entity["first_name"] == "JOHN"
    assert entity["last_name"] == "SMITH"


@pytest.mark.asyncio
async def test_bvn_known_value(adapter):
    """BVN 22222222222 should return CHINEDU OKAFOR."""
    result = await adapter.verify_bvn("22222222222")
    entity = result["entity"]
    assert entity["first_name"] == "CHINEDU"
    assert entity["last_name"] == "OKAFOR"


@pytest.mark.asyncio
async def test_account_known_value(adapter):
    """Account 3046507407 at bank 011 should return CHINEDU OKAFOR."""
    result = await adapter.resolve_account("3046507407", "011")
    entity = result["entity"]
    assert "CHINEDU OKAFOR" in entity["account_name"]


@pytest.mark.asyncio
async def test_unknown_nin_returns_generic(adapter):
    """Unknown NIN should return a generic valid response."""
    result = await adapter.verify_nin("99999999999")
    assert "entity" in result
    assert result["entity"]["first_name"] == "VERIFIED"


@pytest.mark.asyncio
async def test_unknown_bvn_returns_generic(adapter):
    result = await adapter.verify_bvn("99999999999")
    assert result["entity"]["first_name"] == "VERIFIED"
