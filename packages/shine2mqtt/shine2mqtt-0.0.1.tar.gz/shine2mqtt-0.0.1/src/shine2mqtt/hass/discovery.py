from typing import Any

from shine2mqtt import HOME_PAGE, __version__
from shine2mqtt.hass.config import HassDiscoveryConfig
from shine2mqtt.hass.map import DATALOGGER_SENSOR_MAP, INVERTER_SENSOR_MAP


class MqttDiscoveryBuilder:
    DISCOVERY_ORIGIN = {
        "name": "shine2mqtt",
        "sw_version": __version__,
        "support_url": HOME_PAGE,
    }

    def __init__(self, config: HassDiscoveryConfig):
        self._config = config

    def build_datalogger_discovery_message(
        self,
        datalogger_sw_version: str,
        datalogger_serial: str,
    ) -> dict[str, Any]:
        discovery_payload = {
            "availability_topic": self._config.availability_topic,
            "device": {
                "identifiers": [self._config.datalogger.device_id, datalogger_serial],
                "manufacturer": self._config.datalogger.brand,
                "model": self._config.datalogger.model,
                "name": self._config.datalogger.name,
                "sw_version": datalogger_sw_version,
                "serial_number": datalogger_serial,
                # "configuration_url": ip_address,
                # "connections": [["ip": ip_address],["mac": mac_address]],
            },
            "origin": self.DISCOVERY_ORIGIN,
            "components": {},
        }

        discovery_payload["components"] = self._build_components(
            DATALOGGER_SENSOR_MAP, "datalogger"
        )

        return discovery_payload

    def build_inverter_discovery_message(
        self, inverter_fw_version: str, inverter_serial: str
    ) -> dict[str, Any]:
        discovery_payload = {
            "availability_topic": self._config.availability_topic,
            "device": {
                "identifiers": [self._config.inverter.device_id, inverter_serial],
                "manufacturer": self._config.inverter.brand,
                "model": self._config.inverter.model,
                "name": self._config.inverter.name,
                "sw_version": inverter_fw_version,
                "serial_number": inverter_serial,
                "via_device": self._config.datalogger.device_id,
            },
            "origin": self.DISCOVERY_ORIGIN,
            "components": {},
        }

        discovery_payload["components"] = self._build_components(INVERTER_SENSOR_MAP, "inverter")

        return discovery_payload

    def _build_components(self, sensor_map: dict[str, dict], base_sub_topic: str) -> dict[str, Any]:
        components = {}

        for entity_id, sensor_config in sensor_map.items():
            component = {
                "platform": "sensor",
                "name": sensor_config["name"],
                "icon": sensor_config["icon"],
                "value_template": "{{ value_json.value }}",
                "unique_id": f"{entity_id}",
                "state_topic": f"{self._config.base_topic}/{base_sub_topic}/sensor/{entity_id}",
            }

            if "device_class" in sensor_config:
                component["device_class"] = sensor_config["device_class"]

            if "unit_of_measurement" in sensor_config:
                component["unit_of_measurement"] = sensor_config["unit_of_measurement"]

            if "entity_category" in sensor_config:
                component["entity_category"] = sensor_config["entity_category"]

            components[entity_id] = component

        return components

    def build_inverter_discovery_topic(self) -> str:
        return self._build_device_discovery_topic(self._config.inverter.device_id)

    def build_datalogger_discovery_topic(self) -> str:
        return self._build_device_discovery_topic(self._config.datalogger.device_id)

    def _build_device_discovery_topic(self, device_id: str) -> str:
        topic = f"{self._config.prefix_topic}/device/{device_id}/config"

        return topic
