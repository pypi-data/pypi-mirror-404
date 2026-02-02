from pydantic import Field

from ..methods.base import MSMethod
from ..types import Product


class UpdateProduct(MSMethod[Product]):
    __return__ = Product
    __api_method__ = "entity/product"

    id: str = Field(..., alias="product_id")
    data: Product
