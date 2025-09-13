"""Base loader pattern for file operations."""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from app.interfaces.services.data import ILoader

T = TypeVar("T", bound=BaseModel)


class BaseLoader(ILoader[T], ABC, Generic[T]):
    """Abstract base class for data loaders.

    Provides common functionality for file reading, validation, and error handling.
    """

    def __init__(self, validate_on_load: bool = True):
        """Initialize the base loader.

        Args:
            validate_on_load: Whether to validate data when loading
        """
        self.validate_on_load = validate_on_load

    def load(self, path: Path) -> T:
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse JSON from {path}: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to read file {path}: {e}") from e

        return self._parse_data(data, path)

    @abstractmethod
    def _parse_data(self, data: dict[str, Any] | list[Any], source_path: Path) -> T:
        """Parse raw JSON data into the appropriate model (Any is thus necessary).

        Args:
            data: Raw JSON data
            source_path: Path the data was loaded from (for error messages)

        Returns:
            Parsed and validated model instance

        Raises:
            RuntimeError: If parsing or validation fails
        """
        pass

    def _validate_data(self, data: T) -> None:
        """Validate loaded data.

        Args:
            data: Data to validate

        Raises:
            ValueError: If validation fails
        """
        if self.validate_on_load and isinstance(data, BaseModel):
            try:
                # Pydantic models validate on construction, but we can force revalidation
                data.model_validate(data.model_dump())
            except Exception as e:
                raise ValueError(f"Data validation failed: {e}") from e
