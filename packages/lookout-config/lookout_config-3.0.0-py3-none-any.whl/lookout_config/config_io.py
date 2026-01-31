import yaml
import os
from typing import Any, get_origin, Literal
from pathlib import Path
from pydantic import ValidationError

from lookout_config.types import LookoutConfig
from lookout_config.helpers import YamlDumper


class ConfigIO:
    """Configuration I/O handler for Lookout configuration files."""

    file_name = "lookout.yml"
    schema_url = "https://greenroom-robotics.github.io/lookout/schemas/lookout.schema.json"

    def __init__(self, config_directory: str | Path = ""):
        """Initialize ConfigIO with a configurable config directory.

        Args:
            config_directory: Base configuration directory path.
        """
        if str(config_directory).startswith("~"):
            self.config_directory = Path(config_directory).expanduser()
        else:
            self.config_directory = (
                Path("~/.config/greenroom").joinpath(config_directory).expanduser()
            )

    def get_path(self) -> Path:
        """Returns the full path to the lookout configuration file."""
        return self.config_directory / self.file_name

    def parse(self, config: dict[str, Any]) -> LookoutConfig:
        """Parse a configuration dictionary into a LookoutConfig object."""
        return LookoutConfig(**config or {})

    def read(self) -> LookoutConfig:
        """Read and parse the lookout configuration file."""
        path = self.get_path()
        with open(path) as stream:
            try:
                return self.parse(yaml.safe_load(stream))
            except ValidationError as e:
                raise ValueError(f"Failed to parse {path}: {e}") from e

    def write(self, config: LookoutConfig, include_defaults: bool = False):
        """Write a LookoutConfig object to the configuration file."""
        path = self.get_path()
        # Make the parent dir if it doesn't exist
        os.makedirs(path.parent, exist_ok=True)
        json_string = config.model_dump(mode="json", exclude_defaults=not include_defaults)
        self._add_literal_fields_to_dict(config, json_string)
        with open(path, "w") as stream:
            print(f"Writing: {path}")
            headers = f"# yaml-language-server: $schema={ConfigIO.schema_url}"
            data = "\n".join([headers, yaml.dump(json_string, Dumper=YamlDumper, sort_keys=True)])
            stream.write(data)

    def _add_literal_fields_to_dict(self, obj: Any, data: dict):
        """Process fields of a model object, handling Literal fields and discriminated unions recursively."""
        if not hasattr(obj, "__class__") or not hasattr(obj.__class__, "model_fields"):
            return

        for field_name, field_info in obj.__class__.model_fields.items():
            field_value = getattr(obj, field_name)

            # Handle direct Literal fields
            if get_origin(field_info.annotation) == Literal:
                data[field_name] = field_value

            # Handle discriminated union fields
            elif hasattr(field_info, "discriminator") and field_info.discriminator:
                if field_value is not None:
                    if field_name not in data:
                        data[field_name] = {}
                    discriminator_name = str(field_info.discriminator)
                    data[field_name][discriminator_name] = getattr(field_value, discriminator_name)
                    # Recursively process the union member
                    self._add_literal_fields_to_dict(field_value, data[field_name])

            # Recursively process nested BaseModel objects
            elif hasattr(field_value, "__class__") and hasattr(
                field_value.__class__, "model_fields"
            ):
                if field_name not in data:
                    data[field_name] = {}
                self._add_literal_fields_to_dict(field_value, data[field_name])
