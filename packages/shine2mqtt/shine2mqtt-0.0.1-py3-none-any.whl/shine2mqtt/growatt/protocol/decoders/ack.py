from shine2mqtt.growatt.protocol.constants import ACK
from shine2mqtt.growatt.protocol.decoders.base import MessageDecoder
from shine2mqtt.growatt.protocol.messages.ack import GrowattAckMessage
from shine2mqtt.growatt.protocol.messages.base import MBAPHeader


class AckMessageResponseDecoder(MessageDecoder[GrowattAckMessage]):
    def decode(self, header: MBAPHeader, payload: bytes) -> GrowattAckMessage:
        ack = payload == ACK
        return GrowattAckMessage(header=header, ack=ack)
