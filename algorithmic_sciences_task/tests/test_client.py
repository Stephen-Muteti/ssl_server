"""
Unit tests for FileSearchClient.

Includes tests for connection handling, query sending,
and interactive session behavior.
"""

import socket
from unittest.mock import MagicMock, patch
from typing import Optional, Any
import time
import queue
from itertools import cycle

import pytest

from client.client import FileSearchClient

from core.logger import logger


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> FileSearchClient:
    """
    Create and return a mocked FileSearchClient instance.

    This fixture sets fixed configuration values instead of relying
    on external config files.

    Args:
        monkeypatch (pytest.MonkeyPatch):
            Fixture for modifying the environment.

    Returns:
        FileSearchClient: A mock client with predefined settings.
    """

    def mock_get_config_value(
        _path: str, key: str, default: Optional[str] = None
    ) -> str:
        """Return fixed mock configuration values."""
        overrides: dict[str, str] = {
            "server_host": "127.0.0.1",
            "server_port": "5000",
            "ssl_enabled": "false",
            "certfile": "",
        }
        return overrides.get(key, default or "")

    monkeypatch.setattr(
        "core.config_loader.get_config_value", mock_get_config_value
    )
    return FileSearchClient()


def test_connect_returns_socket(
    monkeypatch: pytest.MonkeyPatch, client: FileSearchClient
) -> None:
    """
    Verify that connect() correctly returns an SSL-wrapped socket.

    Args:
        client (FileSearchClient): The instance being tested.
    """
    # Force SSL to be enabled
    monkeypatch.setattr(client, "ssl_enabled", True)

    mock_socket = MagicMock()
    mock_ssl_socket = MagicMock()
    mock_context = MagicMock()
    mock_context.wrap_socket.return_value = mock_ssl_socket

    with patch("socket.socket", return_value=mock_socket), patch(
        "ssl.create_default_context", return_value=mock_context
    ):
        conn = client.connect()
        assert conn == mock_ssl_socket
        mock_context.wrap_socket.assert_called_once_with(
            mock_socket, server_hostname="127.0.0.1"
        )


def test_send_query_success(client: FileSearchClient) -> None:
    """
    Test successful query sending.

    Verifies correct handling when the server processes the query
    and returns a valid response.

    Args:
        client (FileSearchClient): The instance being tested.
    """
    mock_socket = MagicMock()
    mock_socket.recv.return_value = b"MATCH: Result"

    latency, response = client.send_query_over_socket(
        mock_socket, "query string"
    )

    assert latency is not None
    assert response == "MATCH: Result"
    mock_socket.sendall.assert_called_once_with(b"query string")
    mock_socket.recv.assert_called_once()


def test_send_query_server_timeout(client: FileSearchClient) -> None:
    """
    Test query handling when the server times out.

    Verifies response handling when a socket timeout occurs.

    Args:
        client (FileSearchClient): The instance being tested.
    """
    mock_socket = MagicMock()
    mock_socket.recv.side_effect = socket.timeout("timeout")

    latency, response = client.send_query_over_socket(mock_socket, "any")

    assert latency is None
    assert "ERROR" in response


def test_interactive_session_server_timeout(
    monkeypatch: pytest.MonkeyPatch, client: FileSearchClient
) -> None:
    """
    Test interactive session behavior when the server times out.

    Args:
        monkeypatch (pytest.MonkeyPatch):
            Fixture for modifying the environment.
        client (FileSearchClient): The instance being tested.
    """
    mock_socket = MagicMock()
    mock_socket.recv.side_effect = [
        b"__TIMEOUT__: Server disconnected due to inactivity.",
        b"",
    ]

    with patch.object(client, "connect", return_value=mock_socket):
        with patch("builtins.input", side_effect=["sample", "exit"]):
            monkeypatch.setattr("sys.stdout.write", lambda x: None)
            client.interactive_session()  # Should handle timeout gracefully


