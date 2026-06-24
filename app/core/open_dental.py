"""Open Dental REST API connector."""
import json
import urllib.error
import urllib.request
import datetime
from typing import Optional


class OpenDentalConnector:
    def __init__(self, api_url: str, developer_key: str, customer_key: str = ""):
        self.api_url = api_url.rstrip("/")
        self.developer_key = developer_key
        self.customer_key = customer_key

    def _headers(self) -> dict:
        h = {
            "Content-Type": "application/json",
            "Authorization": f"ODFHIR {self.developer_key}",
        }
        if self.customer_key:
            h["CustomerKey"] = self.customer_key
        return h

    def _get(self, endpoint: str) -> dict:
        req = urllib.request.Request(
            f"{self.api_url}/{endpoint}",
            headers=self._headers(),
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())

    def _post(self, endpoint: str, body: dict) -> dict:
        data = json.dumps(body).encode()
        req = urllib.request.Request(
            f"{self.api_url}/{endpoint}",
            data=data,
            headers=self._headers(),
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())

    def test_connection(self) -> bool:
        try:
            self._get("patients?Limit=1")
            return True
        except Exception:
            return False

    def search_patients(self, name: str = "", dob: str = "") -> list[dict]:
        """Return list of patient dicts matching name or DOB."""
        params = []
        if name:
            params.append(f"LName={urllib.parse.quote(name)}")
        if dob:
            params.append(f"Birthdate={dob}")
        qs = "&".join(params)
        try:
            result = self._get(f"patients?{qs}&Limit=50")
            return result if isinstance(result, list) else []
        except Exception:
            return []

    def insert_progress_note(
        self,
        patient_num: int,
        note_text: str,
        proc_date: Optional[str] = None,
        provider_num: int = 0,
    ) -> tuple[bool, str]:
        """Insert a progress note for a patient. Returns (success, message)."""
        if proc_date is None:
            proc_date = datetime.date.today().isoformat()
        try:
            self._post("procnotes", {
                "PatNum":    patient_num,
                "Note":      note_text,
                "ProcDate":  proc_date,
                "ProvNum":   provider_num,
            })
            return True, "Note sent to Open Dental successfully."
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            return False, f"HTTP {e.code}: {body}"
        except Exception as e:
            return False, str(e)


import urllib.parse
