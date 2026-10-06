from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.routers.orders import (
    checkout,
    get_orders,
    get_order,
)


# ============================================================
# HELPERS
# ============================================================

def current_user():
    return {
        "id": 1,
        "username": "customer1",
        "role": "CUSTOMER",
        "token": "test-jwt-token",
    }


def sample_cart():
    return {
        "cart_id": 1,
        "items": [
            {
                "cart_item_id": 101,
                "product_id": 10,
                "name": "iPhone 17",
                "price": "79999.00",
                "quantity": 2,
                "subtotal": "159998.00",
                "available": True,
            },
            {
                "cart_item_id": 102,
                "product_id": 20,
                "name": "Samsung A37",
                "price": "45999.00",
                "quantity": 1,
                "subtotal": "45999.00",
                "available": True,
            },
        ],
        "total": "205997.00",
    }


def sample_order():
    order = MagicMock()
    order.id = 1001
    order.user_id = 1
    order.status = "PLACED"
    order.total_amount = Decimal("205997.00")
    return order


# ============================================================
# CHECKOUT
# ============================================================

@patch("app.routers.orders.clear_cart")
@patch("app.routers.orders.reduce_product_stock")
@patch("app.routers.orders.get_cart")
def test_checkout_success(
    mock_get_cart,
    mock_reduce_stock,
    mock_clear_cart,
):
    db = MagicMock()

    mock_get_cart.return_value = sample_cart()

    user = current_user()

    result = checkout(
        db=db,
        current_user=user,
    )

    # Cart service called with JWT
    mock_get_cart.assert_called_once_with("test-jwt-token")

    # Order + 2 OrderItems
    assert db.add.call_count == 3

    created_order = db.add.call_args_list[0][0][0]

    assert created_order.user_id == 1
    assert created_order.status == "PLACED"
    assert created_order.total_amount == Decimal("205997.00")

    # Order ID is generated before OrderItems
    db.flush.assert_called_once()

    # Transaction committed
    db.commit.assert_called_once()

    # Order refreshed
    db.refresh.assert_called_once_with(created_order)

    # Stock reduced once for each product
    assert mock_reduce_stock.call_count == 2

    mock_reduce_stock.assert_any_call(
        product_id=10,
        quantity=2,
    )

    mock_reduce_stock.assert_any_call(
        product_id=20,
        quantity=1,
    )

    # Cart cleared after checkout
    mock_clear_cart.assert_called_once_with(
        "test-jwt-token"
    )

    assert result is created_order


@patch("app.routers.orders.clear_cart")
@patch("app.routers.orders.reduce_product_stock")
@patch("app.routers.orders.get_cart")
def test_checkout_empty_cart(
    mock_get_cart,
    mock_reduce_stock,
    mock_clear_cart,
):
    db = MagicMock()

    mock_get_cart.return_value = {
        "items": [],
        "total": 0,
    }

    with pytest.raises(HTTPException) as exc:
        checkout(
            db=db,
            current_user=current_user(),
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "Cart is empty"

    db.add.assert_not_called()
    db.commit.assert_not_called()

    mock_reduce_stock.assert_not_called()
    mock_clear_cart.assert_not_called()


@patch("app.routers.orders.clear_cart")
@patch("app.routers.orders.reduce_product_stock")
@patch("app.routers.orders.get_cart")
def test_checkout_product_not_available(
    mock_get_cart,
    mock_reduce_stock,
    mock_clear_cart,
):
    db = MagicMock()

    cart = sample_cart()

    cart["items"][0]["available"] = False

    mock_get_cart.return_value = cart

    with pytest.raises(HTTPException) as exc:
        checkout(
            db=db,
            current_user=current_user(),
        )

    assert exc.value.status_code == 400

    assert (
        exc.value.detail
        == "Product iPhone 17 is no longer available"
    )

    db.add.assert_not_called()
    db.commit.assert_not_called()

    mock_reduce_stock.assert_not_called()
    mock_clear_cart.assert_not_called()


@patch("app.routers.orders.clear_cart")
@patch("app.routers.orders.reduce_product_stock")
@patch("app.routers.orders.get_cart")
def test_checkout_calculates_total_itself(
    mock_get_cart,
    mock_reduce_stock,
    mock_clear_cart,
):
    db = MagicMock()

    cart = sample_cart()

    # Deliberately provide an incorrect total from Cart Service.
    # Order Service should NOT trust this value.
    cart["total"] = "1.00"

    mock_get_cart.return_value = cart

    checkout(
        db=db,
        current_user=current_user(),
    )

    created_order = db.add.call_args_list[0][0][0]

    # 79999 * 2 + 45999 * 1
    assert created_order.total_amount == Decimal(
        "205997.00"
    )


@patch("app.routers.orders.clear_cart")
@patch("app.routers.orders.reduce_product_stock")
@patch("app.routers.orders.get_cart")
def test_checkout_creates_order_item_snapshots(
    mock_get_cart,
    mock_reduce_stock,
    mock_clear_cart,
):
    db = MagicMock()

    mock_get_cart.return_value = sample_cart()

    checkout(
        db=db,
        current_user=current_user(),
    )

    assert db.add.call_count == 3

    first_order_item = db.add.call_args_list[1][0][0]
    second_order_item = db.add.call_args_list[2][0][0]

    assert first_order_item.product_id == 10
    assert first_order_item.product_name == "iPhone 17"
    assert first_order_item.price == Decimal("79999.00")
    assert first_order_item.quantity == 2
    assert first_order_item.subtotal == Decimal("159998.00")

    assert second_order_item.product_id == 20
    assert second_order_item.product_name == "Samsung A37"
    assert second_order_item.price == Decimal("45999.00")
    assert second_order_item.quantity == 1
    assert second_order_item.subtotal == Decimal("45999.00")


# ============================================================
# GET ORDERS
# ============================================================

def test_get_orders_success():
    db = MagicMock()

    orders = [
        sample_order(),
        sample_order(),
    ]

    (
        db.query.return_value
        .filter.return_value
        .order_by.return_value
        .all.return_value
    ) = orders

    result = get_orders(
        db=db,
        current_user=current_user(),
    )

    assert result == orders
    assert len(result) == 2

    db.query.assert_called_once()


def test_get_orders_empty():
    db = MagicMock()

    (
        db.query.return_value
        .filter.return_value
        .order_by.return_value
        .all.return_value
    ) = []

    result = get_orders(
        db=db,
        current_user=current_user(),
    )

    assert result == []


# ============================================================
# GET ONE ORDER
# ============================================================

def test_get_order_success():
    db = MagicMock()

    order = sample_order()

    db.query.return_value.filter.return_value.first.return_value = (
        order
    )

    result = get_order(
        order_id=1001,
        db=db,
        current_user=current_user(),
    )

    assert result is order
    assert result.id == 1001
    assert result.user_id == 1


def test_get_order_not_found():
    db = MagicMock()

    db.query.return_value.filter.return_value.first.return_value = (
        None
    )

    with pytest.raises(HTTPException) as exc:
        get_order(
            order_id=9999,
            db=db,
            current_user=current_user(),
        )

    assert exc.value.status_code == 404
    assert exc.value.detail == "Order not found"