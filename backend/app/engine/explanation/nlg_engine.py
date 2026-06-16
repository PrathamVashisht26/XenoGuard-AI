import re
from app.engine.validation.base import ValidationError as VError


def _explain_phone_length_mismatch(e: VError) -> str:
    actual = e.extra.get("actual_digits", "?")
    expected = e.extra.get("expected_digits", "?")
    country = e.extra.get("country_name", e.extra.get("country", "this country"))
    return (
        f"Phone number '{e.raw_value}' contains {actual} digit(s), "
        f"but {country} requires exactly {expected} digits. "
        f"Remove any country prefix, spaces, or dashes before the local number."
    )


def _explain_phone_pattern_invalid(e: VError) -> str:
    country = e.extra.get("country_name", e.extra.get("country", "this country"))
    return (
        f"Phone number '{e.raw_value}' has the correct length but does not match "
        f"the valid number pattern for {country}. "
        f"Verify the starting digits are valid for this country."
    )


def _explain_country_code_unknown(e: VError) -> str:
    return (
        f"Country code '{e.raw_value}' is not recognized in our validation rules. "
        f"Use a valid ISO 3166-1 alpha-2 code (e.g., IN, SG, US, GB, AE, AU, DE)."
    )


def _explain_date_format_invalid(e: VError) -> str:
    field = e.extra.get("field", e.field_name or "date field")
    return (
        f"The value '{e.raw_value}' in '{field}' could not be parsed as a valid date. "
        f"Accepted formats: YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD HH:MM:SS. "
        f"Normalize to ISO 8601 format (YYYY-MM-DD) for best compatibility."
    )


def _explain_email_invalid(e: VError) -> str:
    return (
        f"'{e.raw_value}' is not a valid email address. "
        f"Common issues: missing '@' symbol, invalid domain, or unsupported special characters. "
        f"Expected format: user@domain.com"
    )


def _explain_payment_mode_invalid(e: VError) -> str:
    modes = e.extra.get("valid_modes", "CREDIT_CARD, DEBIT_CARD, UPI, NET_BANKING, CASH, WALLET")
    return (
        f"Payment mode '{e.raw_value}' is not in the accepted list. "
        f"Valid modes: {modes}."
    )


def _explain_currency_format_invalid(e: VError) -> str:
    field = e.extra.get("field", e.field_name or "amount field")
    return (
        f"Currency value '{e.raw_value}' in '{field}' is not in a recognized format. "
        f"Expected: a numeric value optionally prefixed with a currency code or symbol "
        f"(e.g., 'USD 99.99', '₹1,234.56', '99.99')."
    )


def _explain_amount_negative(e: VError) -> str:
    field = e.extra.get("field", e.field_name or "amount field")
    return (
        f"The amount in '{field}' is negative ({e.raw_value}). "
        f"Transaction amounts should be non-negative. "
        f"If this is a refund, consider using a dedicated refund record."
    )


def _explain_quantity_negative(e: VError) -> str:
    return (
        f"Product quantity '{e.raw_value}' is negative, which is invalid for a transaction record. "
        f"Quantities must be positive integers."
    )


def _explain_quantity_zero(e: VError) -> str:
    return (
        f"Product quantity is 0. A transaction with zero quantity may indicate a data entry error "
        f"or a cancelled order that was not filtered out."
    )


def _explain_quantity_not_integer(e: VError) -> str:
    return (
        f"Quantity '{e.raw_value}' is a decimal value. "
        f"Product quantities should be whole numbers unless fractional units are intentional."
    )


def _explain_quantity_not_numeric(e: VError) -> str:
    return (
        f"Quantity '{e.raw_value}' cannot be parsed as a number. "
        f"This field must contain a valid integer."
    )


def _explain_product_name_missing(e: VError) -> str:
    return (
        "Product name is empty. While not always critical, a missing product name "
        "reduces data quality and makes downstream reporting unreliable."
    )


def _explain_duplicate_order_id(e: VError) -> str:
    return (
        f"Order ID '{e.raw_value}' appears more than once in this dataset. "
        f"Duplicate order IDs indicate upstream data pipeline issues, "
        f"ETL merge conflicts, or accidental re-submission."
    )


def _explain_missing_required_field(e: VError) -> str:
    field = e.extra.get("field", e.field_name or "unknown field")
    return (
        f"Required field '{field}' is empty or missing. "
        f"This field must be populated for the transaction to be valid."
    )


