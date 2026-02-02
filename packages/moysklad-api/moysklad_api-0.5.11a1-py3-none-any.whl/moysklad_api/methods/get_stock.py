from pydantic import Field

from ..enums import QuantityMode, StockMode
from ..filters.base import BaseFilter
from ..methods import MSMethod
from ..types import MetaArray, Stock


class GetStock(MSMethod):
    __return__ = MetaArray[Stock]
    __api_method__ = "report/stock/all"

    limit: int | None = None
    offset: int | None = None
    expand: tuple[str, ...] | str | None = None
    filters: BaseFilter | tuple[BaseFilter, ...] | None = None

    stock_mode: StockMode = Field(
        default=StockMode.ALL,
        alias="stockMode",
    )
    quantity_mode: QuantityMode = Field(
        default=QuantityMode.NON_EMPTY,
        alias="quantityMode",
    )
