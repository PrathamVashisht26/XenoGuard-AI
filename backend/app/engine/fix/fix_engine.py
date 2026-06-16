import re
from datetime import datetime

ACCEPTED_FORMATS = [
    "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y",
    "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S",
    "%d-%m-%Y", "%Y%m%d", "%d %b %Y", "%d %B %Y",
    "%b %d, %Y", "%B %d, %Y",
]


class FixEngine:
    def apply_fix(self, fix_action: str, row: dict, field_name: str) -> dict | None:
        handler_name = f"_fix_{fix_action.lower()}"
        handler = getattr(self, handler_name, None)
        if handler is None:
            return None
        try:
            return handler(row, field_name)
        except Exception:
            return None

    def _fix_strip_non_digits(self, row: dict, field_name: str) -> dict | None:
        original = str(row.get(field_name, "") or "")
        fixed = re.sub(r"\D", "", original)
        if not fixed:
            return None
        return {**row, field_name: fixed}

    def _fix_normalize_date_iso(self, row: dict, field_name: str) -> dict | None:
        val = str(row.get(field_name, "") or "").strip()
        for fmt in ACCEPTED_FORMATS:
            try:
                parsed = datetime.strptime(val, fmt)
                return {**row, field_name: parsed.strftime("%Y-%m-%d")}
            except ValueError:
                pass
        return None

    def _fix_strip_currency_symbols(self, row: dict, field_name: str) -> dict | None:
        val = str(row.get(field_name, "") or "")
        numeric_str = re.sub(r"[^\d.]", "", val.replace(",", ""))
        if not numeric_str:
            return None
        try:
            return {**row, field_name: f"{float(numeric_str):.2f}"}
        except ValueError:
            return None

    def _fix_remove_duplicate_row(self, row: dict, field_name: str) -> dict | None:
        return None


fix_engine = FixEngine()
