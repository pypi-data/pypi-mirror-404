# IMPORTANT
# After changing this file, run `python3 -m lookout_config.generate_schemas`
# To re-generate the json schemas
import os

from lookout_config.config_io import ConfigIO
from lookout_config.types import (
    GeolocationMode,
    LogLevel,
    LookoutConfig,
    Mode,
    Point,
    Polygon,
    PositioningSystem,
)


def get_config_io() -> ConfigIO:
    """Get a ConfigIO instance using the LOOKOUT_CONFIG_DIR environment variable."""
    config_dir = os.environ.get("LOOKOUT_CONFIG_DIR")
    if config_dir is None:
        raise ValueError("LOOKOUT_CONFIG_DIR environment variable is not set.")
    return ConfigIO(config_directory=config_dir)


__all__ = [
    "get_config_io",
    "ConfigIO",
    "LookoutConfig",
    "Mode",
    "LogLevel",
    "GeolocationMode",
    "Point",
    "Polygon",
    "PositioningSystem",
]
