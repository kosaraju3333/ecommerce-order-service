"""create orders and order_items tables

Revision ID: 03fec9401bf0
Revises: 
Create Date: 2026-10-07 12:32:21.292829

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '03fec9401bf0'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column(
            "total_amount",
            sa.Numeric(precision=10, scale=2),
            nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True
        ),
        sa.PrimaryKeyConstraint("id")
    )

    op.create_index(
        "ix_orders_id",
        "orders",
        ["id"],
        unique=False
    )

    op.create_index(
        "ix_orders_user_id",
        "orders",
        ["user_id"],
        unique=False
    )

    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("product_name", sa.String(length=255), nullable=False),
        sa.Column(
            "price",
            sa.Numeric(precision=10, scale=2),
            nullable=False
        ),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column(
            "subtotal",
            sa.Numeric(precision=10, scale=2),
            nullable=False
        ),

        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"]
        ),

        sa.PrimaryKeyConstraint("id")
    )

    op.create_index(
        "ix_order_items_id",
        "order_items",
        ["id"],
        unique=False
    )

def downgrade() -> None:

    op.drop_index(
        "ix_order_items_id",
        table_name="order_items"
    )

    op.drop_table("order_items")

    op.drop_index(
        "ix_orders_user_id",
        table_name="orders"
    )

    op.drop_index(
        "ix_orders_id",
        table_name="orders"
    )

    op.drop_table("orders")