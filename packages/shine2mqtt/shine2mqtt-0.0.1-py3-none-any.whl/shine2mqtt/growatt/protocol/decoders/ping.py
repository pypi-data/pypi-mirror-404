from shine2mqtt.growatt.protocol.decoders.base import MessageDecoder
from shine2mqtt.growatt.protocol.messages.base import MBAPHeader
from shine2mqtt.growatt.protocol.messages.ping import GrowattPingMessage


class PingRequestDecoder(MessageDecoder[GrowattPingMessage]):
    def decode(self, header: MBAPHeader, payload: bytes) -> GrowattPingMessage:
        variables = {
            "datalogger_serial": self.read_str(payload, 0, 10),
        }

        return GrowattPingMessage(
            header=header,
            **variables,
        )
