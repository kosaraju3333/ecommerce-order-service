from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel


class OrderItemResponse(BaseModel):

    id: int
    product_id: int
    product_name: str
    price: Decimal
    quantity: int
    subtotal: Decimal

    model_config = {
        "from_attributes": True
    }


class OrderResponse(BaseModel):

    id: int
    user_id: int
    status: str
    total_amount: Decimal
    created_at: datetime

    items: list[OrderItemResponse]

    model_config = {
        "from_attributes": True
    }