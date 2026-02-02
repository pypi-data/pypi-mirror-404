from pydantic import Field

from ..filters.base import BaseFilter
from ..methods import MSMethod
from ..types import MetaArray, PurchaseOrder


class GetPurchaseOrders(MSMethod):
    __return__ = MetaArray[PurchaseOrder]
    __api_method__ = "entity/purchaseorder"

    limit: int | None = None
    offset: int | None = None
    expand: tuple[str, ...] | str | None = None
    filters: BaseFilter | tuple[BaseFilter, ...] | None = None

    search: str | None = Field(
        default=None,
        alias="search",
    )
