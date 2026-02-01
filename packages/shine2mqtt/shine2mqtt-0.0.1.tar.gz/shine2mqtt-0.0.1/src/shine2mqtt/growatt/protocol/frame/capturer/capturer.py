import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from shine2mqtt.growatt.protocol.messages.base import MBAPHeader


@dataclass
class CapturedFrame:
    frame: bytes
    header: MBAPHeader
    payload: bytes


class FrameCapturer(ABC):
    @abstractmethod
    def capture(self, frame: CapturedFrame) -> None:
        pass


class FileFrameCapturer(FrameCapturer):
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def capture(self, frame: CapturedFrame) -> None:
        filename = self._get_filename(frame)
        filepath = self.output_dir / filename

        if filepath.exists():
            with open(filepath) as f:
                data = json.load(f)
        else:
            data = {"frames": [], "headers": [], "payloads": []}

        data["frames"].append(frame.frame.hex())
        data["headers"].append(frame.header.asdict())
        data["payloads"].append(frame.payload.hex())

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    def _get_filename(self, frame: CapturedFrame) -> str:
        function_name = frame.header.function_code.name.lower()
        return f"{function_name}_message.json"
