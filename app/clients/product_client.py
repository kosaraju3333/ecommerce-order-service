import httpx

from fastapi import HTTPException, status

from app.config import settings


def reduce_product_stock(
    product_id: int,
    quantity: int
):

    url = (
        f"{settings.PRODUCT_SERVICE_URL}"
        f"/api/products/{product_id}/stock/reduce"
    )

    try:

        response = httpx.put(
            url,
            json={
                "quantity": quantity
            },
            timeout=5.0
        )

    except httpx.RequestError:

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Product service is unavailable"
        )

    if response.status_code == 404:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found"
        )

    if response.status_code == 400:

        detail = response.json().get(
            "detail",
            "Unable to reduce product stock"
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

    if response.status_code != 200:

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to update product inventory"
        )

    return response.json()