from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ValidationError:
    field_name: Optional[str]
    error_code: str
    error_category: str  # PHONE | DATE | EMAIL | PAYMENT | PRODUCT | DUPLICATE | MISSING | CURRENCY | INTEGRITY
    severity: str = "ERROR"  # ERROR | WARNING
    raw_value: Optional[str] = None
    extra: dict = field(default_factory=dict)  # validator-specific context for NLG


class BaseValidator(ABC):
    @abstractmethod
    def validate(self, row: dict, context: dict) -> list[ValidationError]:
        """Validate one row. Return list of errors (empty list = row is valid for this check)."""
        pass
