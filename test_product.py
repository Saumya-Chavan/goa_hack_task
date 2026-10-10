import sys
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

def test_full_product_crud():
    print("=== Testing Product CRUD Endpoints ===")

    # 1. Validation tests on creation
    print("\n--- 1. Validation: Negative price should fail (422) ---")
    res = client.post("/products", json={"name": "Bad Price", "price": -10.0, "stock": 5})
    assert res.status_code == 422, f"Expected 422, got {res.status_code}"
    print("Passed:", res.status_code)

    print("\n--- 2. Validation: Zero price should fail (422) ---")
    res = client.post("/products", json={"name": "Zero Price", "price": 0.0, "stock": 5})
    assert res.status_code == 422, f"Expected 422, got {res.status_code}"
    print("Passed:", res.status_code)

    print("\n--- 3. Validation: Negative stock should fail (422) ---")
    res = client.post("/products", json={"name": "Bad Stock", "price": 10.0, "stock": -1})
    assert res.status_code == 422, f"Expected 422, got {res.status_code}"
    print("Passed:", res.status_code)

    print("\n--- 4. Validation: Empty name should fail (422) ---")
    res = client.post("/products", json={"name": "", "price": 10.0, "stock": 5})
    assert res.status_code == 422, f"Expected 422, got {res.status_code}"
    print("Passed:", res.status_code)

    print("\n--- 5. Validation: Blank name should fail (422) ---")
    res = client.post("/products", json={"name": "   ", "price": 10.0, "stock": 5})
    assert res.status_code == 422, f"Expected 422, got {res.status_code}"
    print("Passed:", res.status_code)

    # 2. Successful creation (C)
    print("\n--- 6. Create valid products (201) ---")
    res1 = client.post("/products", json={
        "name": "Mechanical Keyboard",
        "category": "Electronics",
        "price": 99.99,
        "stock": 15
    })
    assert res1.status_code == 201, f"Expected 201, got {res1.status_code}"
    prod1 = res1.json()
    prod1_id = prod1["id"]
    print(f"Created product 1 (ID: {prod1_id}):", prod1)

    res2 = client.post("/products", json={
        "name": "Wireless Mouse",
        "category": "Electronics",
        "price": 29.99,
        "stock": 50
    })
    assert res2.status_code == 201, f"Expected 201, got {res2.status_code}"
    prod2 = res2.json()
    prod2_id = prod2["id"]
    print(f"Created product 2 (ID: {prod2_id}):", prod2)

    res3 = client.post("/products", json={
        "name": "Coffee Mug",
        "category": "Kitchen",
        "price": 14.50,
        "stock": 100
    })
    assert res3.status_code == 201, f"Expected 201, got {res3.status_code}"
    prod3 = res3.json()
    prod3_id = prod3["id"]
    print(f"Created product 3 (ID: {prod3_id}):", prod3)

    # 3. Read single product (R)
    print("\n--- 7. Get product by ID (200) ---")
    res = client.get(f"/products/{prod1_id}")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert res.json()["name"] == "Mechanical Keyboard"
    print("Fetched product 1:", res.json())

    print("\n--- 8. Get non-existent product should return 404 ---")
    res = client.get("/products/9999999")
    assert res.status_code == 404, f"Expected 404, got {res.status_code}"
    print("Passed 404 response:", res.json())

    # 4. Read list with filters and pagination (R)
    print("\n--- 9. List products with pagination and category/max_price filter ---")
    res = client.get("/products?category=Electronics&max_price=50&page=1&limit=10")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    data = res.json()
    print("Filter response:", data)
    assert "data" in data
    assert "page" in data
    assert "limit" in data
    assert "total" in data
    assert all(item["category"] == "Electronics" and item["price"] <= 50 for item in data["data"])

    # 5. Update product (U)
    print("\n--- 10. Update product (PUT) (200) ---")
    res = client.put(f"/products/{prod2_id}", json={
        "name": "Wireless Mouse Pro",
        "category": "Electronics",
        "price": 39.99,
        "stock": 45
    })
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert res.json()["name"] == "Wireless Mouse Pro"
    assert res.json()["price"] == 39.99
    print("Updated product:", res.json())

    print("\n--- 11. Update non-existent product should return 404 ---")
    res = client.put("/products/9999999", json={
        "name": "Ghost",
        "price": 10.0,
        "stock": 1
    })
    assert res.status_code == 404, f"Expected 404, got {res.status_code}"
    print("Passed 404 response on update:", res.json())

    # 6. Delete product (D)
    print("\n--- 12. Delete product (DELETE) (204) ---")
    res = client.delete(f"/products/{prod3_id}")
    assert res.status_code == 204, f"Expected 204, got {res.status_code}"
    print("Deleted successfully with 204 status")

    print("\n--- 13. Verify deleted product is not found (404) ---")
    res = client.get(f"/products/{prod3_id}")
    assert res.status_code == 404, f"Expected 404, got {res.status_code}"
    print("Verified 404 after deletion")

    print("\n--- 14. Delete non-existent product should return 404 ---")
    res = client.delete("/products/9999999")
    assert res.status_code == 404, f"Expected 404, got {res.status_code}"
    print("Passed 404 on deleting non-existent product")

    print("\n=== All Product CRUD Tests Passed! ===")

if __name__ == "__main__":
    test_full_product_crud()
