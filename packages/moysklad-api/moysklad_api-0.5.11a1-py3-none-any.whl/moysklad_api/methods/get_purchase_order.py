from pydantic import Field

from ..filters.base import BaseFilter
from ..methods import MSMethod
from ..types import PurchaseOrder


class GetPurchaseOrder(MSMethod):
    __return__ = PurchaseOrder
    __api_method__ = "entity/purchaseorder"

    id: str = Field(..., alias="purchaseorder_id")
    limit: int | None = None
    offset: int | None = None
    expand: tuple[str, ...] | str | None = None
    filters: BaseFilter | tuple[BaseFilter, ...] | None = None
