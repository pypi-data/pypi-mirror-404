from pydantic import Field

from ..filters.base import BaseFilter
from ..methods import MSMethod
from ..types import Product


class GetProduct(MSMethod):
    __return__ = Product
    __api_method__ = "entity/product"

    id: str = Field(..., alias="product_id")

    limit: int | None = None
    offset: int | None = None
    expand: tuple[str, ...] | str | None = None
    filters: BaseFilter | tuple[BaseFilter, ...] | None = None
