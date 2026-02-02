from pydantic import Field

from .entity import Entity
from .meta import Meta


class Error(Entity):
    error: str = Field(..., alias="error")
    parameter: str = Field(None, alias="parameter")
    code: int = Field(None, alias="code")
    error_message: str = Field(None, alias="error_message")
    more_info: str = Field(None, alias="moreInfo")
    line: int = Field(None, alias="line")
    column: int = Field(None, alias="column")
    dependencies: str = Field(None, alias="dependencies")
    meta: Meta | None = None
