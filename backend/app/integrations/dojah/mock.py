"""MockAdapter — offline demo fallback with canned Dojah sandbox responses.

For resolve_account, we load the seed employee CSV so that every seeded
employee's bank account resolves to their actual name — only genuine
mismatches (like the ghost worker's shared account) show as red.
"""

import csv
from pathlib import Path

from app.integrations.dojah.provider import VerificationProvider


# Canned responses matching Dojah sandbox test values
MOCK_NIN_RESPONSES = {
    "70123456789": {
        "entity": {
            "first_name": "JOHN",
            "middle_name": "DOE",
            "last_name": "SMITH",
            "date_of_birth": "1990-01-15",
            "gender": "Male",
            "phone": "08012345678",
        }
    },
}

MOCK_BVN_RESPONSES = {
    "22222222222": {
        "entity": {
            "first_name": "CHINEDU",
            "middle_name": "",
            "last_name": "OKAFOR",
            "date_of_birth": "1985-06-20",
            "gender": "Male",
            "phone": "08033456789",
        }
    },
}


def _build_account_lookup() -> dict[tuple[str, str], str]:
    """Build account→name map from seed employees CSV.

    The bank owns the account name. For the shared account (3046507407/011),
    only the legitimate owner (Chinedu Okafor, EMP-005) is the registered
    holder — the ghost (Adaeze Okafor, EMP-036) using the same account will
    mismatch because the bank returns "CHINEDU OKAFOR", not "ADAEZE OKAFOR".
    """
    lookup: dict[tuple[str, str], str] = {}
    seed_path = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "data"
        / "seed"
        / "employees.csv"
    )
    if not seed_path.exists():
        return lookup
    with open(seed_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            acct = (row.get("bank_account") or "").strip()
            code = (row.get("bank_code") or "").strip()
            name = (row.get("full_name") or "").strip().upper()
            if acct and code and (acct, code) not in lookup:
                # First employee with this account is the registered holder
                lookup[(acct, code)] = name
    return lookup


_ACCOUNT_LOOKUP: dict[tuple[str, str], str] | None = None


def _get_account_lookup() -> dict[tuple[str, str], str]:
    global _ACCOUNT_LOOKUP
    if _ACCOUNT_LOOKUP is None:
        _ACCOUNT_LOOKUP = _build_account_lookup()
    return _ACCOUNT_LOOKUP


class MockAdapter(VerificationProvider):
    async def verify_nin(self, nin: str) -> dict:
        if nin in MOCK_NIN_RESPONSES:
            return MOCK_NIN_RESPONSES[nin]
        return {
            "entity": {
                "first_name": "VERIFIED",
                "middle_name": "",
                "last_name": "PERSON",
                "date_of_birth": "1990-01-01",
                "gender": "Male",
                "phone": "08000000000",
            }
        }

    async def verify_bvn(self, bvn: str) -> dict:
        if bvn in MOCK_BVN_RESPONSES:
            return MOCK_BVN_RESPONSES[bvn]
        return {
            "entity": {
                "first_name": "VERIFIED",
                "middle_name": "",
                "last_name": "PERSON",
                "date_of_birth": "1990-01-01",
                "gender": "Male",
                "phone": "08000000000",
            }
        }

    async def resolve_account(self, account: str, bank_code: str) -> dict:
        lookup = _get_account_lookup()
        key = (account, bank_code)
        account_name = lookup.get(key, "ACCOUNT HOLDER")
        return {
            "entity": {
                "account_name": account_name,
                "account_number": account,
                "bank_code": bank_code,
            }
        }
