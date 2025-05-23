"""
Buffered chunk search algorithm.

Implements a search method that processes files in fixed-size chunks
to efficiently locate exact line matches without loading the entire file
into memory.
"""

from .protocols import SearchProtocol

# Local imports
from ..logger import logger


class BufferedChunkSearcher(SearchProtocol):
    """
    Implement a search algorithm that reads a file in fixed-size chunks.

    This approach checks for exact line matches without loading the entire
    file into memory.
    """

    def __init__(self) -> None:
        """Initialize BufferedChunkSearcher with caching attributes."""
        self.cached_results: dict[str, bool] = {}
        self.last_filepath: str | None = None
        self.last_search_string: str | None = None

    def __repr__(self) -> str:
        """
        Return a string representation of the BufferedChunkSearcher instance.

        Returns:
            str: A formatted string describing the instance and cached data.
        """
        return (
            "BufferedChunkSearcher("
            f"last_filepath={self.last_filepath}, "
            f"last_search_string={self.last_search_string}, "
            f"cached_results={len(self.cached_results)} items)"
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
        Search for an exact match of a search_string using buffered reading.

        Args:
            filepath (str): Path to the file to search.
            search_string (str): Exact line to look for in the file.
            reread_on_query (bool): Whether the file should be reloaded.

        Returns:
            str: One of the following results:
                - "STRING EXISTS" if found.
                - "STRING NOT FOUND" if not.
                - "FILE NOT FOUND" if the file does not exist.
                - "ERROR: <message>" on failure.
        """
        if (
            not reread_on_query
            and self.last_filepath == filepath
            and self.last_search_string == search_string
        ):
            return (
                "STRING EXISTS"
                if self.cached_results.get(filepath + search_string, False)
                else "STRING NOT FOUND"
            )

        # Number of bytes per read
        buffer_size = 8192
        remainder = ""

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                while True:
                    chunk = f.read(buffer_size)
                    if not chunk:
                        break
                    lines = (remainder + chunk).split("\n")
                    remainder = lines.pop()
                    for line in lines:
                        if line.strip() == search_string:
                            self._cache_result(filepath, search_string, True)
                            return "STRING EXISTS"

                if remainder and remainder.strip() == search_string:
                    self._cache_result(filepath, search_string, True)
                    return "STRING EXISTS"

                self._cache_result(filepath, search_string, False)
                return "STRING NOT FOUND"

        except FileNotFoundError:
            return "FILE NOT FOUND"
        except (OSError, ValueError) as e:
            logger.error("BufferedChunkSearcher failed: %s", e)
            return f"ERROR: {e}"

    def _cache_result(
        self, filepath: str, search_string: str, result: bool
    ) -> None:
        """
        Cache the search result for faster repeated queries.

        Args:
            filepath (str): Path to the file being searched.
            search_string (str): Exact search_string searched.
            result (bool): Whether the search_string was found in the file.
        """
        self.cached_results[filepath + search_string] = result
        self.last_filepath = filepath
        self.last_search_string = search_string
