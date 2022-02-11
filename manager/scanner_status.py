from enum import Enum, auto


class ScannerStatus(Enum):
    AwaitingInteraction = auto()
    RegisterInteraction = auto()
    ScanComplete = auto()

    def validate_status(self, status):
        if status == self:
            raise ValueError()
