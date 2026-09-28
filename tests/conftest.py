import pytest

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models.order import Order, OrderItem
from app.config import settings


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


@pytest.fixture()
def db():

    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db):

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def create_token(
    user_id,
    username,
    role="CUSTOMER",
):

    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "exp": datetime.now(timezone.utc)
        + timedelta(minutes=30),
    }

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


@pytest.fixture()
def customer_headers():

    token = create_token(
        1,
        "customer_test",
    )

    return {
        "Authorization": f"Bearer {token}"
    }


@pytest.fixture()
def second_customer_headers():

    token = create_token(
        2,
        "customer_two",
    )

    return {
        "Authorization": f"Bearer {token}"
    }


@pytest.fixture()
def sample_cart():

    return {
        "cart_id": 1,
        "items": [
            {
                "cart_item_id": 1,
                "product_id": 101,
                "name": "iPhone Test",
                "price": "1000.00",
                "image_url": "/images/iphone.jpg",
                "quantity": 2,
                "subtotal": "2000.00",
                "available": True,
            },
            {
                "cart_item_id": 2,
                "product_id": 102,
                "name": "MacBook Test",
                "price": "2000.00",
                "image_url": "/images/macbook.jpg",
                "quantity": 1,
                "subtotal": "2000.00",
                "available": True,
            },
        ],
        "total": "4000.00",
    }


@pytest.fixture()
def order(db):

    order = Order(
        user_id=1,
        status="PLACED",
        total_amount=Decimal("2000.00"),
    )

    db.add(order)
    db.flush()

    item = OrderItem(
        order_id=order.id,
        product_id=101,
        product_name="iPhone Test",
        price=Decimal("1000.00"),
        quantity=2,
        subtotal=Decimal("2000.00"),
    )

    db.add(item)
    db.commit()
    db.refresh(order)

    return order


@pytest.fixture()
def second_customer_order(db):

    order = Order(
        user_id=2,
        status="PLACED",
        total_amount=Decimal("500.00"),
    )

    db.add(order)
    db.flush()

    item = OrderItem(
        order_id=order.id,
        product_id=999,
        product_name="Other Product",
        price=Decimal("500.00"),
        quantity=1,
        subtotal=Decimal("500.00"),
    )

    db.add(item)
    db.commit()
    db.refresh(order)

    return order