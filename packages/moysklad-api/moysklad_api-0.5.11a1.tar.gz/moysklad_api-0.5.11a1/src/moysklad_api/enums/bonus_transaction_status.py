from enum import Enum


class BonusTransactionStatus(str, Enum):
    WAIT_PROCESSING = "WAIT_PROCESSING"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"
