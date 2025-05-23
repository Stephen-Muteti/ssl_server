"""
Cached line search algorithm.

Implements a search method that caches file contents for efficient
repeated queries.
"""

from typing import Optional

from .protocols import SearchProtocol


class CachedLineSearcher(SearchProtocol):
    """
    Cache the contents of a file for efficient repeated queries.

    Attributes:
        file_content (Optional[list[str]]): List of lines read from the file.
    """

    def __init__(self) -> None:
        """Initialize an empty file content cache."""
        self.file_content: Optional[list[str]] = None

    def __repr__(self) -> str:
        """
        Return a string representation of the CachedLineSearcher instance.

        Returns:
            str: A formatted string describing the instance state.
        """
        return (
            f"CachedLineSearcher(file_content_size="
            f"{len(self.file_content) if self.file_content else 0})"
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
        Search for a specific string in the file.

        Args:
            filepath (str): Path to the file to search.
            search_string (str): String to search for in the file.
            reread_on_query (bool):
                If True, rereads the file on every search call.

        Returns:
            str:
                - "STRING EXISTS" if the string is found.
                - "STRING NOT FOUND" if the string is not found.
                - "FILE NOT FOUND" if the file does not exist.
                - An error message if another exception occurs.
        """
        try:
            # Load or reload file content if needed
            if reread_on_query or self.file_content is None:
                with open(filepath, "r", encoding="utf-8") as file:
                    self.file_content = file.readlines()

            # Search for exact string match (stripped of whitespace)
            for line in self.file_content:
                if line.strip() == search_string:
                    return "STRING EXISTS"
            return "STRING NOT FOUND"

        except FileNotFoundError:
            return "FILE NOT FOUND"
        except (OSError, ValueError) as e:
            return f"ERROR: {str(e)}"
