from pydantic import Field

from ..filters.base import BaseFilter
from ..methods import MSMethod
from ..types import Counterparty


class GetCounterparty(MSMethod):
    __return__ = Counterparty
    __api_method__ = "entity/counterparty"

    id: str = Field(..., alias="counterparty_id")

    limit: int | None = None
    offset: int | None = None
    expand: tuple[str, ...] | str | None = None
    filters: BaseFilter | tuple[BaseFilter, ...] | None = None
