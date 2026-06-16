from .base import BaseValidator, ValidationError


class ProductValidator(BaseValidator):
    def validate(self, row: dict, context: dict) -> list[ValidationError]:
        errors = []

        qty_raw = str(row.get("quantity", "") or "").strip()
        if qty_raw and qty_raw not in ("nan", "None", "null"):
            try:
                qty = float(qty_raw)
                if qty < 0:
                    errors.append(ValidationError(
                        field_name="quantity",
                        error_code="QUANTITY_NEGATIVE",
                        error_category="PRODUCT",
                        raw_value=qty_raw,
                        extra={"value": qty_raw},
                    ))
                elif qty == 0:
                    errors.append(ValidationError(
                        field_name="quantity",
                        error_code="QUANTITY_ZERO",
                        error_category="PRODUCT",
                        severity="WARNING",
                        raw_value=qty_raw,
                        extra={"value": qty_raw},
                    ))
                elif qty != int(qty):
                    errors.append(ValidationError(
                        field_name="quantity",
                        error_code="QUANTITY_NOT_INTEGER",
                        error_category="PRODUCT",
                        severity="WARNING",
                        raw_value=qty_raw,
                        extra={"value": qty_raw},
                    ))
            except ValueError:
                errors.append(ValidationError(
                    field_name="quantity",
                    error_code="QUANTITY_NOT_NUMERIC",
                    error_category="PRODUCT",
                    raw_value=qty_raw,
                    extra={"value": qty_raw},
                ))

        product_name = str(row.get("product_name", "") or "").strip()
        if not product_name or product_name in ("nan", "None", "null"):
            errors.append(ValidationError(
                field_name="product_name",
                error_code="PRODUCT_NAME_MISSING",
                error_category="PRODUCT",
                severity="WARNING",
                raw_value="",
                extra={},
            ))

        return errors
