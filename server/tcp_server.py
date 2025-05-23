"""
TCP/SSL search server.

Implements a file search server that accepts incoming client connections,
wraps them in secure channels if configured, and hands them off to
ClientHandler sessions.
"""

import os
import platform
import sys
import socket
import threading
import signal
from typing import Tuple

# First-party imports (your internal modules)
from config.settings import CONFIG_FILE_PATH

# Core module imports (grouped together)
from core.ssl_wrapper import SSLSocketWrapper
from core.config_loader import get_config_value
from core.logger import logger
from core.connection_handler import ClientHandler


class SearchServer:
    """
    Handle client connections and manage file searches over TCP/SSL.

    Accepts incoming requests, secures connections if necessary, and
    forwards requests to the appropriate handler.
    """

    def __init__(self) -> None:
        """Initialize server configuration from the config file."""
        # Server configuration
        self.server_config = {
            "port": int(
                get_config_value(CONFIG_FILE_PATH, "server_port", default=5000)
            ),
            "ssl_enabled": get_config_value(
                CONFIG_FILE_PATH, "ssl_enabled", default=False
            ),
            "file_path": get_config_value(CONFIG_FILE_PATH, "linuxpath"),
        }

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.log_config = {
            "log_dir": get_config_value(
                CONFIG_FILE_PATH, "log_dir", default="/var/log"
            ),
            "clients": [],
        }

        # Lock to prevent race conditions
        self.clients_lock = threading.Lock()

        # SSL Certificates
        self.ssl_certificates = {
            "client_certfile": get_config_value(
                CONFIG_FILE_PATH, "client_certfile"
            ),
            "server_certfile": get_config_value(
                CONFIG_FILE_PATH, "server_certfile"
            ),
            "server_keyfile": get_config_value(
                CONFIG_FILE_PATH, "server_keyfile"
            ),
            "ca_bundle": get_config_value(
                CONFIG_FILE_PATH, "ca_bundle_file", default="certs/ca.pem"
            ),
        }

    def _get_log_paths(self) -> Tuple[str, str]:
        """Return paths for stdout and stderr log files."""
        stdout_path = os.path.join(self.log_config["log_dir"], "tcpserver.log")
        stderr_path = os.path.join(
            self.log_config["log_dir"], "tcpserver_error.log"
        )
        return stdout_path, stderr_path

    def daemonize(self) -> None:
        """Run the server as a background process."""
        if os.name == "posix":
            pid = os.fork()  # pylint: disable=no-member
            if pid > 0:
                sys.exit()

            os.setsid()  # pylint: disable=no-member

            pid = os.fork()  # pylint: disable=no-member
            if pid > 0:
                sys.exit()

            sys.stdout.flush()
            sys.stderr.flush()

            stdout_path, stderr_path = self._get_log_paths()

            try:
                os.makedirs(self.log_config["log_dir"], exist_ok=True)
                with open(stdout_path, "a", encoding="utf-8") as stdout, open(
                    stderr_path, "a", encoding="utf-8"
                ) as stderr:
                    os.dup2(stdout.fileno(), sys.stdout.fileno())
                    os.dup2(stderr.fileno(), sys.stderr.fileno())
            except (PermissionError, OSError) as e:
                logger.warning(
                    "Log path inaccessible (%s), falling back to home dir.",
                    e,
                )
                fallback_log = os.path.expanduser("~/tcpserver.log")
                with open(fallback_log, "a", encoding="utf-8") as stdout:
                    os.dup2(stdout.fileno(), sys.stdout.fileno())
                    os.dup2(stdout.fileno(), sys.stderr.fileno())

            signal.signal(signal.SIGTERM, self.shutdown)

    def shutdown(self, _signum: int, _frame: object) -> None:
        """Shutdown the server and close client connections."""
        logger.info("Shutting down server.")

        with self.clients_lock:
            for client in self.log_config["clients"]:
                try:
                    client.close()
                except (OSError, ValueError) as e:
                    logger.warning("Error closing client: %s", e)

        self.server_socket.close()
        sys.exit(0)

    def _setup_socket(self) -> None:
        """Bind server socket and begin listening."""
        self.server_socket.bind(("0.0.0.0", self.server_config["port"]))
        self.server_socket.listen(5)
        logger.info("Server started on port %s", self.server_config["port"])

    def _handle_client(
        self, client_socket: socket.socket, client_address: Tuple[str, int]
    ) -> None:
        """Handle client connection with mutual TLS authentication."""
        if self.server_config["ssl_enabled"]:
            ssl_wrapper = SSLSocketWrapper(
                self.ssl_certificates["server_certfile"],
                self.ssl_certificates["server_keyfile"],
                self.ssl_certificates["ca_bundle"],
            )
            client_socket = ssl_wrapper.wrap(client_socket)

        with self.clients_lock:
            self.log_config["clients"].append(client_socket)

        try:
            session = ClientHandler(client_socket, client_address)
            session.handle()
        finally:
            client_socket.close()
            with self.clients_lock:
                self.log_config["clients"].remove(client_socket)

    def start(self) -> None:
        """Start the main server loop and listen for incoming connections."""
        if platform.system() == "Linux" and not os.path.exists(
            "/run/systemd/system"
        ):
            self.daemonize()
        self._setup_socket()

        while True:
            try:
                client_socket, client_address = self.server_socket.accept()
                logger.info("Accepted connection from %s", client_address)

                threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, client_address),
                    daemon=True,
                ).start()

            except (OSError, ValueError) as e:
                logger.error("Server error: %s", e)
