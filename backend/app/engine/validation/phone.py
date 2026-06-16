import re
import json
from pathlib import Path
from .base import BaseValidator, ValidationError

_RULES_PATH = Path(__file__).parent.parent.parent.parent / "rules" / "phone_rules.json"
PHONE_RULES: dict = json.loads(_RULES_PATH.read_text(encoding="utf-8"))


class PhoneValidator(BaseValidator):
    def validate(self, row: dict, context: dict) -> list[ValidationError]:
        errors = []
        phone_raw = str(row.get("phone", "") or "").strip()
        country = str(row.get("country_code", "") or "").upper().strip()

        if not phone_raw:
            return []

        digits_only = re.sub(r"\D", "", phone_raw)
        rule = PHONE_RULES.get(country)

        if not rule:
            errors.append(ValidationError(
                field_name="country_code",
                error_code="COUNTRY_CODE_UNKNOWN",
                error_category="PHONE",
                raw_value=country,
                extra={"country": country},
            ))
            return errors

        expected = rule["digits"]
        country_name = rule["name"]

        if len(digits_only) != expected:
            errors.append(ValidationError(
                field_name="phone",
                error_code="PHONE_LENGTH_MISMATCH",
                error_category="PHONE",
                raw_value=phone_raw,
                extra={
                    "country": country,
                    "country_name": country_name,
                    "expected_digits": expected,
                    "actual_digits": len(digits_only),
                },
            ))
        elif not re.match(rule["regex"], digits_only):
            errors.append(ValidationError(
                field_name="phone",
                error_code="PHONE_PATTERN_INVALID",
                error_category="PHONE",
                raw_value=phone_raw,
                extra={"country": country, "country_name": country_name},
            ))

        return errors
