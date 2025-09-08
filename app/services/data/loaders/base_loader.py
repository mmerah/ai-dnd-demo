"""Base loader pattern for file operations."""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from app.interfaces.services.data import ILoader

T = TypeVar("T", bound=BaseModel)


class BaseLoader(ILoader[T], ABC, Generic[T]):
    """Abstract base class for data loaders following SOLID principles.

    Provides common functionality for file reading, validation, and error handling.
    """

    def __init__(self, validate_on_load: bool = True):
        """Initialize the base loader.

        Args:
            validate_on_load: Whether to validate data when loading
        """
        self.validate_on_load = validate_on_load

    def load(self, path: Path) -> T:
        """Load data from a file.

        Args:
            path: Path to the file to load

        Returns:
            Loaded and validated data

        Raises:
            FileNotFoundError: If the file doesn't exist
            RuntimeError: If loading or validation fails
        """
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

    def save(self, path: Path, data: T) -> None:
        """Save data to a file.

        Args:
            path: Path to save the file
            data: Data to save

        Raises:
            RuntimeError: If saving fails
        """
        try:
            # Ensure parent directory exists
            path.parent.mkdir(parents=True, exist_ok=True)

            # Convert to JSON-serializable dict
            json_data = self._prepare_for_save(data)

            # Save to file
            with open(path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            raise RuntimeError(f"Failed to save file {path}: {e}") from e

    def load_multiple(self, directory: Path, pattern: str = "*.json") -> dict[str, T]:
        """Load multiple files from a directory.

        Args:
            directory: Directory to load from
            pattern: Glob pattern for files to load

        Returns:
            Dictionary mapping file stems to loaded data
        """
        if not directory.exists():
            return {}

        result = {}
        for file_path in directory.glob(pattern):
            if file_path.is_file():
                try:
                    data = self.load(file_path)
                    result[file_path.stem] = data
                except Exception:
                    # Skip files that fail to load
                    continue

        return result

    @abstractmethod
    def _parse_data(self, data: dict[str, Any] | list[Any], source_path: Path) -> T:
        # Any is necessary here because raw JSON data can contain mixed types
        """Parse raw JSON data into the appropriate model.

        Args:
            data: Raw JSON data
            source_path: Path the data was loaded from (for error messages)

        Returns:
            Parsed and validated model instance

        Raises:
            RuntimeError: If parsing or validation fails
        """
        pass

    @abstractmethod
    def _prepare_for_save(self, data: T) -> dict[str, Any] | list[Any]:
        # Any is necessary for JSON-serializable output that can contain mixed types
        """Prepare model data for JSON serialization.

        Args:
            data: Model instance to prepare

        Returns:
            JSON-serializable dictionary or list
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
