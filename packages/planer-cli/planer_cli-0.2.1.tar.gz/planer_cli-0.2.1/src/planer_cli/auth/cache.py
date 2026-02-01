"""Token cache persistence for MSAL."""

import os
from pathlib import Path

from msal import SerializableTokenCache


class FileTokenCache(SerializableTokenCache):
    """File-based token cache with secure permissions.

    Persists the MSAL token cache to a file with mode 600 for security.
    """

    def __init__(self, cache_file: Path) -> None:
        """Initialize the token cache.

        Args:
            cache_file: Path to the cache file.
        """
        super().__init__()
        self.cache_file = cache_file
        self._load()

    def _load(self) -> None:
        """Load cache from file if it exists."""
        if self.cache_file.exists():
            with open(self.cache_file, "r") as f:
                self.deserialize(f.read())

    def save(self) -> None:
        """Save cache to file with secure permissions."""
        if self.has_state_changed:
            # Create parent directories if needed
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)

            # Write with secure permissions (user read/write only)
            with open(self.cache_file, "w") as f:
                os.chmod(self.cache_file, 0o600)
                f.write(self.serialize())

    def clear(self) -> None:
        """Clear the cache file."""
        if self.cache_file.exists():
            self.cache_file.unlink()
        # Clear in-memory cache by deserializing empty state
        self.deserialize("{}")
