import requests
import json

BASE_URL = "https://stock-management-api.onrender.com"

def test_endpoint(method, endpoint, data=None):
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
        return response
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def main():
    # Test root endpoint
    test_endpoint("GET", "/")
    
    # Create tables
    test_endpoint("POST", "/create-tables")
    
    # Test adding a product
    product_data = {
        "name": "Test Product",
        "category": "Test Category",
        "quantity": 10,
        "min_stock": 5
    }
    response = test_endpoint("POST", "/product", product_data)
    
    if response and response.status_code == 201:
        product_id = response.json().get('product_id')
        
        # Test getting all products
        test_endpoint("GET", "/products")
        
        # Test getting specific product
        test_endpoint("GET", f"/product/{product_id}")
        
        # Test updating product quantity
        update_data = {
            "new_quantity": 15,
            "seller_name": "Test Seller",
            "invoice_number": "INV001"
        }
        test_endpoint("PUT", f"/product/{product_id}/quantity", update_data)
        
        # Test getting product history
        test_endpoint("GET", f"/product/{product_id}/history")
    
    # Test getting stock data
    test_endpoint("GET", "/stock")

if __name__ == "__main__":
    main() 