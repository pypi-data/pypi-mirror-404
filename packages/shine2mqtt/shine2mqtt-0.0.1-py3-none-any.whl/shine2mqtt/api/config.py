from dataclasses import dataclass


@dataclass
class ApiConfig:
    enabled: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
