from pydantic import Field

from ..filters.base import BaseFilter
from ..methods import MSMethod
from ..types import Audit


class GetAudit(MSMethod):
    __return__ = Audit
    __api_method__ = "audit"

    id: str = Field(..., alias="audit_id")
    limit: int | None = None
    offset: int | None = None
    expand: tuple[str, ...] | str | None = None
    filters: BaseFilter | tuple[BaseFilter, ...] | None = None
