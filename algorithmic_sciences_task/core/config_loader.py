"""
Config loader module.

Provides utility functions to retrieve and parse values from
a YAML configuration file.
"""

# Standard library imports
import os
from typing import Any, Optional, Union

# Third-party imports
import yaml

# Local project imports
from core.logger import logger


def get_config_value(
    config_file_path: str, key: str, default: Optional[Any] = None
) -> Any:
    """
    Retrieve a configuration value from the YAML configuration file.

    Args:
        config_file_path (str): Path to the YAML configuration file.
        key (str): Configuration key to look up.
        default (Optional[Any], optional): Default value if the key
        is not found or an error occurs. Defaults to None.

    Returns:
        Any: The value corresponding to the key, parsed if applicable,
        or the default value when an error occurs.
    """
    try:
        with open(config_file_path, "r", encoding="utf-8") as config_file:
            config = yaml.safe_load(config_file)
            value = config.get(key, default)
            return parse_config_value(value)
    except (
        OSError,
        yaml.YAMLError,
    ) as e:
        logger.error("Failed to read config: %s", e)
        return default


def parse_config_value(value: Any) -> Union[str, bool, Any]:
    """
    Parse the config value to convert strings to boolean or absolute paths.

    Args:
        value (Any): This is the raw value from the configuration file.

    Returns:
        Union[str, bool, Any]: The parsed value as boolean,
        absolute file path, or the unchanged value.
    """
    if isinstance(value, str):
        lowered = value.lower()
        if lowered in ["true", "yes", "1"]:
            return True
        if lowered in [
            "false",
            "no",
            "0",
        ]:
            return False
        if value.endswith((".crt", ".key", ".txt", ".csv")):
            # Resolve to absolute path inside project
            project_root = os.path.dirname(os.path.abspath(__file__))
            abs_path = os.path.abspath(os.path.join(project_root, "..", value))
            return abs_path
    return value
