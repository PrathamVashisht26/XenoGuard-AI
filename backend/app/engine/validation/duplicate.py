from .base import BaseValidator, ValidationError


class DuplicateDetector(BaseValidator):

    def validate(self, row: dict, context: dict) -> list[ValidationError]:
        seen: set = context.setdefault("seen_order_ids", set())
        order_id = str(row.get("order_id", "") or "").strip()

        if not order_id or order_id in ("nan", "None", "null"):
            return []

        if order_id in seen:
            return [ValidationError(
                field_name="order_id",
                error_code="DUPLICATE_ORDER_ID",
                error_category="DUPLICATE",
                raw_value=order_id,
                extra={"order_id": order_id},
            )]

        seen.add(order_id)
        return []
