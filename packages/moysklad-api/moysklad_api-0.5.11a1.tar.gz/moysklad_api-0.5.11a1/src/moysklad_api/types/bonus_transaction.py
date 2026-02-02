from pydantic import Field

from ..enums.bonus_transaction_category_type import BonusTransactionCategoryType
from ..enums.bonus_transaction_status import BonusTransactionStatus
from ..enums.bonus_transaction_type import BonusTransactionType
from .agent import Agent
from .bonus_program import BonusProgram
from .entity import Entity
from .group import Group
from .organization import Organization
from .owner import Owner
from .parent_document import ParentDocument


class BonusTransaction(Entity):
    id: str | None = Field(None, alias="id")
    account_id: str | None = Field(None, alias="accountId")
    agent: Agent | None = Field(None, alias="agent")
    bonus_program: BonusProgram | None = Field(None, alias="bonusProgram")
    applicable: bool | None = Field(None, alias="applicable")
    bonus_value: int | None = Field(None, alias="bonusValue")
    category_type: BonusTransactionCategoryType | None = Field(None, alias="categoryType")
    transaction_status: BonusTransactionStatus | None = Field(None, alias="transactionStatus")
    transaction_type: BonusTransactionType | None = Field(None, alias="transactionType")
    code: str | None = Field(None, alias="code")
    description: str | None = Field(None, alias="description")
    external_code: str | None = Field(None, alias="externalCode")
    name: str | None = Field(None, alias="name")
    created: str | None = Field(None, alias="created")
    updated: str | None = Field(None, alias="updated")
    execution_date: str | None = Field(None, alias="executionDate")
    moment: str | None = Field(None, alias="moment")
    group: Group | None = Field(None, alias="group")
    owner: Owner | None = Field(None, alias="owner")
    organization: Organization | None = Field(None, alias="organization")
    parent_document: ParentDocument | None = Field(None, alias="parentDocument")
    shared: bool | None = Field(None, alias="shared")
    updated_by: str | None = Field(None, alias="updatedBy")
