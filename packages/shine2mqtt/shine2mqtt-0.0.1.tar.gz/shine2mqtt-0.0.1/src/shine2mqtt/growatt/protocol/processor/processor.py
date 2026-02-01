import asyncio
from asyncio import Queue

from loguru import logger

from shine2mqtt.growatt.protocol.command import (
    BaseCommand,
    GetConfigByNameCommand,
    GetConfigByRegistersCommand,
)
from shine2mqtt.growatt.protocol.config import ConfigRegistry
from shine2mqtt.growatt.protocol.constants import (
    DATALOGGER_SW_VERSION_REGISTER,
    FunctionCode,
)
from shine2mqtt.growatt.protocol.frame.encoder import FrameEncoder
from shine2mqtt.growatt.protocol.messages import (
    BaseMessage,
    GrowattAckMessage,
    GrowattAnnounceMessage,
    GrowattBufferedDataMessage,
    GrowattDataMessage,
    GrowattGetConfigRequestMessage,
    GrowattPingMessage,
    MBAPHeader,
)
from shine2mqtt.growatt.protocol.messages.config import GrowattGetConfigResponseMessage
from shine2mqtt.growatt.protocol.processor.state import SessionState


class ProtocolProcessor:
    _GET_CONFIG_REGISTER_START = 0
    _GET_CONFIG_REGISTER_END = 61

    def __init__(
        self,
        encoder: FrameEncoder,
        incoming_messages: Queue[BaseMessage],
        outgoing_frames: Queue[bytes],
        protocol_commands: Queue[BaseCommand],
        protocol_events: Queue[BaseMessage],
    ):
        self.encoder = encoder
        self.incoming_messages = incoming_messages
        self.outgoing_frames = outgoing_frames
        self.protocol_commands = protocol_commands
        self.protocol_events = protocol_events

        self.session_state = SessionState()
        self.config_registry = ConfigRegistry()

    async def run(self):
        try:
            await asyncio.gather(self._message_processor_loop(), self._command_processor_loop())
        finally:
            logger.info("Protocol processor fully closed")

    def reset(self):
        self.session_state = SessionState()

    async def _message_processor_loop(self):
        while True:
            message: BaseMessage = await self.incoming_messages.get()

            logger.info(
                f"Processing incoming {message.header.function_code.name} ({message.header.function_code.value:#02x}) message."
            )
            logger.debug(f"Message content: {message}")

            self.session_state.update_transaction_id(message.header)

            match message:
                case GrowattPingMessage():
                    response_messages = self._handle_ping_request(message)
                case GrowattAnnounceMessage():
                    response_messages = self._handle_announce_request(message)
                case GrowattDataMessage() | GrowattBufferedDataMessage():
                    response_messages = self._handle_data_request(message)
                case GrowattAckMessage():
                    response_messages = self._handle_set_config_response()
                case GrowattGetConfigResponseMessage():
                    response_messages = self._handle_get_config_response(message)
                case _:
                    logger.error(f"No handler for message type: {type(message)}")
                    response_messages: list[BaseMessage] = []

            key = (message.header.function_code, message.header.transaction_id)

            if key in self.session_state.command_futures:
                future = self.session_state.command_futures.pop(key)
                future.set_result(message)
                logger.debug(
                    f"Resolved command future for transaction ID {message.header.transaction_id}"
                )

            for response_message in response_messages:
                logger.info(
                    f"Enqueue response {response_message.header.function_code.name} ({response_message.header.function_code.value:#02x})"
                )
                logger.debug(f"Response message content: {response_message}")

                outgoing_frame: bytes = self.encoder.encode(response_message)
                self.outgoing_frames.put_nowait(outgoing_frame)

            self.protocol_events.put_nowait(message)

    def _handle_ping_request(self, message: GrowattPingMessage) -> list[BaseMessage]:
        return [message]

    def _handle_announce_request(self, message: GrowattAnnounceMessage) -> list[BaseMessage]:
        response_messages = []

        response_messages.append(GrowattAckMessage(header=message.header, ack=True))

        if not self.session_state.is_announced():
            self.session_state.announce(message)
            # get software version first to enable device discovery
            # FIXME this should be configurable
            response_messages.append(
                self._build_get_config_request_message(
                    register_start=DATALOGGER_SW_VERSION_REGISTER,
                    register_end=DATALOGGER_SW_VERSION_REGISTER,
                )
            )
            response_messages.append(
                self._build_get_config_request_message(
                    register_start=self._GET_CONFIG_REGISTER_START,
                    register_end=self._GET_CONFIG_REGISTER_END,
                )
            )

        return response_messages

    def _build_get_config_request_message(self, register_start, register_end=None):
        if register_end is None:
            register_end = register_start

        function_code = FunctionCode.GET_CONFIG
        transaction_id = self.session_state.get_transaction_id(function_code)

        header = MBAPHeader(
            transaction_id=transaction_id,
            protocol_id=self.session_state.protocol_id,
            length=0,
            unit_id=self.session_state.unit_id,
            function_code=function_code,
        )

        return GrowattGetConfigRequestMessage(
            header, self.session_state.datalogger_serial, register_start, register_end
        )

    def _handle_data_request(self, message: GrowattDataMessage) -> list[BaseMessage]:
        return [GrowattAckMessage(header=message.header, ack=True)]

    def _handle_buffered_data_request(
        self, message: GrowattBufferedDataMessage
    ) -> list[BaseMessage]:
        return [GrowattAckMessage(header=message.header, ack=True)]

    def _handle_set_config_response(self) -> list[BaseMessage]:
        # this just ack the set config command
        return []

    def _handle_get_config_response(
        self, message: GrowattGetConfigResponseMessage
    ) -> list[BaseMessage]:
        logger.info(
            f"Received config register={message.register} name='{message.name}', value='{message.value}'"
        )
        return []

    async def _command_processor_loop(self):
        while True:
            command: BaseCommand = await self.protocol_commands.get()
            logger.debug(f"Processing command: {command}")

            if isinstance(command, GetConfigByNameCommand):
                register = self.config_registry.get_register_by_name(command.name)
                if register is None:
                    command.future.set_exception(ValueError(f"Unknown config name: {command.name}"))
                    continue
                message = self._build_get_config_request_message(
                    register_start=register,
                )
                self.session_state.store_command_future(message.header, command.future)
                frame = self.encoder.encode(message)
                self.outgoing_frames.put_nowait(frame)

            elif isinstance(command, GetConfigByRegistersCommand):
                if self.config_registry.get_register_info(command.register) is None:
                    command.future.set_exception(
                        ValueError(f"Unknown config register: {command.register}")
                    )
                    continue
                message = self._build_get_config_request_message(
                    register_start=command.register,
                )
                self.session_state.store_command_future(message.header, command.future)
                frame = self.encoder.encode(message)
                self.outgoing_frames.put_nowait(frame)
