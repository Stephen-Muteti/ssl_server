"""
Set-based search algorithm.

Implements a search method that caches file contents in a set
for fast lookups, avoiding repeated reads.
"""

from typing import Optional

from .protocols import SearchProtocol


class SetBasedSearcher(SearchProtocol):
    """
    Cache lines from a file for efficient searches.

    Uses a set to store file content and refreshes the cache only when
    necessary.

    Attributes:
        cached_set (Optional[set[str]]): Cached set of lines
        (stripped of whitespace).
    """

    def __init__(self) -> None:
        """Initialize SetBasedSearcher with an empty cached set."""
        self.cached_set: Optional[set[str]] = None

    def __repr__(self) -> str:
        """
        Return a string representation of the SetBasedSearcher instance.

        Returns:
            str: A formatted string describing the cached state.
        """
        return (
            f"SetBasedSearcher("
            f"cached_size={len(self.cached_set) if self.cached_set else 0})"
        )

    def supports_caching(self) -> bool:
        """
        Indicate whether the search algorithm supports caching.

        Returns:
            bool: True if caching is supported, False otherwise.
        """
        return True

    def search(
        self, filepath: str, search_string: str, reread_on_query: bool = False
    ) -> str:
        """
        Search for a string using a cached set.

        Args:
            filepath (str): Path to the file to be searched.
            search_string (str): The string to search for in the file.
            reread_on_query (bool): Whether to refresh the cached set
            before searching.

        Returns:
            str: One of the following results:
                - "STRING EXISTS" if the string is found.
                - "STRING NOT FOUND" if not.
                - "FILE NOT FOUND" if the file does not exist.
                - An error message if an exception occurs.
        """
        try:
            # Refresh the cached set if required
            if reread_on_query or self.cached_set is None:
                with open(filepath, "r", encoding="utf-8") as file:
                    self.cached_set = {line.strip() for line in file}

            # Search for the string in the cached set
            return (
                "STRING EXISTS"
                if search_string in self.cached_set
                else "STRING NOT FOUND"
            )

        except FileNotFoundError:
            return "FILE NOT FOUND"
        except (OSError, ValueError) as e:
            return f"ERROR: {str(e)}"
