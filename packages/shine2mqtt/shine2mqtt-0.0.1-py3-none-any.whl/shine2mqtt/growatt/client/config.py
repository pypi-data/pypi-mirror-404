from dataclasses import dataclass


@dataclass
class SimulatedClientConfig:
    enabled: bool = False
    server_host: str = "localhost"
    server_port: int = 5279
    data_interval: int = 60  # seconds (1 minute)
    ping_interval: int = 180  # seconds (3 minutes)
