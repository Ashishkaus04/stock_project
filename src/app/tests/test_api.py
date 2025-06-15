import requests
import json
import pytest

BASE_URL = "http://127.0.0.1:5000"

@pytest.mark.parametrize("method,endpoint,data", [
    ("GET", "/", None),
    ("POST", "/create-tables", None),
    ("GET", "/products", None),
    ("GET", "/stock", None),
])
def test_endpoint(method, endpoint, data):
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        
        print(f"\nTesting {method} {endpoint}")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2) if response.text else response.text}")
        assert response.status_code in [200, 201, 204]  # Valid status codes
        return response
    except Exception as e:
        print(f"Error: {str(e)}")
        pytest.fail(f"Test failed with error: {str(e)}")

def test_product_operations():
    # Test adding a product
    product_data = {
        "name": "Test Product",
        "category": "Test Category",
        "quantity": 10,
        "min_stock": 5
    }
    response = requests.post(f"{BASE_URL}/product", json=product_data)
    assert response.status_code == 201
    product_id = response.json().get('product_id')
    
    # Test getting specific product
    response = requests.get(f"{BASE_URL}/product/{product_id}")
    assert response.status_code == 200
    
    # Test updating product quantity
    update_data = {
        "new_quantity": 15,
        "seller_name": "Test Seller",
        "invoice_number": "INV001"
    }
    response = requests.put(f"{BASE_URL}/product/{product_id}/quantity", json=update_data)
    assert response.status_code == 200
    
    # Test getting product history
    response = requests.get(f"{BASE_URL}/product/{product_id}/history")
    assert response.status_code == 200

if __name__ == "__main__":
    pytest.main([__file__, "-v"])