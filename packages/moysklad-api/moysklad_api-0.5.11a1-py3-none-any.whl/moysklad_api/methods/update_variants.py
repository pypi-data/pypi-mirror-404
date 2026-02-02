from ..methods.base import MSMethod
from ..types import Variant


class UpdateVariants(MSMethod[Variant]):
    __return__ = list[Variant]
    __api_method__ = "entity/variant"

    data: list[Variant]
