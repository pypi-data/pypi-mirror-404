from ..filters.base import BaseFilter
from ..methods import MSMethod
from ..types import MetaArray, Variant


class GetVariants(MSMethod):
    __return__ = MetaArray[Variant]
    __api_method__ = "entity/variant"

    limit: int | None = None
    offset: int | None = None
    expand: tuple[str, ...] | str | None = None
    filters: BaseFilter | tuple[BaseFilter, ...] | None = None
