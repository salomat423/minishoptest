# MiniShop — Django E-Commerce REST API

A production-ready e-commerce backend with async order processing via Celery. Built with Django REST Framework, PostgreSQL, and Redis.

## Features

- Product catalog with categories, filtering, and search
- Order management with async processing pipeline
- Celery workers for order confirmation and status updates
- Docker deployment with PostgreSQL + Redis
- Full test coverage with pytest

## Tech Stack

- **Backend** — Django 4.2 + Django REST Framework
- **Database** — PostgreSQL
- **Queue** — Celery + Redis
- **Deployment** — Docker + docker-compose + Gunicorn
- **Tests** — pytest + pytest-django

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/products/` | List products (filter by category, price, search) |
| GET | `/api/products/{id}/` | Product detail |
| POST | `/api/orders/` | Create order (auth required) |
| GET | `/api/orders/{id}/` | Order status |

### Create Order

```http
POST /api/orders/
Authorization: Basic <credentials>
Content-Type: application/json

{
  "items": [
    {"product": 1, "quantity": 2},
    {"product": 3, "quantity": 1}
  ]
}
```

### Filter Products

```http
GET /api/products/?category=electronics&min_price=100&max_price=500&search=phone
```

## Celery Tasks

- `send_order_confirmation` — sends email notification after order is placed
- `update_order_status` — moves order from `pending` → `processing` after a configurable delay

## Setup

### Local

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt

# Copy env file and fill in values
cp .env.example .env

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

In a separate terminal:
```bash
celery -A minishop worker -l info
```

### Docker

```bash
docker compose up --build
```

Services: `web` (port 8000), `db` (PostgreSQL 16), `redis`, `celery`

## Environment Variables

```env
DATABASE_URL=postgresql://user:password@localhost:5432/minishop
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key
DEBUG=True
ORDER_PROCESSING_DELAY_MINUTES=5
```

## Project Structure

```
minishop/
├── catalog/              # Product and Category models + API
│   ├── models.py
│   ├── serializers.py
│   └── views.py
├── orders/               # Order models + Celery tasks
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── tasks.py
├── minishop/             # Django settings, URLs, Celery config
├── tests/                # pytest test suite
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Tests

```bash
python -m pytest
```

6 tests covering models, API endpoints, and order creation flow.

## Admin

Available at `/admin/` — manage products, categories, and orders.
