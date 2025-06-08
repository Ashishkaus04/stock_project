import db
import pytest
from datetime import datetime
import time

def unique_name(base):
    return f"{base}_{int(time.time() * 1000)}"

def test_create_tables():
    """Test table creation"""
    db.create_tables()
    # If no exception is raised, tables were created successfully

def test_add_product():
    """Test adding a new product"""
    name = unique_name("Test Product")
    # Test adding a product
    product_id = db.add_product(
        name=name,
        category="Test Category",
        quantity=100,
        min_stock=10
    )
    assert product_id is not None
    
    # Verify product was added correctly
    details = db.get_product_details(product_id)
    assert details is not None
    assert details[0] == name
    assert details[1] == "Test Category"
    assert details[2] == 100
    assert details[3] == 10

def test_update_product_quantity():
    """Test updating product quantity"""
    name = unique_name("Update Test Product")
    # First add a product
    product_id = db.add_product(
        name=name,
        category="Test Category",
        quantity=50,
        min_stock=5
    )
    
    # Update quantity
    new_quantity = 75
    db.update_product_quantity(
        product_id=product_id,
        new_quantity=new_quantity,
        seller_name="Test Seller",
        invoice_number="INV-001"
    )
    
    # Verify update
    details = db.get_product_details(product_id)
    assert details[2] == new_quantity
    
    # Check history
    history = db.get_quantity_history(product_id)
    assert len(history) > 0
    latest_change = history[0]
    assert latest_change[1] == new_quantity  # new_quantity
    assert latest_change[3] == "Test Seller"  # seller_name
    assert latest_change[4] == "INV-001"  # invoice_number

def test_get_all_products():
    """Test retrieving all products"""
    name = unique_name("All Products Test")
    # Add a test product
    db.add_product(
        name=name,
        category="Test Category",
        quantity=25,
        min_stock=5
    )
    
    # Get all products
    products = db.get_all_products()
    assert len(products) > 0
    
    # Verify structure of returned data
    for product in products:
        # Check that we have at least the required 5 fields
        assert len(product) >= 5  # id, name, category, quantity, min_stock
        assert isinstance(product[0], int)  # id
        assert isinstance(product[1], str)  # name
        assert isinstance(product[2], str)  # category
        assert isinstance(product[3], int)  # quantity
        assert isinstance(product[4], int)  # min_stock

def test_get_stock_data():
    """Test retrieving stock data"""
    name = unique_name("Stock Data Test")
    # Add a test product
    db.add_product(
        name=name,
        category="Test Category",
        quantity=30,
        min_stock=5
    )
    
    # Get stock data
    stock_data = db.get_stock_data()
    assert len(stock_data) > 0
    
    # Verify structure of returned data
    for item in stock_data:
        assert len(item) == 3  # name, category, quantity
        assert isinstance(item[0], str)  # name
        assert isinstance(item[1], str)  # category
        assert isinstance(item[2], int)  # quantity

if __name__ == "__main__":
    # Run all tests
    test_create_tables()
    test_add_product()
    test_update_product_quantity()
    test_get_all_products()
    test_get_stock_data()
    print("All tests completed successfully!") 