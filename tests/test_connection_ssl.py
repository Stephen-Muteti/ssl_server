"""
Unit tests for SSL connections in FileSearchClient.

This module tests mutual TLS authentication, logging behavior,
and handling of invalid certificates.
"""

import subprocess
import time

from unittest.mock import patch
from unittest.mock import MagicMock

from pathlib import Path
from typing import Generator
import ssl

import pytest
from pytest import MonkeyPatch

from client.client import FileSearchClient

SERVER_SCRIPT = Path("tests/test_ssl_server.py")


@pytest.fixture(autouse=True)
def mock_ssl_config(monkeypatch: MonkeyPatch) -> None:
    """
    Mock SSL configuration values for testing.

    Replaces `get_config_value` with hardcoded values to ensure
    consistent behavior during SSL-related tests.

    Args:
        monkeypatch (MonkeyPatch):
            Pytest fixture for modifying global behavior.
    """

    def fake_get_config_value(
        _section: str, key: str, default: object = None
    ) -> object:
        return {"ssl_enabled": True, "host": "127.0.0.1", "port": 4443}.get(
            key, default
        )

    monkeypatch.setattr(
        "client.client.get_config_value", fake_get_config_value
    )


@pytest.fixture(scope="module")
def _start_test_server() -> Generator[None, None, None]:
    """
    Start the test server in SSL mode before running tests.

    Ensures the server is up before tests execute, and shuts it down after.

    Yields:
        None: Server fixture cleanup after tests.
    """
    cert_dir = Path("tests/certs")

    with subprocess.Popen(
        [
            "python",
            str(SERVER_SCRIPT),
            str(cert_dir / "server.crt"),
            str(cert_dir / "server.key"),
            str(cert_dir / "ca.pem"),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ) as server_proc:
        time.sleep(1)

        if server_proc.poll() is not None:
            stderr_output = (
                server_proc.stderr.read().decode()
                if server_proc.stderr
                else "Unknown error"
            )
            raise RuntimeError(
                f"Test server failed to start:\n{stderr_output}"
            )

        yield

        server_proc.terminate()
        server_proc.wait()


# Fixture with intentionally invalid cert
@pytest.fixture
def client_with_invalid_cert() -> FileSearchClient:
    """
    Create a client using invalid SSL certificates.

    Returns:
        FileSearchClient: A client configured with incorrect certificates.
    """
    client = FileSearchClient()
    client.client_cert = "tests/certs/invalid_client.crt"
    client.client_key = "tests/certs/invalid_client.key"
    client.server_cert = "tests/certs/ca.pem"
    return client


def test_connection_with_wrong_cert(_start_test_server: None) -> None:
    """
    Test failure of SSL connection due to mismatched client certificate.

    Ensures that the server rejects connections when the client uses
    certificates not signed by the trusted CA.

    Args:
        start_test_server (None): Fixture that launches the SSL test server.
    """
    client = FileSearchClient()
    client.client_cert = "tests/certs/invalid_client.crt"
    client.client_key = "tests/certs/invalid_client.key"
    client.server_cert = "tests/certs/ca.pem"

    with pytest.raises(ssl.SSLError):
        conn = client.connect()
        if conn is None:
            raise ssl.SSLError("SSL connection setup failed")
        conn.connect((client.host, client.port))


def test_mtls_rejects_invalid_client(
    _start_test_server: None, client_with_invalid_cert: FileSearchClient
) -> None:
    """
    Validate server-side enforcement of client certificate verification.

    This test ensures that mutual TLS (mTLS) is correctly implemented and
    the server rejects unauthorized client certificates.

    Args:
        start_test_server (None): Fixture to start/stop test SSL server.
        client_with_invalid_cert (FileSearchClient): Client with invalid certs.
    """
    with pytest.raises(ssl.SSLError):
        conn = client_with_invalid_cert.connect()
        if conn is None:
            raise ssl.SSLError("SSL connection setup failed")
        conn.connect(
            (client_with_invalid_cert.host, client_with_invalid_cert.port)
        )


@patch("client.client.logger")
def test_logging_on_ssl_failure(mock_logger: MagicMock) -> None:
    """
    Ensure proper logging occurs during SSL connection failure.

    Verifies that the logger captures and reports connection setup
    errors when SSL certificate files are missing.

    Args:
        mock_logger (MagicMock): Patched logger to intercept error messages.
    """
    client = FileSearchClient()
    client.client_cert = "tests/certs/missing.crt"
    client.client_key = "tests/certs/missing.key"
    client.server_cert = "tests/certs/ca.pem"

    # Should return None and log an error
    conn = client.connect()
    assert conn is None

    # Extract logged error messages
    logged_messages = [
        call.args[0] for call in mock_logger.error.call_args_list
    ]
    assert any("SSL connection setup failed" in msg for msg in logged_messages)


def test_successful_ssl_connection(_start_test_server: None) -> None:
    """
    Test a successful mTLS connection with valid certificates.

    Verifies that the FileSearchClient can establish a secure connection and
    transmit data using correct credentials.

    Args:
        start_test_server (None): Fixture to ensure the server is running.
    """
    client = FileSearchClient()
    client.client_cert = "tests/certs/client.crt"
    client.client_key = "tests/certs/client.key"
    client.server_cert = "tests/certs/ca.pem"

    conn = client.connect()
    assert conn is not None

    # Establish connection and send dummy data
    conn.connect((client.host, client.port))
    conn.send(b"Hello test server!")
    conn.close()
