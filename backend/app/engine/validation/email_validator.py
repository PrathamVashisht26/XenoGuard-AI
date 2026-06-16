import re
from .base import BaseValidator, ValidationError

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


class EmailValidator(BaseValidator):
    def validate(self, row: dict, context: dict) -> list[ValidationError]:
        errors = []
        email = str(row.get("email", "") or "").strip()
        if not email or email in ("nan", "None", "null"):
            return []  # handled by MissingFieldsValidator if mandatory
        if not EMAIL_REGEX.match(email):
            errors.append(ValidationError(
                field_name="email",
                error_code="EMAIL_INVALID",
                error_category="EMAIL",
                raw_value=email,
                extra={"email": email},
            ))
        return errors
