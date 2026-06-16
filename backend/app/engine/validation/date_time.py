import json
from datetime import datetime
from pathlib import Path
from .base import BaseValidator, ValidationError

_FORMATS_PATH = Path(__file__).parent.parent.parent.parent / "rules" / "date_formats.json"
_cfg = json.loads(_FORMATS_PATH.read_text(encoding="utf-8"))
ACCEPTED_FORMATS: list[str] = _cfg["accepted_formats"]

DATE_FIELDS = ["order_date", "transaction_date", "delivery_date", "created_at", "updated_at"]


class DateTimeValidator(BaseValidator):
    def validate(self, row: dict, context: dict) -> list[ValidationError]:
        errors = []
        for field_name in DATE_FIELDS:
            val = row.get(field_name)
            if not val or str(val).strip() in ("", "nan", "None", "null"):
                continue
            val_str = str(val).strip()
            parsed = self._try_parse(val_str)
            if not parsed:
                errors.append(ValidationError(
                    field_name=field_name,
                    error_code="DATE_FORMAT_INVALID",
                    error_category="DATE",
                    raw_value=val_str,
                    extra={"field": field_name, "value": val_str},
                ))
        return errors

    @staticmethod
    def _try_parse(value: str) -> bool:
        for fmt in ACCEPTED_FORMATS:
            try:
                datetime.strptime(value, fmt)
                return True
            except ValueError:
                pass
        return False
