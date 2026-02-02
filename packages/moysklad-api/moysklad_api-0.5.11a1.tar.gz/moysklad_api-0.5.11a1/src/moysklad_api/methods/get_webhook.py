from pydantic import Field

from ..filters.base import BaseFilter
from ..methods import MSMethod
from ..types import Webhook


class GetWebhook(MSMethod):
    __return__ = Webhook
    __api_method__ = "entity/webhook"

    id: str = Field(..., alias="webhook_id")

    limit: int | None = None
    offset: int | None = None
    expand: tuple[str, ...] | str | None = None
    filters: BaseFilter | tuple[BaseFilter, ...] | None = None
