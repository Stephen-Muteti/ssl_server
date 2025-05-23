"""
Line-by-line search algorithm.

Implements a simple search method that scans a file one line at a time
to find exact search_string matches.
"""

from .protocols import SearchProtocol

from ..logger import logger


class LineByLineSearcher(SearchProtocol):
    """
    Perform a line-by-line search to find exact matches of a search_string.

    Suitable for smaller files and simple search needs.
    """

    def __repr__(self) -> str:
        """
        Return a string representation of the LineByLineSearcher instance.

        Returns:
            str: A formatted string describing the searcher instance.
        """
        return "LineByLineSearcher()"

    def supports_caching(self) -> bool:
        """
        Indicate whether the search algorithm supports caching.

        Returns:
            bool: True if caching is supported, False otherwise.
        """
        return True

    def search(
        self, filepath: str, search_string: str, _reread_on_query: bool = False
    ) -> str:
        """
        Search for an exact match of a search_string in the file.

        Args:
            filepath (str): The path to the file to search.
            search_string (str): The exact string to search for.
            reread_on_query (bool): Whether to reread file (unused here).

        Returns:
            str: One of the following strings
                - "STRING EXISTS" if found
                - "STRING NOT FOUND" if not
                - "FILE NOT FOUND"
                - "ERROR: <message>" on failure.
        """
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                for line in file:
                    if line.strip() == search_string:
                        return "STRING EXISTS"
            return "STRING NOT FOUND"
        except FileNotFoundError:
            return "FILE NOT FOUND"
        except (OSError, ValueError) as e:
            logger.error("LineByLineSearcher failed: %s", e)
            return f"ERROR: {e}"
