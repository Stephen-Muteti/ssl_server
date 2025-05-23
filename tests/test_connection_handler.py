"""
Unit tests for ClientHandler.

NOTE:
These tests do NOT require a real configuration file.
All calls to `get_config_value` are mocked to return test-specific values.

This allows tests to run in isolation and avoids external dependencies.
"""

import socket
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from core.connection_handler import ClientHandler, SEARCH_CLASSES
from core.search_algorithms.mmap_search import MmapSearcher


@pytest.fixture
def mock_socket() -> MagicMock:
    """Provide a mocked socket object."""
    return MagicMock(spec=socket.socket)


@pytest.fixture
def tmp_file(tmp_path: Path) -> Path:
    """Create a temporary file with sample content."""
    file = tmp_path / "sample.txt"
    file.write_text("Hello\nFind me\nAnother line\n")
    return file


def test_handler_processes_query_and_sends_response(
    mock_socket: MagicMock, tmp_file: Path
) -> None:
    """
    Process a valid query and send the result.

    Args:
        mock_socket (MagicMock): Mocked socket instance.
        tmp_file (Path): Temporary file with sample data.
    """
    query = "Find me"
    reread = False
    mock_socket.recv.side_effect = [query.encode(), b""]

    # Mock config values
    with patch("core.connection_handler.get_config_value") as mock_cfg:
        # Mock config values to avoid relying on real config file
        mock_cfg.side_effect = lambda *_args, **_kwargs: {
            "client_timeout_time": 10,
            "linuxpath": str(tmp_file),
            "reread": reread,
            "search_algorithm": "mmap",
        }[_args[1]]

        selected_class = SEARCH_CLASSES["mmap"]

        with patch.object(
            selected_class, "search", return_value="MATCH: Find me"
        ) as mock_search:
            handler = ClientHandler(mock_socket, ("127.0.0.1", 5050))
            handler.handle()

            mock_search.assert_called_once_with(str(tmp_file), query, reread)
            sent_data = mock_socket.send.call_args[0][0].decode()
            assert "MATCH: Find me" in sent_data


def test_handler_timeout_disconnects_client(mock_socket: MagicMock) -> None:
    """
    Ensure a timeout results in the correct message being sent.

    Args:
        mock_socket (MagicMock): Mocked socket instance.
    """
    mock_socket.recv.side_effect = socket.timeout

    # Mock config values
    with patch("core.connection_handler.get_config_value") as mock_cfg:
        # Mock config values to avoid relying on real config file
        mock_cfg.side_effect = lambda *_args, **_kwargs: {
            "client_timeout_time": 5,
            "linuxpath": "/fake/path.txt",
            "reread": True,
            "search_algorithm": "mmap",
        }[_args[1]]

        handler = ClientHandler(mock_socket, ("127.0.0.1", 5050))
        handler.handle()

        sent_data = mock_socket.send.call_args[0][0].decode()
        assert "__TIMEOUT__" in sent_data


def test_handler_uses_correct_search_algorithm(
    mock_socket: MagicMock, tmp_file: Path
) -> None:
    """
    Verify that the correct search algorithm is selected and used.

    Args:
        mock_socket (MagicMock): Mocked socket instance.
        tmp_file (Path): Temporary file with sample data.
    """
    mock_socket.recv.side_effect = [b"Look here", b""]

    with patch("core.connection_handler.get_config_value") as mock_cfg, patch(
        "core.connection_handler.SEARCH_CLASSES",
        {"mmap": MmapSearcher},
    ), patch.object(
        MmapSearcher, "search", return_value="MATCH: Look here"
    ) as mock_search:
        # Mock config values to avoid relying on real config file
        mock_cfg.side_effect = lambda *_args, **_kwargs: {
            "client_timeout_time": 5,
            "linuxpath": str(tmp_file),
            "reread": True,
            "search_algorithm": "mmap",
        }[_args[1]]

        handler = ClientHandler(mock_socket, ("127.0.0.1", 8080))
        handler.handle()

        mock_search.assert_called_once_with(str(tmp_file), "Look here", True)
        sent_data = mock_socket.send.call_args[0][0].decode()
        assert "MATCH: Look here" in sent_data
