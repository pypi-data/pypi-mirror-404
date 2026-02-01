from asyncio import Future
from dataclasses import dataclass, field

from shine2mqtt.growatt.protocol.constants import FunctionCode
from shine2mqtt.growatt.protocol.messages.announce import GrowattAnnounceMessage
from shine2mqtt.growatt.protocol.messages.header import MBAPHeader


@dataclass
class SessionState:
    announced: bool = False
    protocol_id: int = 0
    unit_id: int = 0
    datalogger_serial: str = ""

    last_transaction_id: dict[FunctionCode, int] = field(
        default_factory=lambda: {
            FunctionCode.PING: 0,
            FunctionCode.ANNOUNCE: 0,
            FunctionCode.DATA: 0,
            FunctionCode.BUFFERED_DATA: 0,
            FunctionCode.SET_CONFIG: 0,
            FunctionCode.GET_CONFIG: 0,
        }
    )
    command_futures: dict[tuple[FunctionCode, int], Future] = field(default_factory=dict)

    def is_announced(self) -> bool:
        return self.announced

    def announce(self, message: GrowattAnnounceMessage) -> None:
        self.announced = True
        self.protocol_id = message.header.protocol_id
        self.unit_id = message.header.unit_id
        self.datalogger_serial = message.datalogger_serial

    def get_transaction_id(self, function_code: FunctionCode) -> int:
        self.last_transaction_id[function_code] += 1
        return self.last_transaction_id[function_code]

    def update_transaction_id(self, header: MBAPHeader) -> None:
        self.last_transaction_id[header.function_code] = header.transaction_id

    def store_command_future(self, header: MBAPHeader, future: Future) -> None:
        self.command_futures[(header.function_code, header.transaction_id)] = future