def _explain_cross_field_amount_mismatch(e: VError) -> str:
    calc = e.extra.get("calculated", "?")
    declared = e.extra.get("declared", "?")
    qty = e.extra.get("qty", "?")
    price = e.extra.get("unit_price", "?")
    return (
        f"Amount mismatch: unit_price ({price}) × quantity ({qty}) = {calc}, "
        f"but total_amount is declared as {declared}. "
        f"The discrepancy exceeds the 5% tolerance threshold. "
        f"Verify pricing, quantity, or whether tax/discount is included."
    )


EXPLANATION_MAP = {
    "PHONE_LENGTH_MISMATCH": _explain_phone_length_mismatch,
    "PHONE_PATTERN_INVALID": _explain_phone_pattern_invalid,
    "COUNTRY_CODE_UNKNOWN": _explain_country_code_unknown,
    "DATE_FORMAT_INVALID": _explain_date_format_invalid,
    "EMAIL_INVALID": _explain_email_invalid,
    "PAYMENT_MODE_INVALID": _explain_payment_mode_invalid,
    "CURRENCY_FORMAT_INVALID": _explain_currency_format_invalid,
    "AMOUNT_NEGATIVE": _explain_amount_negative,
    "QUANTITY_NEGATIVE": _explain_quantity_negative,
    "QUANTITY_ZERO": _explain_quantity_zero,
    "QUANTITY_NOT_INTEGER": _explain_quantity_not_integer,
    "QUANTITY_NOT_NUMERIC": _explain_quantity_not_numeric,
    "PRODUCT_NAME_MISSING": _explain_product_name_missing,
    "DUPLICATE_ORDER_ID": _explain_duplicate_order_id,
    "MISSING_REQUIRED_FIELD": _explain_missing_required_field,
    "CROSS_FIELD_AMOUNT_MISMATCH": _explain_cross_field_amount_mismatch,
}

FIX_SUGGESTIONS = {
    "PHONE_LENGTH_MISMATCH": "Strip country prefix (+91, +65, etc.), spaces, and dashes — keep only the local digits.",
    "PHONE_PATTERN_INVALID": "Verify the number against official country phone number format documentation.",
    "COUNTRY_CODE_UNKNOWN": "Replace with a valid ISO 3166-1 alpha-2 country code (e.g., IN, SG, US).",
    "DATE_FORMAT_INVALID": "Normalize date to ISO 8601 format: YYYY-MM-DD.",
    "EMAIL_INVALID": "Correct the email to follow user@domain.tld format.",
    "PAYMENT_MODE_INVALID": "Map to the nearest valid payment mode or flag for manual review.",
    "CURRENCY_FORMAT_INVALID": "Strip currency symbols; ensure the value is numeric with 2 decimal places (e.g., 99.99).",
    "AMOUNT_NEGATIVE": "Verify if this is a refund or correction; use a positive value or a separate refund record.",
    "QUANTITY_NEGATIVE": "Set quantity to a positive integer.",
    "QUANTITY_ZERO": "Remove zero-quantity rows or confirm they represent valid cancelled orders.",
    "QUANTITY_NOT_INTEGER": "Round to the nearest whole number if fractional quantities are not intended.",
    "QUANTITY_NOT_NUMERIC": "Replace with a valid integer value.",
    "PRODUCT_NAME_MISSING": "Populate the product name field from your product catalog.",
    "DUPLICATE_ORDER_ID": "Remove duplicate rows or assign unique order IDs.",
    "MISSING_REQUIRED_FIELD": "Populate the missing field before reprocessing.",
    "CROSS_FIELD_AMOUNT_MISMATCH": "Recalculate total_amount as unit_price × quantity, then add applicable tax/discount.",
}

FIX_ACTIONS = {
    "PHONE_LENGTH_MISMATCH": "STRIP_NON_DIGITS",
    "DATE_FORMAT_INVALID": "NORMALIZE_DATE_ISO",
    "CURRENCY_FORMAT_INVALID": "STRIP_CURRENCY_SYMBOLS",
    "DUPLICATE_ORDER_ID": "REMOVE_DUPLICATE_ROW",
}


def explain_error(error: VError) -> tuple[str, str, str | None]:
    handler = EXPLANATION_MAP.get(error.error_code)
    explanation = handler(error) if handler else f"Validation failed on field '{error.field_name}' with code {error.error_code}."
    suggestion = FIX_SUGGESTIONS.get(error.error_code, "Review this field manually.")
    action = FIX_ACTIONS.get(error.error_code)
    return explanation, suggestion, action
