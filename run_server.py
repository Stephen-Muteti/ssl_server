"""
Run the File Search Server.

Starts the server and listens for incoming connections.
"""

from server.tcp_server import SearchServer
from core.logger import logger

if __name__ == "__main__":
    try:
        logger.info("Starting File Search Server...")
        server = SearchServer()
        server.start()
    except KeyboardInterrupt:
        logger.info("Server shut down by user.")
