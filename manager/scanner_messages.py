from enum import Enum, auto

from errors import ScannerError
from result import ResultKey


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


def from_result_key(key):
    match key:
        case ResultKey.INITIAL_SCAN:
            return ScannerMessage(MessageType.StartScan)
        case ResultKey.MANUAL_INTERACTION:
            return ScannerMessage(MessageType.RegisterInteraction)
        case ResultKey.DELETE_COOKIES:
            return ScannerMessage(MessageType.ClearCookies)
        case ResultKey.END_SCAN:
            return ScannerMessage(MessageType.StopScan)
        case other:
            raise ScannerError(f'Unexpected interaction key "{other}", aborting scan.')
