from unittest.mock import Mock, patch

import httpx
import pytest

from fastapi import HTTPException

from app.clients.product_client import reduce_product_stock


def test_reduce_stock_success():

    response = Mock()

    response.status_code = 200

    response.json.return_value = {
        "message": "Stock reduced successfully",
        "product_id": 101,
        "quantity_reduced": 2,
        "remaining_stock": 8,
    }

    with patch(
        "app.clients.product_client.httpx.put",
        return_value=response,
    ):

        result = reduce_product_stock(
            product_id=101,
            quantity=2,
        )

    assert result["product_id"] == 101
    assert result["quantity_reduced"] == 2


def test_reduce_stock_product_not_found():

    response = Mock()
    response.status_code = 404

    with patch(
        "app.clients.product_client.httpx.put",
        return_value=response,
    ):

        with pytest.raises(HTTPException) as exc:

            reduce_product_stock(
                product_id=99999,
                quantity=1,
            )

    assert exc.value.status_code == 404

    assert (
        exc.value.detail
        == "Product 99999 not found"
    )


def test_reduce_stock_insufficient_stock():

    response = Mock()
    response.status_code = 400

    response.json.return_value = {
        "detail": "Insufficient stock"
    }

    with patch(
        "app.clients.product_client.httpx.put",
        return_value=response,
    ):

        with pytest.raises(HTTPException) as exc:

            reduce_product_stock(
                product_id=101,
                quantity=100,
            )

    assert exc.value.status_code == 400
    assert exc.value.detail == "Insufficient stock"


def test_reduce_stock_bad_gateway():

    response = Mock()
    response.status_code = 500

    with patch(
        "app.clients.product_client.httpx.put",
        return_value=response,
    ):

        with pytest.raises(HTTPException) as exc:

            reduce_product_stock(
                product_id=101,
                quantity=1,
            )

    assert exc.value.status_code == 502


def test_product_service_unavailable():

    with patch(
        "app.clients.product_client.httpx.put",
        side_effect=httpx.RequestError(
            "Connection failed"
        ),
    ):

        with pytest.raises(HTTPException) as exc:

            reduce_product_stock(
                product_id=101,
                quantity=1,
            )

    assert exc.value.status_code == 503