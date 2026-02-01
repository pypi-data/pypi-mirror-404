from dataclasses import dataclass

from shine2mqtt.growatt.protocol.constants import FunctionCode


@dataclass
class MBAPHeader:
    transaction_id: int
    protocol_id: int
    length: int
    unit_id: int
    function_code: FunctionCode

    def asdict(self) -> dict:
        """Serialize header to dict with function_code as hex value"""
        return {
            "transaction_id": self.transaction_id,
            "protocol_id": self.protocol_id,
            "length": self.length,
            "unit_id": self.unit_id,
            "function_code": self.function_code.value,
        }

    @classmethod
    def fromdict(cls, data: dict) -> "MBAPHeader":
        """Deserialize header from dict with function_code as hex value"""
        return cls(
            transaction_id=data["transaction_id"],
            protocol_id=data["protocol_id"],
            length=data["length"],
            unit_id=data["unit_id"],
            function_code=FunctionCode(data["function_code"]),
        )
