from shine2mqtt import PROJECT_ROOT
from shine2mqtt.growatt.protocol.messages.header import MBAPHeader

CAPTURED_FRAMES_DIR = PROJECT_ROOT / "tests" / "data" / "captured"


class CapturedFrameLoader:
    @staticmethod
    def load(message_name: str) -> tuple[list[bytes], list[MBAPHeader], list[bytes]]:
        import json

        base_path = CAPTURED_FRAMES_DIR / "shine_wifi_x" / "mic_3000tl_x"
        file_path = base_path / f"{message_name}.json"

        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        frames = [bytes.fromhex(f) for f in data["frames"]]
        headers = [MBAPHeader.fromdict(header) for header in data["headers"]]
        payloads = [bytes.fromhex(p) for p in data["payloads"]]

        return frames, headers, payloads
