from ..filters.base import BaseFilter
from ..methods import MSMethod
from ..types import MetaArray, Webhook


class GetWebhooks(MSMethod):
    __return__ = MetaArray[Webhook]
    __api_method__ = "entity/webhook"

    limit: int | None = None
    offset: int | None = None
    expand: tuple[str, ...] | str | None = None
    filters: BaseFilter | tuple[BaseFilter, ...] | None = None
