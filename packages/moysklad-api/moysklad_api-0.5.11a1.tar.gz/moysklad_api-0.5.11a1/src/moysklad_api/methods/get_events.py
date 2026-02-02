from pydantic import Field

from ..filters.base import BaseFilter
from ..methods import GetAudit
from ..types import Event, MetaArray


class GetEvents(GetAudit):
    __return__ = MetaArray[Event]
    __api_method__ = "audit/{id}/events"

    id: str = Field(..., alias="audit_id")

    limit: int | None = None
    offset: int | None = None
    expand: tuple[str, ...] | str | None = None
    filters: BaseFilter | tuple[BaseFilter, ...] | None = None
