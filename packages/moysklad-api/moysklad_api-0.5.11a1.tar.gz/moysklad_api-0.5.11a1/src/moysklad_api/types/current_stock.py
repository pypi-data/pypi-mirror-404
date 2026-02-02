from pydantic import BaseModel, Field


class CurrentStock(BaseModel):
    assortment_id: str = Field(..., alias="assortmentId")
    stock: float | None = Field(None, alias="stock")
    quantity: float | None = Field(None, alias="quantity")
    free_stock: float | None = Field(None, alias="freeStock")
    store_id: str | None = Field(None, alias="storeId")
    reserve: float | None = Field(None, alias="reserve")
    in_transit: float | None = Field(None, alias="inTransit")
