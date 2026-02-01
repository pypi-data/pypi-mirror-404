import logging
import os
from argparse import Namespace
from pathlib import Path

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from shine2mqtt import PROJECT_ROOT
from shine2mqtt.api.config import ApiConfig
from shine2mqtt.growatt.client.config import SimulatedClientConfig
from shine2mqtt.growatt.server.config import GrowattServerConfig
from shine2mqtt.mqtt.config import MqttConfig

DEFAULT_CONFIG_FILE = PROJECT_ROOT / "config.yaml"

ENV_PREFIX = "SHINE2MQTT_"


class ApplicationConfig(BaseSettings):
    log_level: str = logging.getLevelName(logging.INFO)
    log_color: bool = True
    config_file: Path | None = None
    capture_data: bool = False
    mqtt: MqttConfig = Field(default_factory=MqttConfig)
    api: ApiConfig = Field(default_factory=ApiConfig)
    server: GrowattServerConfig = Field(default_factory=GrowattServerConfig)
    simulated_client: SimulatedClientConfig = Field(default_factory=SimulatedClientConfig)

    model_config = SettingsConfigDict(
        env_prefix=ENV_PREFIX,
        env_nested_delimiter="__",
        env_file=".env",
    )


class ConfigLoader:
    def load(self, cli_args: Namespace) -> ApplicationConfig:
        file_config = self._load_config_file(cli_args)
        cli_config = self._convert_cli_args(cli_args)

        merged_config = self._merge_dict(file_config, cli_config)

        return ApplicationConfig(**merged_config)

    def _merge_dict(self, base: dict, override: dict) -> dict:
        """Deep merge two dictionaries, with override taking precedence."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_dict(result[key], value)
            else:
                result[key] = value
        return result

    def _config_file(self, cli_args: Namespace) -> Path | None:
        if cli_args.config_file:
            return cli_args.config_file

        env_config_file = os.environ.get(f"{ENV_PREFIX}CONFIG_FILE")

        if env_config_file:
            return Path(env_config_file)

        if DEFAULT_CONFIG_FILE.is_file():
            return DEFAULT_CONFIG_FILE

        return None

    def _convert_cli_args(self, args: Namespace) -> dict:
        """Convert CLI args to nested dict using __ delimiter."""

        cli_config = {}
        for key, value in vars(args).items():
            # Remove unset arguments
            if value is None:
                continue

            # Check if key contains __ for nesting
            if "__" in key:
                # Split on __ to create nested structure
                parts = key.split("__")
                current = cli_config
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = value
            else:
                # Non-nested key, add directly
                cli_config[key] = value

        return cli_config

    def _load_config_file(self, cli_args: Namespace) -> dict:
        path = self._config_file(cli_args)

        if path is None:
            return {}

        if path.exists() is False:
            raise FileNotFoundError(f"Config file {path} does not exist")

        with open(path) as f:
            return yaml.safe_load(f)
