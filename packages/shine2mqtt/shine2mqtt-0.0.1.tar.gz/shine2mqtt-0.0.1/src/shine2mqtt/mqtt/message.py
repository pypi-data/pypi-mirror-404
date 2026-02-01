from dataclasses import dataclass


@dataclass
class MqttMessage:
    topic: str
    payload: str
    qos: int = 0
    retain: bool = False
    timeout: int | None = None
