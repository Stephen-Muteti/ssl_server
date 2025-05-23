"""
Memory-mapped file searcher.

Provides efficient file search using `mmap` for `reread=True`
and a cached set-based approach for `reread=False`.
"""

import mmap
import os
from typing import Optional

from .protocols import SearchProtocol

from ..logger import logger


class MmapSearcher(SearchProtocol):
    """
    Perform a hybrid file search using memory-mapped access.

    Supports two modes:
    - `reread=True`: Uses `mmap` for direct file access.
    - `reread=False`: Caches file content as a set for faster lookups.
    """

    def __init__(self) -> None:
        """Initialize MmapSearcher with optional cached data."""
        self.last_filepath: Optional[str] = None
        self.cached_content: Optional[mmap.mmap] = None
        self.line_cache: Optional[set[str]] = None

    def __repr__(self) -> str:
        """
        Return a string representation of the MmapSearcher instance.

        Returns:
            str: A formatted string describing the instance state.
        """
        return (
            f"MmapSearcher(last_filepath={self.last_filepath}, "
            f"cached_content={'Set' if self.line_cache else 'None'})"
        )

    def supports_caching(self) -> bool:
        """
        Indicate whether the search algorithm supports caching.

        Returns:
            bool: True if caching is supported, False otherwise.
        """
        return True

    def _get_mmap(self, filepath: str) -> Optional[mmap.mmap]:
        """
        Create a memory-mapped object for file search.

        Args:
            filepath (str): Path to the target file.

        Returns:
            Optional[mmap.mmap]: Memory-mapped file object if successful,
            otherwise None.
        """
        try:
            with open(filepath, "rb") as f:
                if os.fstat(f.fileno()).st_size == 0:
                    return None
                return mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

        except FileNotFoundError:
            return None
        except (OSError, ValueError) as e:
            logger.error("Failed to mmap file: %s", e)
            return None

    def _cache_lines(self, filepath: str) -> Optional[set[str]]:
        """
        Cache file content into a set for fast lookups.

        Args:
            filepath (str): Path to the file to cache.

        Returns:
            Optional[set[str]]: A set containing unique lines from the file.
        """
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                return {line.strip() for line in file}

        except (OSError, ValueError) as e:
            logger.error("Failed to cache lines: %s", e)
            return None

    def search(
        self, filepath: str, search_string: str, reread_on_query: bool = False
    ) -> str:
        """
        Search for a search_string in the specified file.

        Uses memory mapping (`mmap`) for `reread=True`, and caches lines
        as a set for fast lookup when `reread=False`.

        Args:
            filepath (str): Path to the file to search.
            search_string (str): Target string to look for.
            reread_on_query (bool): Whether to reload the file on every query.

        Returns:
            str: Search result:
                - "STRING EXISTS" if the search_string is found.
                - "STRING NOT FOUND" if the search_string is absent.
                - "FILE NOT FOUND" if the file does not exist.
                - "ERROR: <message>" if an exception occurs.
        """
        try:
            if not os.path.exists(filepath):
                return "FILE NOT FOUND"

            if reread_on_query:
                mm = self._get_mmap(filepath)
                if mm is None:
                    return "STRING NOT FOUND"

                search_string_bytes = (search_string + os.linesep).encode(
                    "utf-8"
                )
                found = mm.find(search_string_bytes) != -1
                mm.close()

                return "STRING EXISTS" if found else "STRING NOT FOUND"

            if filepath != self.last_filepath or self.line_cache is None:
                self.line_cache = self._cache_lines(filepath)
                self.last_filepath = filepath

            if self.line_cache is None:
                return "STRING NOT FOUND"

            return (
                "STRING EXISTS"
                if search_string in self.line_cache
                else "STRING NOT FOUND"
            )

        except (OSError, ValueError) as e:
            logger.error("MmapSearcher error: %s", e)
            return f"ERROR: {e}"
