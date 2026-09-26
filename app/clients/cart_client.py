import httpx

from fastapi import HTTPException, status

from app.config import settings


def get_cart(token: str):

    url = f"{settings.CART_SERVICE_URL}/api/cart/"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        response = httpx.get(
            url,
            headers=headers,
            timeout=5.0
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cart service is unavailable"
        )

    if response.status_code == 401:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed while accessing Cart Service"
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to communicate with Cart Service"
        )

    return response.json()

def clear_cart(token: str):

    url = f"{settings.CART_SERVICE_URL}/api/cart/"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:

        response = httpx.delete(
            url,
            headers=headers,
            timeout=5.0
        )

    except httpx.RequestError:

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cart service is unavailable"
        )

    if response.status_code == 401:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed while accessing Cart Service"
        )

    if response.status_code != 200:

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to clear cart"
        )

    return response.json()