from enum import Enum, auto


class ScannerMessage:
    def __init__(self, message_type, content=None):
        self.message_type = message_type
        self.content = content


class MessageType(Enum):
    StartScan = auto()
    StopScan = auto()
