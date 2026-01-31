
import json
import os
import shutil
from pathlib import Path
from typing import Any, List, Optional, Union


class ObjectStorage:
    """
    Simple file-based object storage for persisting data with key-based access.

    Supports reading/writing text, JSON, and binary data with automatic
    directory creation and key-based file organization.
    """

    def __init__(self, base_path: Union[str, Path]):
        """
        Initialize the object storage.

        Args:
            base_path: Base directory path for storing objects
        """
        self._base_path = Path(base_path)
        self._base_path.mkdir(parents=True, exist_ok=True)

    @property
    def base_path(self) -> Path:
        """Return the base storage path."""
        return self._base_path

    def _get_full_path(self, key: str) -> Path:
        """Get the full file path for a key."""
        return self._base_path / key

    def read(self, key: str) -> Union[str, dict, list]:
        """
        Read data from storage. Automatically parses JSON if valid.

        Args:
            key: Storage key (relative path)

        Returns:
            Parsed JSON data (dict/list) or raw string
        """
        path = self._get_full_path(key)
        content = path.read_text(encoding="utf-8")
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return content

    def read_text(self, key: str, encoding: str = "utf-8") -> str:
        """
        Read data as text without JSON parsing.

        Args:
            key: Storage key (relative path)
            encoding: File encoding (default: "utf-8")

        Returns:
            File contents as string
        """
        return self._get_full_path(key).read_text(encoding=encoding)

    def read_bytes(self, key: str) -> bytes:
        """
        Read data as bytes.

        Args:
            key: Storage key (relative path)

        Returns:
            File contents as bytes
        """
        return self._get_full_path(key).read_bytes()

    def write(
        self,
        key: str,
        data: Union[str, bytes, dict, list],
        encoding: str = "utf-8",
    ) -> None:
        """
        Write data to storage.

        Args:
            key: Storage key (relative path)
            data: Data to write (str, bytes, dict, or list)
            encoding: File encoding for text data (default: "utf-8")

        Raises:
            TypeError: If data type is not supported
        """
        path = self._get_full_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(data, bytes):
            path.write_bytes(data)
        elif isinstance(data, str):
            path.write_text(data, encoding=encoding)
        elif isinstance(data, (dict, list)):
            content = json.dumps(data, ensure_ascii=False, default=str)
            path.write_text(content, encoding=encoding)
        else:
            raise TypeError(f"Unsupported data type: {type(data).__name__}")

    def delete(self, key: str, missing_ok: bool = False) -> None:
        """
        Delete a key from storage.

        Args:
            key: Storage key (relative path)
            missing_ok: If True, don't raise error if key doesn't exist
        """
        path = self._get_full_path(key)
        path.unlink(missing_ok=missing_ok)

    def exists(self, key: str) -> bool:
        """
        Check if a key exists in storage.

        Args:
            key: Storage key (relative path)

        Returns:
            True if key exists, False otherwise
        """
        return self._get_full_path(key).exists()

    def list_dirs(self) -> List[str]:
        """
        List immediate subdirectories in the storage root.

        Returns:
            List of directory names
        """
        return [p.name for p in self._base_path.iterdir() if p.is_dir()]

    def list_keys(self, prefix: str = "") -> List[str]:
        """
        List all keys (files) in storage, optionally filtered by prefix.

        Args:
            prefix: Key prefix to filter by (default: "")

        Returns:
            List of keys (relative paths from base)
        """
        base = self._base_path / prefix if prefix else self._base_path
        if not base.exists():
            return []

        keys = []
        for path in base.rglob("*"):
            if path.is_file():
                keys.append(str(path.relative_to(self._base_path)))
        return keys