def test_interactive_session_normal_flow(
    monkeypatch: pytest.MonkeyPatch, client: FileSearchClient
) -> None:
    """
    Test correct behavior in an interactive session.

    Verifies response handling when receiving a normal server reply.

    Args:
        monkeypatch (pytest.MonkeyPatch):
            Fixture for modifying the environment.
        client (FileSearchClient): The instance being tested.
    """
    mock_socket = MagicMock()
    mock_socket.recv.side_effect = cycle([b"MATCH: Hello", b""])

    with patch.object(client, "connect", return_value=mock_socket):
        with patch("builtins.input", side_effect=["Hello", "exit"]):
            monkeypatch.setattr("sys.stdout.write", lambda x: None)
            client.interactive_session()
            time.sleep(0.1)


def test_interactive_session_queue_timeout(
    monkeypatch: pytest.MonkeyPatch, client: FileSearchClient
) -> None:
    """
    Test queue timeout handling in an interactive session.

    Ensures the client properly handles when no response
    is received within the expected time frame.
    """
    mock_socket = MagicMock()
    mock_socket.recv.return_value = b"MATCH: Dummy"

    class DummyQueue(queue.Queue):
        """
        A mock queue that always raises `queue.Empty` when `get()` is called.

        This simulates a timeout scenario for testing purposes.
        """

        def get(
            self, block: bool = True, timeout: Optional[float] = None
        ) -> Any:
            """Simulate queue timeout by always raising `queue.Empty`."""
            raise queue.Empty()

    with patch.object(client, "connect", return_value=mock_socket), patch(
        "builtins.input", side_effect=["TimeoutTest", "exit"]
    ), patch("client.client.queue.Queue", DummyQueue):
        monkeypatch.setattr("sys.stdout.write", lambda x: None)
        client.interactive_session()


def test_interactive_session_keyboard_interrupt(
    monkeypatch: pytest.MonkeyPatch, client: FileSearchClient
) -> None:
    """
    Test client behavior when a KeyboardInterrupt occurs.

    Simulates an interactive session where the user manually interrupts
    the execution by pressing Ctrl+C. Ensures the client handles the
    exception gracefully without crashing.

    Args:
        monkeypatch (pytest.MonkeyPatch):
            Fixture for modifying environment behavior.
        client (FileSearchClient): The instance being tested.
    """
    mock_socket = MagicMock()
    mock_socket.recv.return_value = b"MATCH: Dummy"

    with patch.object(client, "connect", return_value=mock_socket), patch(
        "builtins.input", side_effect=KeyboardInterrupt
    ):
        monkeypatch.setattr("sys.stdout.write", lambda x: None)
        client.interactive_session()


def test_interactive_session_shutdown_exception(
    monkeypatch: pytest.MonkeyPatch, client: FileSearchClient
) -> None:
    """
    Test client behavior when a shutdown exception occurs.

    Simulates an interactive session where the server sends a valid response,
    but an exception occurs during socket shutdown. Ensures that the client
    handles the error gracefully without crashing.

    Args:
        monkeypatch (pytest.MonkeyPatch):
            Fixture for modifying environment behavior.
        client (FileSearchClient): The instance being tested.
    """
    mock_socket = MagicMock()
    mock_socket.recv.side_effect = [b"MATCH: Hello", b""]
    mock_socket.shutdown.side_effect = Exception("Shutdown error")

    with patch.object(client, "connect", return_value=mock_socket), patch(
        "builtins.input", side_effect=["Hello", "exit"]
    ), patch.object(logger, "warning") as mock_log:
        monkeypatch.setattr("sys.stdout.write", lambda x: None)
        client.interactive_session()

        mock_log.assert_called_with(
            "Exception occurred during shutdown: %s", "Shutdown error"
        )


def test_network_disconnection(client: FileSearchClient) -> None:
    """Test client behavior when network disconnects mid-query."""
    mock_socket = MagicMock()
    mock_socket.recv.side_effect = socket.error("Mock disconnect")

    latency, response = client.send_query_over_socket(
        mock_socket, "test query"
    )

    assert latency is None
    assert "ERROR" in response
