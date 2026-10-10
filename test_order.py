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

def test_order_endpoints():
    print("=== Testing Orders Router Endpoints ===")

    # 1. Setup: Create a customer and products
    uid = uuid.uuid4().hex[:6]
    cust_res = client.post("/customers", json={
        "name": f"Order Buyer {uid}",
        "email": f"buyer_{uid}@example.com"
    })
    assert cust_res.status_code == 201, cust_res.text
    customer = cust_res.json()
    customer_id = customer["id"]
    print(f"Created customer ID: {customer_id}")

    p1_res = client.post("/products", json={
        "name": f"Laptop {uid}",
        "category": "Tech",
        "price": 1200.0,
        "stock": 10
    })
    assert p1_res.status_code == 201, p1_res.text
    prod1 = p1_res.json()
    prod1_id = prod1["id"]

    p2_res = client.post("/products", json={
        "name": f"Headphones {uid}",
        "category": "Tech",
        "price": 150.0,
        "stock": 5
    })
    assert p2_res.status_code == 201, p2_res.text
    prod2 = p2_res.json()
    prod2_id = prod2["id"]
    print(f"Created products: Prod1(ID: {prod1_id}, Stock: 10, Price: 1200.0), Prod2(ID: {prod2_id}, Stock: 5, Price: 150.0)")

    # 2. Test Customer Exists check (should return 404)
    print("\n--- Test 1: Non-existent customer should return 404 ---")
    res_bad_cust = client.post("/orders", json={
        "customer_id": 999999,
        "items": [{"product_id": prod1_id, "quantity": 1}]
    })
    assert res_bad_cust.status_code == 404, f"Expected 404, got {res_bad_cust.status_code}"
    print("Passed 404 on bad customer:", res_bad_cust.json())

    # 3. Test Non-existent product check (should return 404)
    print("\n--- Test 2: Non-existent product should return 404 ---")
    res_bad_prod = client.post("/orders", json={
        "customer_id": customer_id,
        "items": [{"product_id": 999999, "quantity": 1}]
    })
    assert res_bad_prod.status_code == 404, f"Expected 404, got {res_bad_prod.status_code}"
    print("Passed 404 on bad product:", res_bad_prod.json())

    # 4. Test Insufficient stock (should rollback and return 404 with clear message)
    print("\n--- Test 3: Insufficient stock should rollback and return 404 ---")
    res_out_of_stock = client.post("/orders", json={
        "customer_id": customer_id,
        "items": [
            {"product_id": prod1_id, "quantity": 2},
            {"product_id": prod2_id, "quantity": 100}  # stock is only 5!
        ]
    })
    assert res_out_of_stock.status_code == 404, f"Expected 404, got {res_out_of_stock.status_code}"
    print("Passed 404 on insufficient stock:", res_out_of_stock.json())

    # Verify stock of prod1 was NOT reduced (rollback verification)
    check_p1 = client.get(f"/products/{prod1_id}").json()
    assert check_p1["stock"] == 10, f"Stock was not rolled back! Expected 10, got {check_p1['stock']}"
    print("Verified rollback: Prod1 stock remained 10")

    # 5. Successful order creation (201)
    print("\n--- Test 4: Successful order creation with stock reduction ---")
    res_order = client.post("/orders", json={
        "customer_id": customer_id,
        "items": [
            {"product_id": prod1_id, "quantity": 2},
            {"product_id": prod2_id, "quantity": 3}
        ]
    })
    assert res_order.status_code == 201, f"Expected 201, got {res_order.status_code}"
    order_data = res_order.json()
    order_id = order_data["id"]
    print("Created Order:", order_data)
    assert order_data["customer_id"] == customer_id
    assert "atoms" in order_data or "items" in order_data

    # Check atoms / items contain correct unit prices and quantities
    items = order_data.get("items") or order_data.get("atoms")
    assert len(items) == 2, f"Expected 2 items, got {len(items)}"
    item_map = {item["product_id"]: item for item in items}
    assert item_map[prod1_id]["quantity"] == 2
    assert item_map[prod1_id]["unit_price"] == 1200.0
    assert item_map[prod2_id]["quantity"] == 3
    assert item_map[prod2_id]["unit_price"] == 150.0

    # Verify stock reduction
    check_p1_after = client.get(f"/products/{prod1_id}").json()
    check_p2_after = client.get(f"/products/{prod2_id}").json()
    assert check_p1_after["stock"] == 8, f"Expected prod1 stock 8, got {check_p1_after['stock']}"
    assert check_p2_after["stock"] == 2, f"Expected prod2 stock 2, got {check_p2_after['stock']}"
    print(f"Verified stock deduction: Prod1 stock is now {check_p1_after['stock']}, Prod2 stock is now {check_p2_after['stock']}")

    # 6. Get single order with atoms (200 & 404)
    print(f"\n--- Test 5: Get order by ID {order_id} (200) ---")
    res_get_order = client.get(f"/orders/{order_id}")
    assert res_get_order.status_code == 200, f"Expected 200, got {res_get_order.status_code}"
    single_order = res_get_order.json()
    print("Fetched order:", single_order)
    assert single_order["id"] == order_id
    assert len(single_order["items"]) == 2
    assert len(single_order["atoms"]) == 2

    print("\n--- Test 6: Get non-existent order (404) ---")
    res_order_404 = client.get("/orders/9999999")
    assert res_order_404.status_code == 404, f"Expected 404, got {res_order_404.status_code}"
    print("Passed 404 on non-existent order:", res_order_404.json())

    # 7. List orders with paging
    print("\n--- Test 7: List orders with paging (200) ---")
    res_list_orders = client.get("/orders?page=1&limit=5")
    assert res_list_orders.status_code == 200, f"Expected 200, got {res_list_orders.status_code}"
    orders_page = res_list_orders.json()
    print("List orders response:", orders_page)
    assert "data" in orders_page
    assert "page" in orders_page
    assert "limit" in orders_page
    assert "total" in orders_page
    assert orders_page["page"] == 1
    assert orders_page["limit"] == 5
    assert any(o["id"] == order_id for o in orders_page["data"])

    print("\n=== All Orders Router Tests Passed! ===")

if __name__ == "__main__":
    test_order_endpoints()
