"""
Connection handler module.

Manages client communication, search execution, and response handling.
"""

# Standard library imports
import socket
import time
from datetime import datetime
from typing import Tuple, Type
from socket import timeout as socket_timeout

# Local project imports
from config.settings import CONFIG_FILE_PATH

# Core module imports
from core.logger import logger
from core.config_loader import get_config_value

# Search algorithm imports
from core.search_algorithms.protocols import SearchProtocol
from core.search_algorithms.line_by_line import LineByLineSearcher
from core.search_algorithms.mmap_search import MmapSearcher
from core.search_algorithms.buffered_chunk_search import BufferedChunkSearcher
from core.search_algorithms.regex_line_search import RegexLineSearcher
from core.search_algorithms.trie_search import TrieBasedSearcher
from core.search_algorithms.cached_line_search import CachedLineSearcher
from core.search_algorithms.set_based_searcher import SetBasedSearcher

# Mapping of algorithm names to classes.
# We maintain the entire dictionary for easy swithing.
# Should our optimizations change in the future.
SEARCH_CLASSES: dict[str, Type[SearchProtocol]] = {
    "line_by_line": LineByLineSearcher,
    "mmap": MmapSearcher,
    "buffered_chunk": BufferedChunkSearcher,
    "regex": RegexLineSearcher,
    "trie": TrieBasedSearcher,
    "cached": CachedLineSearcher,
    "set": SetBasedSearcher,
}


class ClientHandler:
    """
    Handle communication with a connected client.

    Includes receiving queries, executing searches, and sending responses.
    Disconnects clients after inactivity timeout.
    """

    def __init__(
        self, client_socket: socket.socket, client_address: Tuple[str, int]
    ) -> None:
        """
        Initialize ClientHandler with client socket and address.

        Stores client details, sets timeout, and selects the search algorithm.
        """
        self.client_socket = client_socket
        self.client_address = client_address
        self.timeout = get_config_value(
            CONFIG_FILE_PATH, "client_timeout_time", default=15
        )
        self.file_path = get_config_value(CONFIG_FILE_PATH, "linuxpath")
        self.reread_on_query = get_config_value(
            CONFIG_FILE_PATH, "reread", default=True
        )
        self.algorithm_name = get_config_value(
            CONFIG_FILE_PATH, "search_algorithm", default="mmap"
        )
        self.searcher: SearchProtocol = SEARCH_CLASSES.get(
            "mmap", MmapSearcher
        )()

    def __repr__(self) -> str:
        """
        Return a string representation of the ClientHandler instance.

        Includes the client's address to facilitate debugging and logging.

        Returns:
            str: A formatted string identifying the client connection.
        """
        return f"ClientHandler({self.client_address})"

    def _send_to_client(self, message: str) -> None:
        """Send a message to the client using UTF-8 encoding."""
        try:
            self.client_socket.send(message.encode("utf-8"))
        except (socket.error, BrokenPipeError) as e:
            logger.debug(
                "Failed to send message to %s: %s", self.client_address, e
            )

    def _process_query(self, query: str) -> Tuple[str, float]:
        """Execute search and return result with execution time."""
        start_time = time.time()
        result = self.searcher.search(
            self.file_path, query, self.reread_on_query
        )
        elapsed_time = time.time() - start_time
        return result, elapsed_time

    def handle(self) -> None:
        """
        Handle client requests.

        It processes incoming search queries,
        handles timeouts, and sends back responses.
        """
        logger.debug("New connection from %s", self.client_address)
        self.client_socket.settimeout(self.timeout)

        try:
            while True:
                try:
                    data = self.client_socket.recv(1024)
                    if not data:
                        logger.info(
                            "Client %s closed the connection.",
                            self.client_address,
                        )
                        break

                    query = data.decode("utf-8").strip()
                    response, exec_time = self._process_query(query)

                    # Build debug info
                    debug_info = (
                        f"DEBUG: Timestamp: {datetime.now().isoformat()}, "
                        f"Search Query: {query}, "
                        f"IP: {self.client_address}, "
                        f"Response: {response}, "
                        f"Algorithm: {self.algorithm_name}, "
                        f"Execution Time: {exec_time:.6f} seconds"
                    )

                    # Combine the search response and debug info
                    full_response = f"{response}\n{debug_info}"

                    # Send the full response to the client
                    self._send_to_client(full_response)

                    # Log it to the server logs separately
                    logger.debug(debug_info)

                except socket_timeout:
                    logger.info(
                        "Client %s idle for too long. Disconnecting",
                        self.client_address,
                    )
                    self._send_to_client(
                        "__TIMEOUT__: Server disconnected due to inactivity."
                    )
                    break
        except (socket.error, ValueError, OSError) as e:
            logger.error(
                "Error handling client %s: %s", self.client_address, e
            )
            self._send_to_client(f"ERROR: {str(e)}")

        finally:
            self.client_socket.close()
            logger.debug("Connection with %s closed.", self.client_address)
