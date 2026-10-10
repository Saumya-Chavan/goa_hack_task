# GOA Hack — Inventory, Orders & Analytics Platform

A high-performance full-stack inventory management, order processing, and business analytics system built with **FastAPI**, **SQLAlchemy**, **SQLite**, **React 18**, and **Tailwind CSS**.

---

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Project Architecture](#project-architecture)
- [Features](#features)
  - [1. Product CRUD (`/products`)](#1-product-crud-products)
  - [2. Customer Management (`/customers`)](#2-customer-management-customers)
  - [3. Transactional Orders & Atoms (`/orders`)](#3-transactional-orders--atoms-orders)
  - [4. Business Analytics (`/analytics`)](#4-business-analytics-analytics)
  - [5. Frontend Dashboard (`/dashboard`)](#5-frontend-dashboard-dashboard)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation & Setup](#installation--setup)
  - [Running the Application](#running-the-application)
- [API Reference](#api-reference)
- [Running Test Suites](#running-test-suites)

---

## Overview

This project provides an end-to-end commerce and inventory platform with robust data validation, atomic database transactions for orders, advanced SQL analytics, and an interactive tabbed frontend dashboard with zero build-step overhead.

---

## Tech Stack

- **Backend**: Python 3.13, [FastAPI](https://fastapi.tiangolo.com/), [SQLAlchemy 2.x](https://www.sqlalchemy.org/), [Pydantic v2](https://docs.pydantic.dev/), [Uvicorn](https://www.uvicorn.org/)
- **Database**: SQLite with ACID transaction safety
- **Frontend**: [React 18](https://react.dev/), [Tailwind CSS](https://tailwindcss.com/) (served directly via FastAPI static mount)
- **Testing**: FastAPI TestClient & [HTTPX](https://www.python-httpx.org/)

---

## Project Architecture

```text
goa_hack/
├── database.py              # SQLite engine, SessionLocal, and declarative base
├── models.py                # SQLAlchemy ORM models (Product, Customer, Order, OrderItem, HealthCheckLog)
├── schemas.py               # Pydantic v2 data schemas and validation logic
├── main.py                  # FastAPI app entry point, CORS, routers & static mounts
├── routers/
│   ├── __init__.py
│   ├── health.py            # Health check endpoints & system logging
│   ├── product.py           # Full Product CRUD with filters & pagination
│   ├── customer.py          # Customer creation & email uniqueness checks
│   ├── order.py             # Atomic order placement & stock deduction
│   └── analytics.py         # SQL join & aggregation analytics endpoints
├── static/
│   └── index.html           # React 18 + Tailwind CSS single-page dashboard
├── test_product.py          # Automated test suite for Product CRUD
├── test_customer.py         # Automated test suite for Customer endpoints
├── test_order.py            # Automated test suite for Order transactions & stock
├── test_analytics.py        # Automated test suite for SQL analytics
└── requirements.txt         # Project dependencies
```

---

## Features

### 1. Product CRUD (`/products`)
- **Full CRUD operations**: Create (`POST`), Read List & Single (`GET`), Update (`PUT`/`PATCH`), and Delete (`DELETE`).
- **Input Validation**: Rejects empty/blank names (`min_length=1`), enforces positive prices (`price > 0`), and non-negative stock (`stock >= 0`).
- **Paging & Filtering**: Filter by `category` and `max_price`, with pagination parameters `page` and `limit`/`page_limit`. Returns `{ data, page, limit, total }`.
- **Status Codes**: `201 Created` on creation, `204 No Content` on deletion, and `404 Not Found` if a product does not exist.

### 2. Customer Management (`/customers`)
- **Format Validation**: Strict regex verification for email format (`user@domain.tld`), returning `422 Unprocessable Entity` for invalid entries.
- **Uniqueness Check**: Rejects duplicate email registrations with **`409 Conflict`**.
- **Listing & Details**: Retrieve all registered customers with optional offset/limit pagination.

### 3. Transactional Orders & Atoms (`/orders`)
- **Atomic Single-Transaction Execution**:
  1. Validates that the customer exists (returns `404 Not Found` if missing).
  2. Aggregates requested quantities across order items.
  3. Checks stock for every product; if stock is insufficient, rolls back and returns **`404 Not Found`** with an explanatory message.
  4. Automatically deducts inventory stock.
  5. Persists the order and its items (**atoms**) snapshotting current unit prices.
- **Order Retrieval**: Fetch single order with its eager-loaded items (`joinedload`), or list all orders with pagination.

### 4. Business Analytics (`/analytics`)
- **Product Sales & Revenue**: Outer joins `Product` with `OrderItem` and aggregates total units sold and revenue per item (`GET /analytics/product-sales`).
- **Top 5 Customers by Spend**: Joins `Customer` $\to$ `Order` $\to$ `OrderItem` to rank the highest lifetime spenders (`GET /analytics/top-customers`).
- **Low Stock Inventory Alerts**: Identifies products whose stock is below a configurable threshold (defaults to 10) (`GET /analytics/low-stock?threshold=10`).

### 5. Frontend Dashboard (`/dashboard`)
- **Zero Build Setup**: Pure React 18 and Tailwind CSS loaded directly in the browser via CDN.
- **Tab Navigation**: Clean, intuitive switching between:
  - 📦 **Products**: Catalog table, category/price filters, pagination, and Add Product modal.
  - 👥 **Customers**: Customer directory and Add Customer modal with instant feedback.
  - 🛒 **Orders**: Detailed order list with atom breakdown and multi-item order placement.
  - 📊 **Analytics**: Revenue tables, customer spend leaderboard, and low-stock threshold sliders.

---

## Getting Started

### Prerequisites
- Python 3.10+ (tested on Python 3.13)
- `pip` package manager

### Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd goa_hack
   ```

2. **Activate the Virtual Environment**:
   - On macOS / Linux:
     ```bash
     source .venv/bin/activate
     ```
   - On Windows:
     ```powershell
     .\.venv\Scripts\activate
     ```

   *(If creating a new virtual environment)*:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

Start the Uvicorn development server:
```bash
uvicorn main:app --reload
```

The application will be accessible at:
- **Web Dashboard**: [http://localhost:8000/dashboard](http://localhost:8000/dashboard) (or [http://localhost:8000/](http://localhost:8000/))
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## API Reference

### Products
| Method | Endpoint | Description | Status Code |
| :--- | :--- | :--- | :--- |
| `GET` | `/products` | List products (supports `category`, `max_price`, `page`, `limit`) | `200 OK` |
| `POST` | `/products` | Create product (enforces non-empty name, `price > 0`, `stock >= 0`) | `201 Created` |
| `GET` | `/products/{id}` | Retrieve product by ID | `200 OK` / `404 Not Found` |
| `PUT` | `/products/{id}` | Update product attributes | `200 OK` / `404 Not Found` |
| `DELETE` | `/products/{id}` | Delete product | `204 No Content` / `404 Not Found` |

### Customers
| Method | Endpoint | Description | Status Code |
| :--- | :--- | :--- | :--- |
| `GET` | `/customers` | List all registered customers | `200 OK` |
| `POST` | `/customers` | Register customer (email format validation; duplicate returns 409) | `201 Created` / `409 Conflict` |
| `GET` | `/customers/{id}` | Retrieve customer by ID | `200 OK` / `404 Not Found` |

### Orders
| Method | Endpoint | Description | Status Code |
| :--- | :--- | :--- | :--- |
| `POST` | `/orders` | Atomic order placement, stock verification & deduction | `201 Created` / `404 Not Found` |
| `GET` | `/orders` | List orders with pagination (`page`, `limit`) | `200 OK` |
| `GET` | `/orders/{id}` | Get single order with its items/atoms | `200 OK` / `404 Not Found` |

### Analytics
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/analytics/product-sales` | Aggregated units sold and total revenue per product |
| `GET` | `/analytics/top-customers` | Top 5 customers ranked by lifetime spend (`limit` parameter optional) |
| `GET` | `/analytics/low-stock` | Products with inventory below threshold (default: `10`) |

### System Health
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Basic service health status |
| `GET` | `/health/detailed` | Database connectivity check |
| `POST` | `/health/log` | Record health check event in database |
| `GET` | `/health/logs` | View historical health check logs |

---

## Running Test Suites

Each module is backed by comprehensive test suites covering validation constraints, edge cases, status codes, and atomic rollbacks:

```bash
# 1. Test Product CRUD & validation rules
python test_product.py

# 2. Test Customer email validation & duplicate 409 handling
python test_customer.py

# 3. Test Order placement, atom persistence, and stock rollback on 404
python test_order.py

# 4. Test SQL joins and aggregation analytics
python test_analytics.py
```

Run all tests together:
```bash
python test_product.py && python test_customer.py && python test_order.py && python test_analytics.py
```