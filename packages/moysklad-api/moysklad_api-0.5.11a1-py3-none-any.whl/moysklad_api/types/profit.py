from pydantic import Field

from .assortment import Assortment
from .report import Report


class Profit(Report):
    assortment: Assortment = Field(..., alias="assortment")

    margin: float = Field(..., alias="margin")
    sales_margin: float = Field(..., alias="salesMargin")
    profit: float = Field(..., alias="profit")

    return_cost: float = Field(..., alias="returnCost")
    return_cost_sum: float = Field(..., alias="returnCostSum")
    return_price: float = Field(..., alias="returnPrice")
    return_quantity: float = Field(..., alias="returnQuantity")
    return_sum: float = Field(..., alias="returnSum")

    sell_cost: float = Field(..., alias="sellCost")
    sell_cost_sum: float = Field(..., alias="sellCostSum")
    sell_price: float = Field(..., alias="sellPrice")
    sell_quantity: float = Field(..., alias="sellQuantity")
    sell_sum: float = Field(..., alias="sellSum")
