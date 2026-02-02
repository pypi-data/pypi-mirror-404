from ..methods.base import MSMethod
from ..types import Product


class UpdateProducts(MSMethod[Product]):
    __return__ = list[Product]
    __api_method__ = "entity/product"

    data: list[Product]
