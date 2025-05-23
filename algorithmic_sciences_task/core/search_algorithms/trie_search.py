"""
Trie-based search algorithm.

Implements a search method that builds a Trie from file contents and
performs full-line search_string matches efficiently.
"""

from typing import Dict, Optional

from .protocols import SearchProtocol

from ..logger import logger


class TrieNode:
    """
    Represent a node in the Trie structure.

    Stores child nodes, matching lines, and marks the end of a stored string.
    """

    def __init__(self) -> None:
        """Initialize TrieNode with empty children and line storage."""
        self.children: Dict[str, "TrieNode"] = {}
        self.lines: list[str] = []
        self.is_end: bool = False

    def has_children(self) -> bool:
        """
        Check if the TrieNode has any child nodes.

        Returns:
            bool: True if it has children, False otherwise.
        """
        return bool(self.children)

    def __repr__(self) -> str:
        """
        Return a string representation of the TrieNode.

        Returns:
            str: Summary of stored lines and children count.
        """
        return (
            f"TrieNode(children={len(self.children)}, "
            f"lines={len(self.lines)})"
        )


class Trie:
    """Implement a Trie (prefix tree) for full-line string matches."""

    def __init__(self) -> None:
        """Initialize an empty Trie with a root node."""
        self.root = TrieNode()

    def insert(self, line: str) -> None:
        """
        Insert a line into the Trie character by character.

        Args:
            line (str): A line from the file to insert into the Trie.
        """
        node = self.root
        for char in line:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end = True
        node.lines.append(line)

    def search_exact(self, line: str) -> bool:
        """
        Check if an exact full-line match exists in the Trie.

        Args:
            line (str): The exact line to match.

        Returns:
            bool: True if the line exists, else False.
        """
        node = self.root
        for char in line:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end and line in node.lines


class TrieBasedSearcher(SearchProtocol):
    """
    Perform full-line search_string searches using a Trie-based approach.

    The Trie is constructed from file contents and provides efficient lookups.
    """

    def __init__(self) -> None:
        """Initialize TrieBasedSearcher with an empty Trie."""
        self.trie = Trie()
        self.loaded_file: Optional[str] = None

    def __repr__(self) -> str:
        """
        Return a string representation of the TrieBasedSearcher instance.

        Returns:
            str: Summary of Trie state and loaded file.
        """
        return f"TrieBasedSearcher(loaded_file={self.loaded_file})"

    def supports_caching(self) -> bool:
        """
        Indicate whether the search algorithm supports caching.

        Returns:
            bool: True if caching is supported, False otherwise.
        """
        return True

    def _preload_file(
        self, filepath: str, reread_on_query: bool = False
    ) -> None:
        """
        Load the file into the Trie.

        If not already loaded or if `reread_on_query` is True,
        rebuild the Trie with new data.

        Args:
            filepath (str): Path to the file to index.
            reread_on_query (bool): If True, forces reloading of the file.
        """
        if not reread_on_query and self.loaded_file == filepath:
            return

        self.trie = Trie()
        with open(filepath, "r", encoding="utf-8") as file:
            for line in file:
                self.trie.insert(line.strip())
        self.loaded_file = filepath

    def search(
        self, filepath: str, search_string: str, reread_on_query: bool = False
    ) -> str:
        """
        Search for an exact search_string match using a Trie.

        Args:
            filepath (str): Path to the file to search.
            search_string (str): search_string to search for.
            reread_on_query (bool, optional): If True, reload the file
            before searching. Defaults to False.

        Returns:
            str: One of the following results:
                - "STRING EXISTS" if the search_string is found.
                - "STRING NOT FOUND" if the search_string is not found.
                - "FILE NOT FOUND" if the file does not exist.
                - "ERROR: <message>" if an unexpected error occurs.
        """
        try:
            self._preload_file(filepath, reread_on_query)
            return (
                "STRING EXISTS"
                if self.trie.search_exact(search_string)
                else "STRING NOT FOUND"
            )
        except FileNotFoundError:
            return "FILE NOT FOUND"
        except (OSError, ValueError) as e:
            logger.error("TrieBasedSearcher search failed: %s", e)
            return f"ERROR: {e}"
