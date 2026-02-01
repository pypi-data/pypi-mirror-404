from shine2mqtt.growatt.protocol.encoders import BaseEncoder
from shine2mqtt.growatt.protocol.messages import GrowattPingMessage


class PingPayloadEncoder(BaseEncoder[GrowattPingMessage]):
    def __init__(self):
        super().__init__(GrowattPingMessage)

    def encode(self, message: GrowattPingMessage) -> bytes:
        payload = self.encode_string(message.datalogger_serial, 10)
        return payload
