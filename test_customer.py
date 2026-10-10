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

def test_customer_endpoints():
    print("=== Testing Customer Router Endpoints ===")

    # 1. Validation tests for invalid emails (422)
    invalid_emails = [
        "not-an-email",
        "user@",
        "@example.com",
        "user@domain",
        "",
        "   ",
        "user@domain..com"
    ]
    for email in invalid_emails:
        print(f"\n--- Validation test for invalid email: '{email}' (should fail 422) ---")
        res = client.post("/customers", json={"name": "Test User", "email": email})
        assert res.status_code == 422, f"Expected 422 for email '{email}', got {res.status_code}"
        print(f"Passed 422 for '{email}'")

    # 2. Validation test for empty name (422)
    print("\n--- Validation test for empty name (should fail 422) ---")
    res = client.post("/customers", json={"name": "   ", "email": "valid.name@example.com"})
    assert res.status_code == 422, f"Expected 422 for empty name, got {res.status_code}"
    print("Passed 422 for empty name")

    # 3. Create customer with valid data (201)
    unique_suffix = uuid.uuid4().hex[:8]
    email1 = f"customer_{unique_suffix}@example.com"
    print(f"\n--- Create customer with valid email: '{email1}' (201) ---")
    res1 = client.post("/customers", json={"name": "Alice Smith", "email": email1})
    assert res1.status_code == 201, f"Expected 201, got {res1.status_code}"
    customer1 = res1.json()
    print("Created customer:", customer1)
    assert customer1["name"] == "Alice Smith"
    assert customer1["email"] == email1
    assert "id" in customer1

    # 4. Attempt to create customer with existing email (409)
    print(f"\n--- Attempt duplicate email creation: '{email1}' (should fail 409) ---")
    res_dup = client.post("/customers", json={"name": "Alice Clone", "email": email1})
    assert res_dup.status_code == 409, f"Expected 409, got {res_dup.status_code}"
    print("Passed 409 duplicate check:", res_dup.json())

    # 5. Create a second customer (201)
    email2 = f"customer2_{unique_suffix}@example.com"
    print(f"\n--- Create second customer: '{email2}' (201) ---")
    res2 = client.post("/customers", json={"name": "Bob Jones", "email": email2})
    assert res2.status_code == 201, f"Expected 201, got {res2.status_code}"
    customer2 = res2.json()
    print("Created customer 2:", customer2)

    # 6. List customers (200)
    print("\n--- List customers (200) ---")
    res_list = client.get("/customers")
    assert res_list.status_code == 200, f"Expected 200, got {res_list.status_code}"
    customers = res_list.json()
    assert isinstance(customers, list), "Expected list response"
    emails_in_list = [c["email"] for c in customers]
    assert email1 in emails_in_list, f"Expected {email1} in customer list"
    assert email2 in emails_in_list, f"Expected {email2} in customer list"
    print(f"Successfully retrieved {len(customers)} customers from list endpoint")

    # 7. Get single customer by ID (200 & 404)
    print(f"\n--- Get customer by ID {customer1['id']} (200) ---")
    res_single = client.get(f"/customers/{customer1['id']}")
    assert res_single.status_code == 200, f"Expected 200, got {res_single.status_code}"
    assert res_single.json()["email"] == email1
    print("Fetched single customer:", res_single.json())

    print("\n--- Get non-existent customer by ID (404) ---")
    res_404 = client.get("/customers/9999999")
    assert res_404.status_code == 404, f"Expected 404, got {res_404.status_code}"
    print("Passed 404 check:", res_404.json())

    print("\n=== All Customer Router Tests Passed! ===")

if __name__ == "__main__":
    test_customer_endpoints()
