from ..filters.base import BaseFilter
from ..methods import MSMethod
from ..types import MetaArray, Product


class GetProducts(MSMethod):
    __return__ = MetaArray[Product]
    __api_method__ = "entity/product"

    limit: int | None = None
    offset: int | None = None
    expand: tuple[str, ...] | str | None = None
    filters: BaseFilter | tuple[BaseFilter, ...] | None = None
