from enum import Enum


class GroupBy(str, Enum):
    PRODUCT = "product"
    VARIANT = "variant"
    CONSIGNMENT = "consignment"
