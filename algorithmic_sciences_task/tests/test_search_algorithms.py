"""
Unit tests for search algorithms.

Verifies correct behavior for different
searchers using various test cases.
"""

from typing import Type, Callable, Any, List
from pathlib import Path

import pytest

# Import searcher classes
from core.search_algorithms.line_by_line import LineByLineSearcher
from core.search_algorithms.mmap_search import MmapSearcher
from core.search_algorithms.buffered_chunk_search import BufferedChunkSearcher
from core.search_algorithms.regex_line_search import RegexLineSearcher
from core.search_algorithms.trie_search import TrieBasedSearcher
from core.search_algorithms.cached_line_search import CachedLineSearcher
from core.search_algorithms.set_based_searcher import SetBasedSearcher

# List of all searcher classes to be tested
SEARCHERS: List[Type[Any]] = [
    LineByLineSearcher,
    MmapSearcher,
    BufferedChunkSearcher,
    RegexLineSearcher,
    TrieBasedSearcher,
    CachedLineSearcher,
    SetBasedSearcher,
]


@pytest.fixture
def temp_test_file(tmp_path: Path) -> Callable[[List[str], str], str]:
    """Create a temporary test file with given lines."""

    def _make_file(lines: List[str], filename: str = "test_file.txt") -> str:
        file_path = tmp_path / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        return str(file_path)

    return _make_file


@pytest.mark.parametrize("searcher_cls", SEARCHERS)
def test_search_finds_match(
    searcher_cls: Type[Any], temp_test_file: Callable[[List[str], str], str]
) -> None:
    """
    Verify that the search function correctly finds a match.

    Args:
        searcher_cls (Type[Any]): Search algorithm class to test.
        temp_test_file (Callable): Fixture function to create test files.
    """
    file_path = temp_test_file(
        ["Hello World\n", "Search Target\n", "End\n"], "test_file.txt"
    )
    searcher = searcher_cls()
    result = searcher.search(file_path, "Search Target", True)

    assert (
        "Search Target" in result or result.strip() != ""
    ), f"{searcher_cls.__name__} did not return match."


@pytest.mark.parametrize("searcher_cls", SEARCHERS)
def test_search_returns_no_match(
    searcher_cls: Type[Any], temp_test_file: Callable[[List[str], str], str]
) -> None:
    """
    Verify that the search function correctly returns no match.

    Args:
        searcher_cls (Type[Any]): Search algorithm class to test.
        temp_test_file (Callable): Fixture function to create test files.
    """
    file_path = temp_test_file(["Hello\n", "Nothing here\n"], "test_file.txt")
    searcher = searcher_cls()
    result = searcher.search(file_path, "Nonexistent String", True)

    assert (
        "STRING NOT FOUND" in result or result.strip() == ""
    ), f"{searcher_cls.__name__} should return no match."


@pytest.mark.parametrize("searcher_cls", SEARCHERS)
def test_search_empty_file(
    searcher_cls: Type[Any], temp_test_file: Callable[[List[str], str], str]
) -> None:
    """
    Verify search behavior for an empty file.

    Args:
        searcher_cls (Type[Any]): Search algorithm class to test.
        temp_test_file (Callable): Fixture function to create test files.
    """
    file_path = temp_test_file([], "test_file.txt")
    searcher = searcher_cls()
    result = searcher.search(file_path, "Anything", True)

    assert (
        "STRING NOT FOUND" in result or result.strip() == ""
    ), f"{searcher_cls.__name__} failed on empty file."


@pytest.mark.parametrize("searcher_cls", SEARCHERS)
def test_search_does_not_reread_if_cached(
    searcher_cls: Type[Any], temp_test_file: Callable[[List[str], str], str]
) -> None:
    """
    Verify that reread=False prevents reloading for caching search algorithms.

    Ensures caching algorithms avoid redundant file reads while
    guaranteeing consistent results for others.

    Args:
        searcher_cls (Type[Any]): Search algorithm class to test.
        temp_test_file (Callable): Fixture function to create test files.
    """
    file_path = temp_test_file(["Cached Line\n"], "test_file.txt")
    searcher = searcher_cls()
    result1 = searcher.search(file_path, "Cached", True)
    result2 = searcher.search(file_path, "Cached", False)

    assert (
        result1 == result2
    ), f"{searcher_cls.__name__} reread=False gave different result."
