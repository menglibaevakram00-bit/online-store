import pytest

from app import create_app
from app.models import Order, Product, db
from app.seed import seed_products


@pytest.fixture()
def client():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        }
    )
    with app.app_context():
        db.create_all()
        seed_products()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def test_products_support_search_category_price_and_sort(client):
    response = client.get("/api/products?search=ASUS&category=Для+учёбы&max_price=8000000")
    assert response.status_code == 200
    assert [product["name"] for product in response.json["products"]] == ["ASUS Vivobook 15"]

    sorted_response = client.get("/api/products?sort=price_desc")
    prices = [product["price"] for product in sorted_response.json["products"]]
    assert prices == sorted(prices, reverse=True)


@pytest.mark.parametrize(
    "query",
    [
        "?min_price=-1",
        "?min_price=9000000&max_price=100",
        "?sort=made_up",
    ],
)
def test_products_reject_invalid_filters(client, query):
    response = client.get(f"/api/products{query}")
    assert response.status_code == 400
    assert "error" in response.json


def test_order_uses_database_prices_not_client_prices(client):
    product = client.get("/api/products").json["products"][0]
    response = client.post(
        "/api/orders",
        json={
            "customer": {"name": "Анна", "phone": "+998 90 123 45 67"},
            "items": [{"product_id": product["id"], "quantity": 2, "price": 1}],
        },
    )
    assert response.status_code == 201
    assert response.json["order"]["total"] == product["price"] * 2
    assert response.json["order"]["items"][0]["unit_price"] == product["price"]

    with client.application.app_context():
        assert db.session.query(Order).count() == 1


@pytest.mark.parametrize(
    "payload",
    [
        {"customer": {"name": "A", "phone": "123456789"}, "items": [{"product_id": 1, "quantity": 1}]},
        {"customer": {"name": "Анна", "phone": "invalid"}, "items": [{"product_id": 1, "quantity": 1}]},
        {"customer": {"name": "Анна", "phone": "---------"}, "items": [{"product_id": 1, "quantity": 1}]},
        {"customer": {"name": "Анна", "phone": "+998 90 123 45 67"}, "items": [{"product_id": 1, "quantity": 0}]},
        {"customer": {"name": "Анна", "phone": "+998 90 123 45 67"}, "items": [{"product_id": 999, "quantity": 1}]},
    ],
)
def test_orders_reject_invalid_or_unknown_items(client, payload):
    response = client.post("/api/orders", json=payload)
    assert response.status_code in (400, 404)
    assert "error" in response.json


def test_health_endpoint_checks_database(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json == {"status": "ok"}
