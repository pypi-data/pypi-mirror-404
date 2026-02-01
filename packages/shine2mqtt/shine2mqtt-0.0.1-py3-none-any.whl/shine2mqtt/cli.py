import argparse
import logging
from pathlib import Path


class ArgParser:
    def __init__(self):
        self.parser = argparse.ArgumentParser(__name__)

        self.parser.add_argument(
            "-l",
            "--log-level",
            help="Set the logging level (e.g., DEBUG, INFO, WARNING, ERROR)",
            choices=list(logging.getLevelNamesMapping().keys()),
            type=str,
            dest="log_level",
        )
        self.parser.add_argument(
            "--log-color",
            help="Set the logging level (e.g., DEBUG, INFO, WARNING, ERROR)",
            action="store_true",
            default=None,
            dest="log_color",
        )

        self.parser.add_argument("-c", "--config-file", type=Path)

        self.parser.add_argument(
            "--capture-data",
            help="Enable capturing of decoded frame data",
            action="store_true",
            default=None,
            dest="capture_data",
        )

        self.parser.add_argument(
            "-s",
            "--simulated-client",
            help="Run simulated TCP client instead of server",
            action="store_true",
            default=None,
            dest="simulated_client__enabled",
        )
        self.parser.add_argument(
            "--simulated-client-server-host", dest="simulated_client__server_host"
        )
        self.parser.add_argument(
            "--simulated-client-server-port", type=int, dest="simulated_client__server_port"
        )

        self.parser.add_argument("--mqtt-base-topic", dest="mqtt__base_topic")
        self.parser.add_argument("--mqtt-availability-topic", dest="mqtt__availability_topic")

        self.parser.add_argument("--mqtt-server-host", dest="mqtt__server__host")
        self.parser.add_argument("--mqtt-server-port", type=int, dest="mqtt__server__port")
        self.parser.add_argument("--mqtt-server-user", dest="mqtt__server__username")
        self.parser.add_argument("--mqtt-server-password", dest="mqtt__server__password")

        self.parser.add_argument(
            "--mqtt-discovery",
            action="store_true",
            default=None,
            dest="mqtt__discovery__enabled",
        )
        self.parser.add_argument(
            "--mqtt-discovery-inverter-model", dest="mqtt__discovery__inverter__model"
        )
        self.parser.add_argument(
            "--mqtt-discovery-datalogger-model", dest="mqtt__discovery__datalogger__model"
        )

        self.parser.add_argument("--server-host", dest="server__host")
        self.parser.add_argument("--server-port", type=int, dest="server__port")

        self.parser.add_argument("--api", action="store_true", default=None, dest="api__enabled")
        self.parser.add_argument("--api-host", dest="api__host")
        self.parser.add_argument("--api-port", type=int, dest="api__port")

    def parse(self) -> argparse.Namespace:
        return self.parser.parse_args()
