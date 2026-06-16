from .base import BaseValidator, ValidationError
from .phone import PhoneValidator
from .date_time import DateTimeValidator
from .email_validator import EmailValidator
from .payment import PaymentValidator
from .currency import CurrencyValidator
from .product import ProductValidator
from .duplicate import DuplicateDetector
from .missing_fields import MissingFieldsValidator
from .cross_field import CrossFieldValidator

__all__ = [
    "BaseValidator",
    "ValidationError",
    "PhoneValidator",
    "DateTimeValidator",
    "EmailValidator",
    "PaymentValidator",
    "CurrencyValidator",
    "ProductValidator",
    "DuplicateDetector",
    "MissingFieldsValidator",
    "CrossFieldValidator",
]

VALIDATOR_CHAIN: list[BaseValidator] = [
    MissingFieldsValidator(),
    PhoneValidator(),
    DateTimeValidator(),
    EmailValidator(),
    PaymentValidator(),
    CurrencyValidator(),
    ProductValidator(),
    CrossFieldValidator(),
    DuplicateDetector(),
]


def validate_row(row: dict, context: dict) -> list[ValidationError]:
    errors = []
    for validator in VALIDATOR_CHAIN:
        errors.extend(validator.validate(row, context))
    return errors
