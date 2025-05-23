"""
SSL socket wrapper.

Encapsulates the setup of an SSL context and the wrapping of socket
objects using the provided certificate and private key.
"""

import ssl
from socket import socket
from core.logger import logger


class SSLSocketWrapper:
    """
    Wrap sockets using SSL for mutual TLS (mTLS) authentication.

    Provides a reusable SSL wrapper that ensures both client and server
    validate each other's certificates.
    """

    def __init__(self, certfile: str, keyfile: str, ca_bundle: str) -> None:
        """Initialize the SSL context with mutual TLS authentication."""
        self.certfile = certfile
        self.keyfile = keyfile
        self.ca_bundle = ca_bundle

        try:
            self.context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

            # Load server's certificate and private key
            self.context.load_cert_chain(
                certfile=self.certfile, keyfile=self.keyfile
            )

            # Require client authentication (mTLS enabled)
            self.context.verify_mode = ssl.CERT_REQUIRED

            # Load trusted CA bundle to validate clients
            self.context.load_verify_locations(self.ca_bundle)

        except ssl.SSLError as e:
            logger.error("Failed to initialize SSL context: %s", e)
            raise

    def wrap(self, sock: socket) -> ssl.SSLSocket:
        """
        Wrap a socket with SSL using the initialized context.

        Args:
            sock (socket): Plain TCP socket to be secured.

        Returns:
            ssl.SSLSocket: SSL-wrapped socket ready for secure communication.

        Raises:
            ssl.SSLError: If the wrapping fails.
        """
        try:
            return self.context.wrap_socket(sock, server_side=True)
        except ssl.SSLError as e:
            logger.error("SSL wrapping failed: %s", e)
            raise

    def __repr__(self) -> str:
        """
        Return a string representation of the SSLSocketWrapper instance.

        Includes paths to the certificates used for mutual TLS authentication.

        Returns:
            str: A formatted string describing the SSL wrapper instance.
        """
        return (
            f"SSLSocketWrapper("
            f"certfile={self.certfile}, "
            f"keyfile={self.keyfile}, "
            f"ca_bundle={self.ca_bundle})"
        )
