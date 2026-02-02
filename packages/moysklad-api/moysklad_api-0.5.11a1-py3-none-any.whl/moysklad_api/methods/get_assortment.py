from pydantic import Field

from ..enums import GroupBy
from ..filters.base import BaseFilter
from ..methods import MSMethod
from ..types import Assortment, MetaArray


class GetAssortment(MSMethod):
    __return__ = MetaArray[Assortment]
    __api_method__ = "entity/assortment"

    limit: int | None = None
    offset: int | None = None
    expand: tuple[str, ...] | str | None = None
    filters: BaseFilter | tuple[BaseFilter, ...] | None = None

    group_by: GroupBy | None = Field(
        default=None,
        alias="groupBy",
    )
