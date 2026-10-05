import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.models.order import Order, OrderItem
from app.routers.orders import router as order_router


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="E-Commerce Order Service",
    description="Order and checkout microservice",
    version="1.0.0"
)

frontend_url = os.getenv(
    "FRONTEND_URL",
    "http://localhost:4200"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(order_router)


@app.get("/")
def root():

    return {
        "service": "order-service",
        "status": "running"
    }


@app.get("/health")
def health():

    return {
        "service": "order-service",
        "status": "UP"
    }