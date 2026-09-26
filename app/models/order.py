from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    DateTime,
    ForeignKey
)

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Order(Base):

    __tablename__ = "orders"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Auth Service user ID.
    # No cross-service foreign key.
    user_id = Column(
        Integer,
        nullable=False,
        index=True
    )

    status = Column(
        String(30),
        nullable=False,
        default="PLACED"
    )

    total_amount = Column(
        Numeric(10, 2),
        nullable=False
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan"
    )


class OrderItem(Base):

    __tablename__ = "order_items"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    order_id = Column(
        Integer,
        ForeignKey("orders.id"),
        nullable=False
    )

    # External Product Service identifier
    product_id = Column(
        Integer,
        nullable=False
    )

    # Product snapshot
    product_name = Column(
        String(255),
        nullable=False
    )

    price = Column(
        Numeric(10, 2),
        nullable=False
    )

    quantity = Column(
        Integer,
        nullable=False
    )

    subtotal = Column(
        Numeric(10, 2),
        nullable=False
    )

    order = relationship(
        "Order",
        back_populates="items"
    )