"""
Logger configuration module.

Sets up logging with a predefined format and debug level.
"""

import logging


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(message)s",
)
logger = logging.getLogger()
