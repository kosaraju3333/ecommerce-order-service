from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.order import Order, OrderItem
from app.schemas.order import OrderResponse
from app.utils.dependencies import get_current_user
from app.clients.cart_client import get_cart, clear_cart
from app.clients.product_client import reduce_product_stock


router = APIRouter(
    prefix="/api/orders",
    tags=["Orders"]
)


# ============================================================
# CHECKOUT / PLACE ORDER
# ============================================================

@router.post(
    "/checkout",
    response_model=OrderResponse
)
def checkout(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    user_id = current_user["id"]
    token = current_user["token"]

    # --------------------------------------------------------
    # 1. Get customer's cart from Cart Service
    # --------------------------------------------------------

    cart = get_cart(token)

    cart_items = cart.get("items", [])

    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty"
        )

    # --------------------------------------------------------
    # 2. Validate all cart items
    # --------------------------------------------------------

    for item in cart_items:

        if item.get("available") is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Product {item['name']} "
                    "is no longer available"
                )
            )

    # --------------------------------------------------------
    # 3. Calculate total ourselves
    # --------------------------------------------------------

    total_amount = Decimal("0.00")

    for item in cart_items:

        price = Decimal(
            str(item["price"])
        )

        quantity = item["quantity"]

        subtotal = price * quantity

        total_amount += subtotal

    # --------------------------------------------------------
    # 4. Create order
    # --------------------------------------------------------

    order = Order(
        user_id=user_id,
        status="PLACED",
        total_amount=total_amount
    )

    db.add(order)

    # flush gives us order.id without committing yet
    db.flush()

    # --------------------------------------------------------
    # 5. Create order item snapshots
    # --------------------------------------------------------

    for item in cart_items:

        price = Decimal(
            str(item["price"])
        )

        quantity = item["quantity"]

        subtotal = price * quantity

        order_item = OrderItem(
            order_id=order.id,
            product_id=item["product_id"],
            product_name=item["name"],
            price=price,
            quantity=quantity,
            subtotal=subtotal
        )

        db.add(order_item)

    # --------------------------------------------------------
    # 6. Commit order + order items
    # --------------------------------------------------------

    db.commit()
    db.refresh(order)

    # Reduce inventory for purchased products
    for item in cart_items:

        reduce_product_stock(
            product_id=item["product_id"],
            quantity=item["quantity"]
        )


    # Clear cart only AFTER order was successfully created
    clear_cart(token)

    return order


# ============================================================
# GET LOGGED-IN USER'S ORDERS
# ============================================================

@router.get(
    "/",
    response_model=list[OrderResponse]
)
def get_orders(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    user_id = current_user["id"]

    return (
        db.query(Order)
        .filter(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
        .all()
    )


# ============================================================
# GET ONE ORDER
# ============================================================

@router.get(
    "/{order_id}",
    response_model=OrderResponse
)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    user_id = current_user["id"]

    order = (
        db.query(Order)
        .filter(
            Order.id == order_id,
            Order.user_id == user_id
        )
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    return order