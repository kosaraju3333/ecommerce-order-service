from unittest.mock import Mock, patch

import httpx
import pytest

from fastapi import HTTPException

from app.clients.cart_client import (
    get_cart,
    clear_cart,
)


def test_get_cart_success():

    response = Mock()

    response.status_code = 200
    response.json.return_value = {
        "items": [],
        "total": 0,
    }

    with patch(
        "app.clients.cart_client.httpx.get",
        return_value=response,
    ):

        result = get_cart("test-token")

    assert result["items"] == []


def test_get_cart_unauthorized():

    response = Mock()
    response.status_code = 401

    with patch(
        "app.clients.cart_client.httpx.get",
        return_value=response,
    ):

        with pytest.raises(HTTPException) as exc:

            get_cart("bad-token")

    assert exc.value.status_code == 401


def test_get_cart_bad_gateway():

    response = Mock()
    response.status_code = 500

    with patch(
        "app.clients.cart_client.httpx.get",
        return_value=response,
    ):

        with pytest.raises(HTTPException) as exc:

            get_cart("test-token")

    assert exc.value.status_code == 502


def test_get_cart_service_unavailable():

    with patch(
        "app.clients.cart_client.httpx.get",
        side_effect=httpx.RequestError(
            "Connection failed"
        ),
    ):

        with pytest.raises(HTTPException) as exc:

            get_cart("test-token")

    assert exc.value.status_code == 503


def test_clear_cart_success():

    response = Mock()

    response.status_code = 200
    response.json.return_value = {
        "message": "Cart cleared successfully"
    }

    with patch(
        "app.clients.cart_client.httpx.delete",
        return_value=response,
    ):

        result = clear_cart("test-token")

    assert (
        result["message"]
        == "Cart cleared successfully"
    )


def test_clear_cart_unauthorized():

    response = Mock()
    response.status_code = 401

    with patch(
        "app.clients.cart_client.httpx.delete",
        return_value=response,
    ):

        with pytest.raises(HTTPException) as exc:

            clear_cart("bad-token")

    assert exc.value.status_code == 401


def test_clear_cart_failure():

    response = Mock()
    response.status_code = 500

    with patch(
        "app.clients.cart_client.httpx.delete",
        return_value=response,
    ):

        with pytest.raises(HTTPException) as exc:

            clear_cart("test-token")

    assert exc.value.status_code == 502


def test_clear_cart_service_unavailable():

    with patch(
        "app.clients.cart_client.httpx.delete",
        side_effect=httpx.RequestError(
            "Connection failed"
        ),
    ):

        with pytest.raises(HTTPException) as exc:

            clear_cart("test-token")

    assert exc.value.status_code == 503