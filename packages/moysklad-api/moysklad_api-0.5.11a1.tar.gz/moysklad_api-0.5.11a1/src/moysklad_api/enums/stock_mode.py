from enum import Enum


class StockMode(str, Enum):
    ALL = "all"
    POSITIVE_ONLY = "positiveOnly"
    NEGATIVE_ONLY = "negativeOnly"
    EMPTY = "empty"
    NON_EMPTY = "nonEmpty"
    UNDER_MINIMUM = "underMinimum"
