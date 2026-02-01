from dataclasses import dataclass

from shine2mqtt.growatt.protocol.constants import CONFIG_REGISTERS


@dataclass(frozen=True)
class RegisterInfo:
    name: str
    description: str
    fmt: str


class ConfigRegistry:
    def __init__(self, registers: dict[int, dict] = CONFIG_REGISTERS):
        self._registers = registers

    def get_register_by_name(self, name: str) -> int | None:
        for register, info in self._registers.items():
            if info.get("name") == name:
                return register
        return None

    def get_register_info(self, register: int) -> RegisterInfo | None:
        info = self._registers.get(register)
        if info is None:
            return None
        return RegisterInfo(
            name=info["name"],
            description=info["description"],
            fmt=info["fmt"],
        )

    def has_register(self, register: int) -> bool:
        return register in self._registers
