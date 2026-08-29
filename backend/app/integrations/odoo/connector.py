"""OdooConnector — JSON-RPC interface to Odoo."""

import httpx


class OdooConnector:
    def __init__(self, url: str, db: str, username: str, password: str):
        self.url = url.rstrip("/")
        self.db = db
        self.username = username
        self.password = password
        self.uid: int | None = None

    async def _rpc(
        self, service: str, method: str, args: list, call_id: int = 1
    ) -> dict:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{self.url}/jsonrpc",
                json={
                    "jsonrpc": "2.0",
                    "method": "call",
                    "id": call_id,
                    "params": {
                        "service": service,
                        "method": method,
                        "args": args,
                    },
                },
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("error"):
                raise Exception(
                    data["error"].get("data", {}).get("message", str(data["error"]))
                )
            return data["result"]

    async def authenticate(self) -> int:
        self.uid = await self._rpc(
            "common",
            "authenticate",
            [self.db, self.username, self.password, {}],
        )
        if not self.uid:
            raise Exception("Authentication failed — check credentials")
        return self.uid

    async def _search_read(
        self, model: str, domain: list, fields: list, limit: int = 100
    ) -> list[dict]:
        if not self.uid:
            await self.authenticate()
        return await self._rpc(
            "object",
            "execute_kw",
            [
                self.db,
                self.uid,
                self.password,
                model,
                "search_read",
                [domain],
                {"fields": fields, "limit": limit},
            ],
            call_id=2,
        )

    async def poll_employees(self) -> list[dict]:
        """Fetch employees from Odoo hr.employee model."""
        return await self._search_read(
            "hr.employee",
            [],
            [
                "name",
                "job_title",
                "department_id",
                "work_email",
                "work_phone",
                "identification_id",
                "active",
            ],
        )

    async def poll_attendance(self, since: str) -> list[dict]:
        """Fetch attendance records from Odoo hr.attendance model."""
        return await self._search_read(
            "hr.attendance",
            [["check_in", ">", since]],
            ["employee_id", "check_in", "check_out", "worked_hours"],
        )

    async def _create(self, model: str, values: dict) -> int:
        """Create a record in Odoo. Returns the new record ID."""
        if not self.uid:
            await self.authenticate()
        return await self._rpc(
            "object",
            "execute_kw",
            [self.db, self.uid, self.password, model, "create", [values]],
            call_id=3,
        )

    async def create_employee(
        self,
        name: str,
        job_title: str = "",
        department_id: int | None = None,
        work_email: str = "",
        work_phone: str = "",
        identification_id: str = "",
    ) -> int:
        """Create an employee in Odoo."""
        vals = {"name": name}
        if job_title:
            vals["job_title"] = job_title
        if department_id:
            vals["department_id"] = department_id
        if work_email:
            vals["work_email"] = work_email
        if work_phone:
            vals["work_phone"] = work_phone
        if identification_id:
            vals["identification_id"] = identification_id
        return await self._create("hr.employee", vals)

    async def create_department(self, name: str) -> int:
        """Create a department in Odoo."""
        return await self._create("hr.department", {"name": name})

    async def poll_expenses(self, since: str) -> list[dict]:
        """Fetch expenses from Odoo hr.expense model (if available)."""
        try:
            return await self._search_read(
                "hr.expense",
                [["write_date", ">", since]],
                ["name", "total_amount", "employee_id", "date", "state"],
            )
        except Exception:
            return []
