from pydantic import Field

from ..filters.base import BaseFilter
from ..methods import MSMethod
from ..types import Demand


class GetDemand(MSMethod):
    __return__ = Demand
    __api_method__ = "entity/demand"

    id: str = Field(..., alias="demand_id")

    limit: int | None = None
    offset: int | None = None
    expand: tuple[str, ...] | str | None = None
    filters: BaseFilter | tuple[BaseFilter, ...] | None = None
