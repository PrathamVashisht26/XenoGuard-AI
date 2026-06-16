from .base import BaseValidator, ValidationError

REQUIRED_FIELDS = [
    "order_id",
    "customer_name",
    "phone",
    "email",
    "country_code",
    "order_date",
    "product_name",
    "quantity",
    "unit_price",
    "total_amount",
    "payment_mode",
]

OPTIONAL_FIELDS = ["delivery_date", "discount_amount", "tax_amount", "transaction_date"]


class MissingFieldsValidator(BaseValidator):
    def validate(self, row: dict, context: dict) -> list[ValidationError]:
        errors = []
        for field_name in REQUIRED_FIELDS:
            val = row.get(field_name)
            if val is None or str(val).strip() in ("", "nan", "None", "null"):
                errors.append(ValidationError(
                    field_name=field_name,
                    error_code="MISSING_REQUIRED_FIELD",
                    error_category="MISSING",
                    raw_value="",
                    extra={"field": field_name},
                ))
        return errors
