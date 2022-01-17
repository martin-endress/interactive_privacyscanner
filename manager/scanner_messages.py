from enum import Enum, auto


class ScannerMessage:
    def __init__(self, message_type, content=None):
        self.message_type = message_type
        self.content = content

    def __str__(self):
        return "[%s] %s" % (str(self.message_type), str(self.content))


class MessageType(Enum):
    StartScan = auto()
    StopScan = auto()
