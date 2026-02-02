from enum import Enum


class StockType(str, Enum):
    STOCK = "stock"
    FREE_STOCK = "freeStock"
    QUANTITY = "quantity"
    RESERVE = "reserve"
    IN_TRANSIT = "inTransit"
