from ..filters.base import BaseFilter
from ..methods import MSMethod
from ..types import BonusTransaction, MetaArray


class GetBonusTransactions(MSMethod):
    __return__ = MetaArray[BonusTransaction]
    __api_method__ = "entity/bonustransaction"

    limit: int | None = None
    offset: int | None = None
    expand: tuple[str, ...] | str | None = None
    filters: BaseFilter | tuple[BaseFilter, ...] | None = None
