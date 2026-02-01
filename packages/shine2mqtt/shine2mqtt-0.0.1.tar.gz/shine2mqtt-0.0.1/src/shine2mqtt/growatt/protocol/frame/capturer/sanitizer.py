from dataclasses import replace

from shine2mqtt.growatt.protocol.messages.announce import GrowattAnnounceMessage
from shine2mqtt.growatt.protocol.messages.base import BaseMessage
from shine2mqtt.growatt.protocol.messages.config import GrowattGetConfigResponseMessage
from shine2mqtt.growatt.protocol.messages.data import GrowattBufferedDataMessage, GrowattDataMessage
from shine2mqtt.growatt.protocol.messages.ping import GrowattPingMessage

DUMMY_DATALOGGER_SERIAL = "XGDABCDEFG"
DUMMY_INVERTER_SERIAL = "MLG0A12345"
DUMMY_IP_ADDRESS = "192.168.1.100"
DUMMY_MAC_ADDRESS = "00:11:22:33:44:55"
DUMMY_SERVER_IP_ADDRESS = "192.168.1.200"
DUMMY_WIFI_SSID = "MyWiFiNetwork"
DUMMY_WIFI_PASSWORD = "MySecretPassword"


class MessageSanitizer:
    def sanitize(self, message: BaseMessage) -> BaseMessage:
        match message:
            case GrowattAnnounceMessage():
                return replace(
                    message,
                    datalogger_serial=DUMMY_DATALOGGER_SERIAL,
                    inverter_serial=DUMMY_INVERTER_SERIAL,
                )
            case GrowattBufferedDataMessage() | GrowattDataMessage():
                return replace(
                    message,
                    datalogger_serial=DUMMY_DATALOGGER_SERIAL,
                    inverter_serial=DUMMY_INVERTER_SERIAL,
                )
            case GrowattPingMessage():
                return replace(
                    message,
                    datalogger_serial=DUMMY_DATALOGGER_SERIAL,
                )
            case GrowattGetConfigResponseMessage():
                return self._sanitize_get_config_response(message)

        return message

    def _sanitize_get_config_response(
        self, message: GrowattGetConfigResponseMessage
    ) -> GrowattGetConfigResponseMessage:
        sanitized_registers = {
            "ip_address": DUMMY_IP_ADDRESS,
            "mac_address": DUMMY_MAC_ADDRESS,
            "server_ip_address": DUMMY_SERVER_IP_ADDRESS,
            "wifi_ssid": DUMMY_WIFI_SSID,
            "wifi_password": DUMMY_WIFI_PASSWORD,
        }
        if message.name not in sanitized_registers:
            return message

        sanitized_value = sanitized_registers[message.name]

        sanitized_data = sanitized_value.encode("ascii")
        length_difference = len(sanitized_data) - len(message.data)

        return replace(
            message,
            datalogger_serial=DUMMY_DATALOGGER_SERIAL,
            length=message.length + length_difference,
            data=sanitized_data,
            value=sanitized_value,
        )
