import re
from .base import BaseValidator, ValidationError

# Matches: 99.99 | USD 99.99 | $99.99 | 1,234.56 | INR1234
CURRENCY_REGEX = re.compile(r"^[A-Z$€£₹¥]?\s?[\d,]+(\.\d{1,4})?$", re.IGNORECASE)


class CurrencyValidator(BaseValidator):
    CURRENCY_FIELDS = ["total_amount", "unit_price", "discount_amount", "tax_amount"]

    def validate(self, row: dict, context: dict) -> list[ValidationError]:
        errors = []
        for field_name in self.CURRENCY_FIELDS:
            val = str(row.get(field_name, "") or "").strip()
            if not val or val in ("nan", "None", "null", ""):
                continue
            cleaned = val.replace(",", "")
            if not CURRENCY_REGEX.match(cleaned):
                errors.append(ValidationError(
                    field_name=field_name,
                    error_code="CURRENCY_FORMAT_INVALID",
                    error_category="CURRENCY",
                    raw_value=val,
                    extra={"field": field_name, "value": val},
                ))
            else:
                # Also check for negative
                numeric_str = re.sub(r"[^\d.]", "", cleaned)
                try:
                    if float(numeric_str) < 0:
                        errors.append(ValidationError(
                            field_name=field_name,
                            error_code="AMOUNT_NEGATIVE",
                            error_category="CURRENCY",
                            severity="WARNING",
                            raw_value=val,
                            extra={"field": field_name},
                        ))
                except ValueError:
                    pass
        return errors
