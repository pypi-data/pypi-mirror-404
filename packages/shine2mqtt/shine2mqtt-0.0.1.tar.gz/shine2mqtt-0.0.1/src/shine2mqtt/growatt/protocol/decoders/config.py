import struct

from loguru import logger

from shine2mqtt.growatt.protocol.config import ConfigRegistry
from shine2mqtt.growatt.protocol.decoders.ack import (
    AckMessageResponseDecoder,
    MessageDecoder,
)
from shine2mqtt.growatt.protocol.messages import (
    GrowattGetConfigRequestMessage,
    GrowattGetConfigResponseMessage,
    GrowattSetConfigRequestMessage,
    MBAPHeader,
)


class SetConfigResponseDecoder(AckMessageResponseDecoder):
    pass


class GetConfigRequestDecoder(MessageDecoder[GrowattGetConfigRequestMessage]):
    """Decoder for GET_CONFIG requests (server → client)"""

    def decode(self, header: MBAPHeader, payload: bytes) -> GrowattGetConfigRequestMessage:
        datalogger_serial = self.read_str(payload, 0, 10)
        register_start = self.read_u16(payload, 10)
        register_end = self.read_u16(payload, 12)

        return GrowattGetConfigRequestMessage(
            header=header,
            datalogger_serial=datalogger_serial,
            register_start=register_start,
            register_end=register_end,
        )


class SetConfigRequestDecoder(MessageDecoder[GrowattSetConfigRequestMessage]):
    """Decoder for SET_CONFIG requests (server → client)"""

    def __init__(self, config_registry: ConfigRegistry | None = None):
        self.config_registry = config_registry if config_registry else ConfigRegistry()

    def decode(self, header: MBAPHeader, payload: bytes) -> GrowattSetConfigRequestMessage:
        datalogger_serial = self.read_str(payload, 0, 10)
        register = self.read_u16(payload, 30)
        length = self.read_u16(payload, 32)

        # Decode value based on register config
        config = self.config_registry.get_register_info(register)
        if config is None:
            # Unknown register, read as bytes
            value = self.read_str(payload, 34, length)
        elif config.fmt == "s":
            value = self.read_str(payload, 34, length)
        elif config.fmt == "B":
            value = self.read_u8(payload, 34)
        elif config.fmt == "H":
            value = self.read_u16(payload, 34)
        else:
            value = self.read_str(payload, 34, length)

        return GrowattSetConfigRequestMessage(
            header=header,
            datalogger_serial=datalogger_serial,
            register=register,
            length=length,
            value=value,
        )


class GetConfigResponseDecoder(MessageDecoder[GrowattGetConfigResponseMessage]):
    """Decoder for GET_CONFIG responses (client → server)"""

    def __init__(self, config_registry: ConfigRegistry | None = None):
        self.config_registry = config_registry if config_registry else ConfigRegistry()

    def decode(self, header: MBAPHeader, payload: bytes) -> GrowattGetConfigResponseMessage:
        datalogger_serial = self.read_str(payload, 0, 10)
        register = self.read_u16(payload, 30)
        length = self.read_u16(payload, 32)

        try:
            data = payload[34 : 34 + length]
        except struct.error:
            logger.error(
                f"Could not unpack get config response data for register {register} with length {length} and data length {len(data)}"
            )
            data = b""

        config = self.config_registry.get_register_info(register)

        if config is None:
            return GrowattGetConfigResponseMessage(
                header=header,
                datalogger_serial=datalogger_serial,
                register=register,
                length=length,
                data=data,
            )

        if config.fmt == "s":
            value = self.read_str(payload, 34, length)
        elif config.fmt == "B":
            value = self.read_u8(payload, 34)
        elif config.fmt == "H":
            value = self.read_u16(payload, 34)
        elif config.fmt == "I":
            value = self.read_u32(payload, 34)

        return GrowattGetConfigResponseMessage(
            header=header,
            datalogger_serial=datalogger_serial,
            register=register,
            length=length,
            data=data,
            name=config.name,
            description=config.description,
            value=value,
        )
