from ..filters.base import BaseFilter
from ..methods import MSMethod
from ..types import Demand, MetaArray


class GetDemands(MSMethod):
    __return__ = MetaArray[Demand]
    __api_method__ = "entity/demand"

    limit: int | None = None
    offset: int | None = None
    expand: tuple[str, ...] | str | None = None
    filters: BaseFilter | tuple[BaseFilter, ...] | None = None
