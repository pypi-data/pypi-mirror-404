from ..filters.base import BaseFilter
from ..methods import MSMethod
from ..types import Counterparty, MetaArray


class GetCounterparties(MSMethod):
    __return__ = MetaArray[Counterparty]
    __api_method__ = "entity/counterparty"

    limit: int | None = None
    offset: int | None = None
    expand: tuple[str, ...] | str | None = None
    filters: BaseFilter | tuple[BaseFilter, ...] | None = None
