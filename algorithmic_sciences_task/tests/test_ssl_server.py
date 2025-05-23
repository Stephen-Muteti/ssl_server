"""
SSL Test Server.

This module sets up a simple SSL server requiring client authentication.
It binds to a specified host and port, waits for a secure client connection,
and handles basic request processing.

Usage:
    Run this script with the required SSL certificate, key, and CA file:
    ```
    python test_ssl_server.py server.crt server.key ca.pem
    ```
"""

import socket
import ssl


def run_ssl_server(
    certfile: str,
    keyfile: str,
    cafile: str,
    host: str = "127.0.0.1",
    port: int = 5000,
) -> None:
    """
    Start an SSL server that requires client authentication.

    Args:
        certfile (str): Path to the server's certificate file.
        keyfile (str): Path to the server's private key file.
        cafile (str): Path to the CA certificate for client authentication.
        host (str): IP address to bind the server (default: "127.0.0.1").
        port (int): Port number to listen on (default: 5000).
    """
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.verify_mode = ssl.CERT_REQUIRED
    context.load_cert_chain(certfile=certfile, keyfile=keyfile)
    context.load_verify_locations(cafile=cafile)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, port))
        sock.listen(5)
        with context.wrap_socket(sock, server_side=True) as ssock:
            conn, _addr = ssock.accept()
            conn.recv(1024)  # just receive and discard
            conn.close()


if __name__ == "__main__":
    import sys

    run_ssl_server(sys.argv[1], sys.argv[2], sys.argv[3])
