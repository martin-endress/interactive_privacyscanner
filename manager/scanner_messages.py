from enum import Enum, auto


class ScannerMessage:
    def __init__(self, message_type, content=None):
        self.message_type = message_type
        self.content = content

    def __str__(self):
        return f"[{self.message_type}] {str(self.content or '')}"


class MessageType(Enum):
    StartScan = auto()
    RegisterInteraction = auto()
    StopScan = auto()
    ClearCookies = auto()
    TakeScreenshot = auto()
    PerformUserInteraction = auto()
