import sys
import uuid
import httpx

# Compatibility fix: Starlette 0.27.0 TestClient passes `app=...` to httpx.Client,
# which was deprecated and removed in httpx >= 0.28.0.
if not hasattr(httpx.Client, "_original_init"):
    _orig_init = httpx.Client.__init__
    def _patched_init(self, *args, **kwargs):
        if "app" in kwargs:
            app = kwargs.pop("app")
            if "transport" not in kwargs:
                kwargs["transport"] = httpx.ASGITransport(app=app)
        return _orig_init(self, *args, **kwargs)
    httpx.Client.__init__ = _patched_init
    httpx.Client._original_init = _orig_init

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_analytics_endpoints():
    print("=== Testing Analytics Endpoints ===")

    uid = uuid.uuid4().hex[:6]

    # Setup: Create 2 products
    p1 = client.post("/products", json={
        "name": f"Analytics Monitor {uid}",
        "category": "Tech",
        "price": 200.0,
        "stock": 4  # below default threshold 10
    }).json()
    p1_id = p1["id"]

    p2 = client.post("/products", json={
        "name": f"Analytics Desk {uid}",
        "category": "Furniture",
        "price": 500.0,
        "stock": 20 # above default threshold 10
    }).json()
    p2_id = p2["id"]

    # Setup: Create 2 customers
    c1 = client.post("/customers", json={
        "name": f"High Spender {uid}",
        "email": f"high_{uid}@example.com"
    }).json()
    c1_id = c1["id"]

    c2 = client.post("/customers", json={
        "name": f"Low Spender {uid}",
        "email": f"low_{uid}@example.com"
    }).json()
    c2_id = c2["id"]

    # Customer 1 buys 2 Monitors ($400) and 1 Desk ($500) = $900 total spend
    order1 = client.post("/orders", json={
        "customer_id": c1_id,
        "items": [
            {"product_id": p1_id, "quantity": 2},
            {"product_id": p2_id, "quantity": 1}
        ]
    }).json()

    # Customer 2 buys 1 Monitor ($200) = $200 total spend
    order2 = client.post("/orders", json={
        "customer_id": c2_id,
        "items": [
            {"product_id": p1_id, "quantity": 1}
        ]
    }).json()

    # 1. Test: Total revenue and units sold per product
    print("\n--- 1. Testing Total revenue and units sold per product ---")
    res_sales = client.get("/analytics/product-sales")
    assert res_sales.status_code == 200, f"Expected 200, got {res_sales.status_code}"
    sales_data = res_sales.json()
    print("Product sales analytics response sample:", sales_data[:3])

    sales_map = {item["product_id"]: item for item in sales_data}
    assert p1_id in sales_map, f"Product {p1_id} should be in sales analytics"
    assert p2_id in sales_map, f"Product {p2_id} should be in sales analytics"

    # Monitor: 2 + 1 = 3 units sold, revenue = 3 * 200 = 600.0
    p1_sales = sales_map[p1_id]
    assert p1_sales["units_sold"] == 3, f"Expected 3 units sold, got {p1_sales['units_sold']}"
    assert p1_sales["total_revenue"] == 600.0, f"Expected 600.0 revenue, got {p1_sales['total_revenue']}"

    # Desk: 1 unit sold, revenue = 1 * 500 = 500.0
    p2_sales = sales_map[p2_id]
    assert p2_sales["units_sold"] == 1, f"Expected 1 unit sold, got {p2_sales['units_sold']}"
    assert p2_sales["total_revenue"] == 500.0, f"Expected 500.0 revenue, got {p2_sales['total_revenue']}"
    print("Passed Product Sales Analytics verification!")

    # 2. Test: Top 5 customers by total spend
    print("\n--- 2. Testing Top 5 customers by total spend ---")
    res_top = client.get("/analytics/top-customers")
    assert res_top.status_code == 200, f"Expected 200, got {res_top.status_code}"
    top_data = res_top.json()
    print("Top customers analytics response:", top_data)
    assert len(top_data) <= 5, f"Should return at most 5 customers, got {len(top_data)}"

    # High Spender spent $900, Low Spender spent $200
    top_map = {c["customer_id"]: c for c in top_data}
    if c1_id in top_map and c2_id in top_map:
        assert top_map[c1_id]["total_spend"] == 900.0, f"Expected 900.0, got {top_map[c1_id]['total_spend']}"
        assert top_map[c2_id]["total_spend"] == 200.0, f"Expected 200.0, got {top_map[c2_id]['total_spend']}"
        # High Spender should be ranked before Low Spender
        c1_idx = next(i for i, c in enumerate(top_data) if c["customer_id"] == c1_id)
        c2_idx = next(i for i, c in enumerate(top_data) if c["customer_id"] == c2_id)
        assert c1_idx < c2_idx, "High Spender should be ranked higher than Low Spender"
    print("Passed Top Customers verification!")

    # 3. Test: Products with stock below threshold (default 10)
    print("\n--- 3. Testing Products with stock below threshold (default 10) ---")
    res_low = client.get("/analytics/low-stock")
    assert res_low.status_code == 200, f"Expected 200, got {res_low.status_code}"
    low_data = res_low.json()
    # P1 stock was 4, after selling 3, remaining stock is 1 (< 10)
    # P2 stock was 20, after selling 1, remaining stock is 19 (not < 10)
    low_ids = [p["id"] for p in low_data]
    assert p1_id in low_ids, f"Product {p1_id} (stock 1) should be in low stock list"
    assert p2_id not in low_ids, f"Product {p2_id} (stock 19) should not be in default low stock list (< 10)"
    assert all(p["stock"] < 10 for p in low_data), "All items must have stock < 10"
    print("Passed default threshold (10) check!")

    # Test with custom threshold: threshold = 1
    print("\n--- 4. Testing Products with custom threshold (threshold=1) ---")
    res_custom = client.get("/analytics/low-stock?threshold=1")
    assert res_custom.status_code == 200, f"Expected 200, got {res_custom.status_code}"
    custom_data = res_custom.json()
    assert all(p["stock"] < 1 for p in custom_data), "All items must have stock < 1"
    assert p1_id not in [p["id"] for p in custom_data], "Product with stock 1 should not be < 1"
    print("Passed custom threshold check!")

    print("\n=== All Analytics Endpoints Tests Passed! ===")

if __name__ == "__main__":
    test_analytics_endpoints()
