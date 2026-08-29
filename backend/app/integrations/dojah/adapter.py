"""DojahAdapter — live sandbox API calls for identity verification."""

import httpx
from app.config import settings
from app.integrations.dojah.provider import VerificationProvider


class DojahAdapter(VerificationProvider):
    def __init__(self):
        self.base_url = settings.dojah_base_url.rstrip("/")
        self.headers = {
            "AppId": settings.dojah_app_id,
            "Authorization": settings.dojah_secret_key,
            "Content-Type": "application/json",
        }

    async def _get(self, endpoint: str, params: dict) -> dict:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                params=params,
            )
            resp.raise_for_status()
            return resp.json()

    async def verify_nin(self, nin: str) -> dict:
        return await self._get("/api/v1/kyc/nin", {"nin": nin})

    async def verify_bvn(self, bvn: str) -> dict:
        return await self._get("/api/v1/kyc/bvn", {"bvn": bvn})

    async def resolve_account(self, account: str, bank_code: str) -> dict:
        return await self._get(
            "/api/v1/kyc/nuban",
            {
                "account_number": account,
                "bank_code": bank_code,
            },
        )
