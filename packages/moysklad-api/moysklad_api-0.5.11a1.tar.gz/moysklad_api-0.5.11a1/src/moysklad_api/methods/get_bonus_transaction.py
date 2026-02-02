from pydantic import Field

from ..filters.base import BaseFilter
from ..methods import MSMethod
from ..types import BonusTransaction


class GetBonusTransaction(MSMethod):
    __return__ = BonusTransaction
    __api_method__ = "entity/bonustransaction"

    id: str = Field(..., alias="bonustransaction_id")
    limit: int | None = None
    offset: int | None = None
    expand: tuple[str, ...] | str | None = None
    filters: BaseFilter | tuple[BaseFilter, ...] | None = None
