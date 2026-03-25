import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from catalog.models import Category, Product
from orders.models import Order

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="buyer", password="pass12345", email="buyer@example.com")


@pytest.fixture
def category(db):
    return Category.objects.create(name="Electronics", slug="electronics")


@pytest.fixture
def product(db, category):
    return Product.objects.create(
        name="USB Cable",
        price="9.99",
        category=category,
        stock=10,
    )


@pytest.mark.django_db
def test_products_list_and_filters(api_client, category, product):
    other = Category.objects.create(name="Books", slug="books")
    Product.objects.create(name="Novel", price="20.00", category=other, stock=3)

    r = api_client.get("/api/products/")
    assert r.status_code == 200
    assert r.data["count"] == 2

    r = api_client.get(f"/api/products/?category={category.id}")
    assert r.status_code == 200
    assert r.data["count"] == 1
    assert r.data["results"][0]["name"] == "USB Cable"

    r = api_client.get("/api/products/?min_price=15&max_price=25")
    assert r.data["count"] == 1
    assert r.data["results"][0]["name"] == "Novel"

    r = api_client.get("/api/products/?search=USB")
    assert r.data["count"] == 1


@pytest.mark.django_db
def test_product_detail(api_client, product):
    r = api_client.get(f"/api/products/{product.id}/")
    assert r.status_code == 200
    assert r.data["name"] == "USB Cable"


@pytest.mark.django_db
def test_order_create_requires_auth(api_client, product):
    r = api_client.post(
        "/api/orders/",
        {"items": [{"product": product.id, "quantity": 1}]},
        format="json",
    )
    assert r.status_code == 403


@pytest.mark.django_db
def test_order_create_and_stock(api_client, user, product):
    api_client.force_authenticate(user=user)
    r = api_client.post(
        "/api/orders/",
        {"items": [{"product": product.id, "quantity": 2}]},
        format="json",
    )
    assert r.status_code == 201
    assert r.data["status"] == "pending"
    assert str(r.data["total"]) == "19.98"
    product.refresh_from_db()
    assert product.stock == 8


@pytest.mark.django_db
def test_order_retrieve_own_only(api_client, user, product):
    api_client.force_authenticate(user=user)
    create = api_client.post(
        "/api/orders/",
        {"items": [{"product": product.id, "quantity": 1}]},
        format="json",
    )
    oid = create.data["id"]

    r = api_client.get(f"/api/orders/{oid}/")
    assert r.status_code == 200

    other = User.objects.create_user(username="other", password="x")
    api_client.force_authenticate(user=other)
    r = api_client.get(f"/api/orders/{oid}/")
    assert r.status_code == 404


@pytest.mark.django_db
def test_celery_updates_order_status_eager(user, product):
    from orders.tasks import update_order_status

    order = Order.objects.create(user=user, total="9.99", status=Order.Status.PENDING)
    update_order_status(order.id)
    order.refresh_from_db()
    assert order.status == Order.Status.PROCESSING
