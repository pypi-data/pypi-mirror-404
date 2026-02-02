from datetime import date, datetime

from pydantic import Field

from ..filters.base import BaseFilter
from ..methods import MSMethod
from ..types import MetaArray, Profit


class GetProfit(MSMethod):
    __return__ = MetaArray[Profit]
    __api_method__ = "report/profit/by{type}"

    limit: int | None = None
    offset: int | None = None
    expand: tuple[str, ...] | str | None = None
    filters: BaseFilter | tuple[BaseFilter, ...] | None = None

    moment_from: str | date | datetime | None = Field(
        default=None,
        alias="momentFrom",
    )
    moment_to: str | date | datetime | None = Field(
        default=None,
        alias="momentTo",
    )
