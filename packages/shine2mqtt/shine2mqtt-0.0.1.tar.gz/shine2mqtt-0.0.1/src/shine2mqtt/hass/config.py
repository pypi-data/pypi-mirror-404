import re

from pydantic import BaseModel, Field


class DeviceConfig(BaseModel):
    # FIXME model should be knows since we can not support everything, or at least we have to know
    model: str = "Unknown"
    brand: str = "Growatt"

    @property
    def device_id(self) -> str:
        brand = re.sub(r"[ \-|]+", "_", self.brand.strip().lower())
        model = re.sub(r"[ \-|]+", "_", self.model.strip().lower())

        return f"{brand}_{model}"

    @property
    def name(self) -> str:
        return f"{self.brand} {self.model}"


class HassDiscoveryConfig(BaseModel):
    enabled: bool = True
    base_topic: str = "solar"
    availability_topic: str = "solar/state"
    prefix_topic: str = "homeassistant"
    inverter: DeviceConfig = Field(default_factory=DeviceConfig)
    datalogger: DeviceConfig = Field(default_factory=DeviceConfig)
