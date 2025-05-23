"""
Search protocol interface.

Defines a standardized method signature for search algorithms.
"""

from typing import Protocol


class SearchProtocol(Protocol):
    """Define the protocol for search algorithms."""

    def search(
        self, filepath: str, search_string: str, reread_on_query: bool = False
    ) -> str:
        """Search for a query in the specified file."""

    def supports_caching(self) -> bool:
        """
        Indicate whether the search algorithm supports caching.

        Returns:
            bool: True if caching is supported, False otherwise.
        """
