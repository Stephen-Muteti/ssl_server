"""Client module for connecting to the file search server."""

import socket
import ssl
import time
import threading
import queue
from typing import Optional, Tuple
from core.logger import logger
from core.config_loader import get_config_value
from config.settings import CONFIG_FILE_PATH


class FileSearchClient:
    """
    A client for querying the file search server over TCP or SSL.

    Supports both single-query and interactive session modes.
    """

    def __init__(self) -> None:
        """
        Initialize the FileSearchClient.

        Sets up host, port, and SSL settings.
        """
        self.host = get_config_value(
            CONFIG_FILE_PATH, "server_host", default="127.0.0.1"
        )
        self.port = int(
            get_config_value(CONFIG_FILE_PATH, "server_port", default=5000)
        )
        self.ssl_enabled = get_config_value(CONFIG_FILE_PATH, "ssl_enabled")
        self.client_cert = get_config_value(
            CONFIG_FILE_PATH, "client_certfile"
        )
        self.client_key = get_config_value(CONFIG_FILE_PATH, "client_keyfile")
        self.server_cert = get_config_value(
            CONFIG_FILE_PATH, "server_certfile"
        )

    def connect(self) -> Optional[socket.socket]:
        """
        Establish a mutual TLS (mTLS) connection.

        Returns:
            Optional[socket.socket]:
                A connected socket or None if the connection fails.
        """
        try:
            raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if self.ssl_enabled:
                context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
                context.load_cert_chain(
                    certfile=self.client_cert, keyfile=self.client_key
                )
                context.verify_mode = ssl.CERT_REQUIRED
                context.load_verify_locations(self.server_cert)
                return context.wrap_socket(
                    raw_socket, server_hostname=self.host
                )

            return raw_socket
        except (OSError, ssl.SSLError) as e:
            logger.error("SSL connection setup failed: %s", e)
            return None

    def _handle_user_input(
        self,
        conn: socket.socket,
        stop_event: threading.Event,
        response_queue: queue.Queue,
    ) -> None:
        """Handle user input for queries."""
        while not stop_event.is_set():
            try:
                query = input("Enter the string to search: ").strip()
                if stop_event.is_set():
                    break
                if not query:
                    continue
                if query.lower() in {"exit", "quit"}:
                    print("Exiting client...")
                    stop_event.set()
                    break

                conn.sendall(query.encode("utf-8"))

                try:
                    response = response_queue.get(timeout=10)
                    parts = response.split("\n", 1)
                    print(f"Server Response: {parts[0]}")
                    if len(parts) > 1:
                        print(parts[1])
                except queue.Empty:
                    print("No response from server.")

            except KeyboardInterrupt:
                print("\nInterrupted by user. Exiting.")
                stop_event.set()
                break

    def _listen_for_server(
        self,
        conn: socket.socket,
        stop_event: threading.Event,
        response_queue: queue.Queue,
    ) -> None:
        """Background listener thread for receiving server messages."""
        while not stop_event.is_set():
            try:
                data = conn.recv(4096)
                if not data:
                    print("Server closed the connection.")
                    stop_event.set()
                    break
                message = data.decode("utf-8")
                if "__TIMEOUT__" in message:
                    print("\nConnection expired! Press Enter to restart.")
                    stop_event.set()

                response_queue.put(message)
            except OSError:
                stop_event.set()
                break

    def _setup_listener(
        self,
        conn: socket.socket,
        stop_event: threading.Event,
        response_queue: queue.Queue,
    ) -> threading.Thread:
        """Start and return the listener thread."""
        listener_thread = threading.Thread(
            target=self._listen_for_server,
            args=(conn, stop_event, response_queue),
        )
        listener_thread.start()
        return listener_thread

    def send_query_over_socket(
        self, s: socket.socket, query: str
    ) -> Tuple[Optional[float], str]:
        """
        Send a search query over an established mTLS connection.

        Args:
            s (socket.socket): Active socket connection.
            query (str): Search string.

        Returns:
            Tuple[Optional[float], str]:
                Response time in seconds and server response.
        """
        try:
            start_time = time.time()
            s.sendall(query.encode("utf-8"))
            data = s.recv(4096)
            latency = time.time() - start_time
            response = (
                data.decode("utf-8") if data else "Server closed connection."
            )
            logger.info("Server Response: %s", response)
            return latency, response
        except (OSError, ValueError) as e:
            logger.error("Error during query send: %s", e)
            return None, f"ERROR: {e}"

    def interactive_session(self) -> None:
        """Start an interactive session with mutual authentication."""
        print("File Search Client (type 'exit' to quit)\n")

        conn = self.connect()
        if not conn:
            print("Failed to connect to server.")
            return

        stop_event = threading.Event()
        response_queue: queue.Queue[str] = queue.Queue()

        listener_thread = self._setup_listener(
            conn, stop_event, response_queue
        )

        try:
            conn.connect((self.host, self.port))
            self._handle_user_input(conn, stop_event, response_queue)
        except (OSError, ValueError) as e:
            logger.error("Error during interactive session: %s", e)
        finally:
            stop_event.set()
            listener_thread.join(timeout=0.5)
            # pylint: disable=broad-exception-caught
            try:
                conn.shutdown(socket.SHUT_RDWR)
            except (BrokenPipeError, ConnectionResetError, socket.error) as e:
                logger.warning(
                    "Exception occurred during shutdown: %s", str(e)
                )
            except Exception as e:
                logger.warning(
                    "Exception occurred during shutdown: %s", str(e)
                )
            finally:
                conn.close()
                logger.info("Connection closed.")
            conn.close()
            logger.info("Connection closed.")


if __name__ == "__main__":
    try:
        client = FileSearchClient()
        client.interactive_session()
    except (OSError, ValueError) as e:
        logger.error("Fatal error in client: %s", e)
        print(f"Fatal error: {e}")
