from unittest.mock import patch

from fastapi import HTTPException

from app.models.order import Order, OrderItem


# ============================================================
# ROOT / HEALTH
# ============================================================


def test_root(client):

    response = client.get("/")

    assert response.status_code == 200

    assert response.json() == {
        "service": "order-service",
        "status": "running",
    }


def test_health(client):

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "UP"


# ============================================================
# AUTHENTICATION
# ============================================================


def test_orders_without_token(client):

    response = client.get("/api/orders/")

    assert response.status_code in (401, 403)


def test_orders_invalid_token(client):

    response = client.get(
        "/api/orders/",
        headers={
            "Authorization": "Bearer invalid.jwt.token"
        },
    )

    assert response.status_code == 401


# ============================================================
# CHECKOUT
# ============================================================


def test_checkout_success(
    client,
    customer_headers,
    sample_cart,
    db,
):

    with (
        patch(
            "app.routers.orders.get_cart",
            return_value=sample_cart,
        ) as mock_get_cart,
        patch(
            "app.routers.orders.reduce_product_stock",
            return_value={
                "message": "Stock reduced successfully"
            },
        ) as mock_reduce,
        patch(
            "app.routers.orders.clear_cart",
            return_value={
                "message": "Cart cleared successfully"
            },
        ) as mock_clear,
    ):

        response = client.post(
            "/api/orders/checkout",
            headers=customer_headers,
        )

    assert response.status_code == 200

    data = response.json()

    assert data["user_id"] == 1
    assert data["status"] == "PLACED"

    # 1000 * 2 + 2000 * 1
    assert float(data["total_amount"]) == 4000.00

    assert len(data["items"]) == 2

    assert data["items"][0]["product_id"] == 101
    assert data["items"][0]["product_name"] == "iPhone Test"
    assert data["items"][0]["quantity"] == 2

    assert data["items"][1]["product_id"] == 102

    # Cart Service called once
    mock_get_cart.assert_called_once()

    # Product Service called once per cart item
    assert mock_reduce.call_count == 2

    mock_reduce.assert_any_call(
        product_id=101,
        quantity=2,
    )

    mock_reduce.assert_any_call(
        product_id=102,
        quantity=1,
    )

    # Cart cleared after checkout
    mock_clear.assert_called_once()

    # Verify DB
    orders = db.query(Order).all()
    items = db.query(OrderItem).all()

    assert len(orders) == 1
    assert len(items) == 2


def test_checkout_empty_cart(
    client,
    customer_headers,
):

    empty_cart = {
        "items": [],
        "total": 0,
    }

    with patch(
        "app.routers.orders.get_cart",
        return_value=empty_cart,
    ):

        response = client.post(
            "/api/orders/checkout",
            headers=customer_headers,
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Cart is empty"


def test_checkout_unavailable_product(
    client,
    customer_headers,
):

    cart = {
        "items": [
            {
                "product_id": 101,
                "name": "Deleted Product",
                "price": "1000.00",
                "quantity": 1,
                "available": False,
            }
        ]
    }

    with patch(
        "app.routers.orders.get_cart",
        return_value=cart,
    ):

        response = client.post(
            "/api/orders/checkout",
            headers=customer_headers,
        )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "Product Deleted Product is no longer available"
    )


def test_checkout_recalculates_total(
    client,
    customer_headers,
):

    # Cart claims total is 1.00.
    # Order Service should NOT trust it.
    cart = {
        "items": [
            {
                "product_id": 101,
                "name": "Product A",
                "price": "100.00",
                "quantity": 3,
                "available": True,
            }
        ],
        "total": "1.00",
    }

    with (
        patch(
            "app.routers.orders.get_cart",
            return_value=cart,
        ),
        patch(
            "app.routers.orders.reduce_product_stock",
            return_value={},
        ),
        patch(
            "app.routers.orders.clear_cart",
            return_value={},
        ),
    ):

        response = client.post(
            "/api/orders/checkout",
            headers=customer_headers,
        )

    assert response.status_code == 200

    # Correct value is 100 * 3
    assert float(response.json()["total_amount"]) == 300.00


def test_checkout_cart_service_unavailable(
    client,
    customer_headers,
):

    with patch(
        "app.routers.orders.get_cart",
        side_effect=HTTPException(
            status_code=503,
            detail="Cart service is unavailable",
        ),
    ):

        response = client.post(
            "/api/orders/checkout",
            headers=customer_headers,
        )

    assert response.status_code == 503

    assert (
        response.json()["detail"]
        == "Cart service is unavailable"
    )


# ============================================================
# GET ORDERS
# ============================================================


def test_get_orders_empty(
    client,
    customer_headers,
):

    response = client.get(
        "/api/orders/",
        headers=customer_headers,
    )

    assert response.status_code == 200
    assert response.json() == []


def test_get_logged_in_users_orders(
    client,
    customer_headers,
    order,
    second_customer_order,
):

    response = client.get(
        "/api/orders/",
        headers=customer_headers,
    )

    assert response.status_code == 200

    data = response.json()

    # Customer 1 must only see own order.
    assert len(data) == 1

    assert data[0]["id"] == order.id
    assert data[0]["user_id"] == 1

    assert len(data[0]["items"]) == 1


# ============================================================
# GET ONE ORDER
# ============================================================


def test_get_order(
    client,
    customer_headers,
    order,
):

    response = client.get(
        f"/api/orders/{order.id}",
        headers=customer_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == order.id
    assert data["user_id"] == 1
    assert data["status"] == "PLACED"

    assert len(data["items"]) == 1

    assert (
        data["items"][0]["product_name"]
        == "iPhone Test"
    )


def test_get_nonexistent_order(
    client,
    customer_headers,
):

    response = client.get(
        "/api/orders/99999",
        headers=customer_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"


def test_customer_cannot_access_another_users_order(
    client,
    customer_headers,
    second_customer_order,
):

    response = client.get(
        f"/api/orders/{second_customer_order.id}",
        headers=customer_headers,
    )

    # Don't expose whether another customer's
    # order actually exists.
    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"