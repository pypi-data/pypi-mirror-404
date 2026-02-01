from pydantic import BaseModel, Field

from shine2mqtt.hass.config import HassDiscoveryConfig


class MqttServerConfig(BaseModel):
    host: str = "localhost"
    port: int = 1883
    client_id: str = "shine2mqtt"
    username: str | None = None
    password: str | None = Field(default=None, repr=False)


class MqttConfig(BaseModel):
    base_topic: str = "solar"
    availability_topic: str = "solar/state"
    server: MqttServerConfig = Field(default_factory=MqttServerConfig)
    discovery: HassDiscoveryConfig = Field(default_factory=HassDiscoveryConfig)
