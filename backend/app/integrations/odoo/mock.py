"""MockOdooConnector — simulated Odoo responses for offline demo."""


class MockOdooConnector:
    def __init__(self):
        self.connected = False

    async def authenticate(self) -> int:
        self.connected = True
        return 1  # fake uid

    async def poll_expenses(self, since: str) -> list[dict]:
        return [
            {
                "id": 1,
                "name": "Client Dinner - Lagos",
                "total_amount": 48500.0,
                "employee_id": [40, "Kola Adeyemi"],
                "date": "2026-08-15",
                "state": "reported",
                "receipt_attached": True,
            },
            {
                "id": 2,
                "name": "Office Supplies",
                "total_amount": 12000.0,
                "employee_id": [5, "Chinedu Okafor"],
                "date": "2026-08-18",
                "state": "approved",
                "receipt_attached": True,
            },
        ]

    async def write_chatter(
        self, expense_id: int, verdict: str, reasons: list[str]
    ) -> bool:
        # In mock mode, just log and return success
        return True
