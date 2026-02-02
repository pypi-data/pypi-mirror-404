from datetime import datetime

from pydantic import Field

from ..enums import StockType
from ..filters.base import BaseFilter
from ..methods import MSMethod
from ..types import CurrentStock


class GetCurrentStock(MSMethod):
    __return__ = list[CurrentStock]
    __api_method__ = "report/stock/all/current"

    limit: int | None = None
    offset: int | None = None
    expand: tuple[str, ...] | str | None = None
    filters: BaseFilter | tuple[BaseFilter, ...] | None = None

    include: str | None = None
    changed_since: datetime | None = Field(None, alias="changedSince")
    stock_type: StockType = Field(StockType.STOCK, alias="stockType")
