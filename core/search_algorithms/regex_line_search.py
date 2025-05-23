"""
Regular expression-based search algorithm.

Implements a search method that uses regex patterns to match lines
in a file.
"""

import re
from typing import Optional

from .protocols import SearchProtocol

from ..logger import logger


class RegexLineSearcher(SearchProtocol):
    """
    Perform a search using regular expressions.

    Matches patterns with each line of the file for flexible and efficient
    searching.

    Attributes:
        file_content (Optional[list[str]]): Cached content of the file.
    """

    def __init__(self) -> None:
        """Initialize RegexLineSearcher with an empty file content cache."""
        self.file_content: Optional[list[str]] = None

    def __repr__(self) -> str:
        """
        Return a string representation of the RegexLineSearcher instance.

        Returns:
            str: A formatted string describing the searcher instance.
        """
        return (
            f"RegexLineSearcher(\n"
            f"    file_content_size="
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
        Search for lines matching a regex pattern.

        Args:
            filepath (str): Path to the file to search.
            search_string (str): Regex pattern to search for.
            reread_on_query (bool): If True, rereads the file on every call.

        Returns:
            str: One of the following results:
                - "STRING EXISTS" if a match is found.
                - "STRING NOT FOUND" if not.
                - "FILE NOT FOUND" if the file does not exist.
                - "ERROR: <message>" if an exception occurs.
        """
        try:
            if reread_on_query or self.file_content is None:
                with open(filepath, "r", encoding="utf-8") as f:
                    self.file_content = f.readlines()

            pattern = re.compile(f"^{re.escape(search_string)}$")
            for line in self.file_content:
                if pattern.match(line.strip()):
                    return "STRING EXISTS"

            return "STRING NOT FOUND"

        except FileNotFoundError:
            return "FILE NOT FOUND"
        except (OSError, ValueError) as e:
            logger.error("RegexLineSearcher failed: %s", e)
            return f"ERROR: {e}"
