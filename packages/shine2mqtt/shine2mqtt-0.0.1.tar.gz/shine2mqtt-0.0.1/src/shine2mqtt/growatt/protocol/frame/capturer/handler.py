from shine2mqtt.growatt.protocol.frame.capturer.capturer import CapturedFrame, FrameCapturer
from shine2mqtt.growatt.protocol.frame.capturer.sanitizer import MessageSanitizer
from shine2mqtt.growatt.protocol.frame.encoder import FrameEncoder
from shine2mqtt.growatt.protocol.messages.base import BaseMessage


class CaptureHandler:
    def __init__(self, encoder: FrameEncoder, capturer: FrameCapturer, sanitizer: MessageSanitizer):
        self.encoder = encoder
        self.capturer = capturer
        self.sanitizer = sanitizer

    def __call__(self, message: BaseMessage) -> None:
        sanitized_message = self.sanitizer.sanitize(message)

        sanitized_frame = self.encoder.encode(sanitized_message)

        payload_encoder = self.encoder.encoder_registry.get_encoder(type(sanitized_message))

        sanitized_payload = payload_encoder.encode(sanitized_message)

        captured = CapturedFrame(
            frame=sanitized_frame,
            header=sanitized_message.header,
            payload=sanitized_payload,
        )
        self.capturer.capture(captured)
