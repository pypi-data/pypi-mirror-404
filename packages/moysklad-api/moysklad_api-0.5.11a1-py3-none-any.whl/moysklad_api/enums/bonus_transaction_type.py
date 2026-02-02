from enum import Enum


class BonusTransactionType(str, Enum):
    EARNING = "EARNING"
    SPENDING = "SPENDING"
