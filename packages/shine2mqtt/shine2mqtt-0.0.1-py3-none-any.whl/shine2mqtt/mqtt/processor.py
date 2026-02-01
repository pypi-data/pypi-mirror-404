import json
from dataclasses import asdict
from typing import Any

from loguru import logger

from shine2mqtt.growatt.protocol.messages import (
    BaseMessage,
    GrowattAnnounceMessage,
    GrowattBufferedDataMessage,
    GrowattDataMessage,
)
from shine2mqtt.growatt.protocol.messages.config import GrowattGetConfigResponseMessage
from shine2mqtt.hass.discovery import MqttDiscoveryBuilder
from shine2mqtt.hass.map import DATALOGGER_SENSOR_MAP, INVERTER_SENSOR_MAP
from shine2mqtt.mqtt.config import MqttConfig
from shine2mqtt.mqtt.message import MqttMessage


class MqttDataloggerMessageProcessor:
    def __init__(self, discovery: MqttDiscoveryBuilder, config: MqttConfig):
        self._discovery = discovery

        self._base_topic = config.base_topic
        self._hass_discovery = config.discovery.enabled

        self._availability_topic = config.availability_topic

        self._inverter_announced = False
        self._datalogger_announced = False

        self._datalogger_config = {}

    def process(self, message: BaseMessage) -> list[MqttMessage]:
        match message:
            case GrowattDataMessage() | GrowattBufferedDataMessage():
                return self._process_data_message(message)
            case GrowattAnnounceMessage():
                return self._process_announce_message(message)
            case GrowattGetConfigResponseMessage():
                return self._process_get_config_response(message)
            case _:
                logger.debug(f"No handler for this message type {type(message)}")
                return []

    # TODO not sure if this belongs here?
    def build_availability_message(self, online: bool) -> MqttMessage:
        payload = "online" if online else "offline"
        return MqttMessage(
            topic=self._availability_topic,
            payload=payload,
            qos=1,
            retain=True,
        )

    def _process_data_message(
        self, message: GrowattDataMessage | GrowattBufferedDataMessage
    ) -> list[MqttMessage]:
        return self._build_mqtt_messages(message)

    def _process_announce_message(self, message: GrowattAnnounceMessage) -> list[MqttMessage]:
        mqtt_messages = []
        if self._hass_discovery and not self._inverter_announced:
            logger.info("Appending inverter discovery message")
            mqtt_messages.append(self._build_inverter_discovery_messages(message))
            self._inverter_announced = True

        # use retain diagnostic sensors don't change over time
        mqtt_messages.extend(self._build_mqtt_messages(message, qos=1, retain=True))

        return mqtt_messages

    def _process_get_config_response(
        self, message: GrowattGetConfigResponseMessage
    ) -> list[MqttMessage]:
        logger.debug(f"Processing get config response message: {message}")
        mqtt_messages = []

        if (
            self._hass_discovery
            and message.name == "datalogger_sw_version"
            and not self._datalogger_announced
        ):
            logger.info("Appending datalogger discovery message")
            discovery_message = self._discovery.build_datalogger_discovery_message(
                datalogger_sw_version=str(message.value),
                datalogger_serial=message.datalogger_serial,
            )

            payload = json.dumps(discovery_message)
            topic = self._discovery.build_datalogger_discovery_topic()

            self._datalogger_announced = True

            return [MqttMessage(topic=topic, payload=payload, qos=1, retain=True)]

        if message.name is not None:
            self._datalogger_config[message.name] = message.value

        if self._datalogger_announced is False:
            return []

        for name, value in self._datalogger_config.items():
            if name not in DATALOGGER_SENSOR_MAP:
                logger.debug(
                    f"No sensor mapping found for datalogger config '{name}', skipping MQTT publish"
                )
                continue

            sensor_config = DATALOGGER_SENSOR_MAP[name]
            entity_id = sensor_config["entity_id"]

            topic = self._build_sensor_message_topic(entity_id, "datalogger")
            payload = json.dumps(self._build_sensor_message_payload(value, sensor_config))

            mqtt_messages.append(MqttMessage(topic=topic, payload=payload, retain=True))

        self._datalogger_config.clear()

        return mqtt_messages

    def _build_mqtt_messages(
        self,
        message: (GrowattAnnounceMessage | GrowattDataMessage | GrowattBufferedDataMessage),
        qos: int = 0,
        retain: bool = False,
    ) -> list[MqttMessage]:
        mqtt_messages = []

        for attribute_name, value in asdict(message).items():
            if attribute_name == "header":
                continue

            if attribute_name not in INVERTER_SENSOR_MAP:
                logger.debug(f"No sensor mapping for '{attribute_name}', skipping MQTT publish")
                continue

            sensor_config = INVERTER_SENSOR_MAP[attribute_name]
            entity_id = sensor_config["entity_id"]

            topic = self._build_sensor_message_topic(entity_id, "inverter")
            payload = json.dumps(self._build_sensor_message_payload(value, sensor_config))

            mqtt_messages.append(MqttMessage(topic=topic, payload=payload, qos=qos, retain=retain))

        return mqtt_messages

    def _build_sensor_message_topic(self, entity_id: str, base_sub_topic: str) -> str:
        return f"{self._base_topic}/{base_sub_topic}/sensor/{entity_id}"

    def _build_sensor_message_payload(self, value, sensor_config) -> dict[str, Any]:
        message = {"value": value}

        if "unit_of_measurement" in sensor_config:
            message["unit_of_measurement"] = sensor_config["unit_of_measurement"]

        return message

    def _build_discovery_messages(self, message: GrowattAnnounceMessage) -> list[MqttMessage]:
        inverter_message = self._build_inverter_discovery_messages(message)
        return [inverter_message]

    def _build_inverter_discovery_messages(self, message: GrowattAnnounceMessage) -> MqttMessage:
        discovery_message = self._discovery.build_inverter_discovery_message(
            inverter_fw_version=message.inverter_fw_version,
            inverter_serial=message.inverter_serial,
        )

        payload = json.dumps(discovery_message)
        topic = self._discovery.build_inverter_discovery_topic()
        return MqttMessage(topic=topic, payload=payload, qos=1, retain=True)

    def _build_datalogger_discovery_messages(
        self, datalogger_sw_version: str, datalogger_serial: str
    ) -> MqttMessage:
        discovery_message = self._discovery.build_datalogger_discovery_message(
            datalogger_sw_version=datalogger_sw_version,
            datalogger_serial=datalogger_serial,
        )
        payload = json.dumps(discovery_message)
        topic = self._discovery.build_datalogger_discovery_topic()
        return MqttMessage(topic=topic, payload=payload, qos=1, retain=True)
