"""VerificationProvider ABC and factory."""

from abc import ABC, abstractmethod
from app.config import settings


class VerificationProvider(ABC):
    @abstractmethod
    async def verify_nin(self, nin: str) -> dict: ...

    @abstractmethod
    async def verify_bvn(self, bvn: str) -> dict: ...

    @abstractmethod
    async def resolve_account(self, account: str, bank_code: str) -> dict: ...


def get_provider() -> VerificationProvider:
    if settings.identity_provider == "dojah":
        from app.integrations.dojah.adapter import DojahAdapter

        return DojahAdapter()
    else:
        from app.integrations.dojah.mock import MockAdapter

        return MockAdapter()
