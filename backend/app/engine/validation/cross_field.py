from .base import BaseValidator, ValidationError


class CrossFieldValidator(BaseValidator):

    def validate(self, row: dict, context: dict) -> list[ValidationError]:
        errors = []
        qty = _to_float(row.get("quantity"))
        unit_price = _to_float(row.get("unit_price"))
        total_amount = _to_float(row.get("total_amount"))

        if qty is None or unit_price is None or total_amount is None:
            return []

        calculated = round(qty * unit_price, 2)
        declared = round(total_amount, 2)

        if declared > 0 and abs(calculated - declared) / declared > 0.05:
            errors.append(ValidationError(
                field_name="total_amount",
                error_code="CROSS_FIELD_AMOUNT_MISMATCH",
                error_category="INTEGRITY",
                raw_value=str(total_amount),
                extra={
                    "calculated": calculated,
                    "declared": declared,
                    "qty": qty,
                    "unit_price": unit_price,
                },
            ))

        return errors


import re

def _to_float(val) -> float | None:
    if val is None:
        return None
    cleaned = re.sub(r"[^\d.\-]", "", str(val))
    try:
        return float(cleaned)
    except ValueError:
        return None
