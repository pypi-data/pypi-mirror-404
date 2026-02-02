from pydantic import Field

from ..methods import MSMethod
from ..types import Variant


class UpdateVariant(MSMethod[Variant]):
    __return__ = Variant
    __api_method__ = "entity/variant"

    id: str = Field(..., alias="variant_id")
    data: Variant
