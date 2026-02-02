from pydantic import Field

from ..methods.base import MSMethod
from ..types.token import Token


class GetToken(MSMethod[Token]):
    __return__ = Token
    __api_method__ = "security/token"

    username: str = Field(..., alias="username")
    password: str = Field(..., alias="password")
