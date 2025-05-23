"""
Configuration settings for the benchmarking server.

Defines the path to the server's YAML configuration file.
"""

import os

CONFIG_FILE_PATH = os.path.join(
    os.path.dirname(__file__), "server_config.yaml"
)
