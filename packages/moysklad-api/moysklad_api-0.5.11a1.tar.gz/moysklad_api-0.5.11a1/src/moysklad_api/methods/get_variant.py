from pydantic import Field

from ..filters.base import BaseFilter
from ..methods import MSMethod
from ..types import Variant


class GetVariant(MSMethod):
    __return__ = Variant
    __api_method__ = "entity/variant"

    id: str = Field(..., alias="variant_id")

    limit: int | None = None
    offset: int | None = None
    expand: tuple[str, ...] | str | None = None
    filters: BaseFilter | tuple[BaseFilter, ...] | None = None
