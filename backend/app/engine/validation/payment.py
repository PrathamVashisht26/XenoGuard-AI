import json
from pathlib import Path
from .base import BaseValidator, ValidationError

_MODES_PATH = Path(__file__).parent.parent.parent.parent / "rules" / "payment_modes.json"
VALID_MODES: list[str] = json.loads(_MODES_PATH.read_text(encoding="utf-8"))["valid_modes"]


class PaymentValidator(BaseValidator):
    def validate(self, row: dict, context: dict) -> list[ValidationError]:
        mode = str(row.get("payment_mode", "") or "").strip().upper()
        if not mode or mode in ("NAN", "NONE", "NULL", ""):
            return []
        if mode not in VALID_MODES:
            return [ValidationError(
                field_name="payment_mode",
                error_code="PAYMENT_MODE_INVALID",
                error_category="PAYMENT",
                raw_value=mode,
                extra={"mode": mode, "valid_modes": ", ".join(VALID_MODES)},
            )]
        return []
