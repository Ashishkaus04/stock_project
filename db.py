import sqlite3
from datetime import datetime

def connect_db():
    conn = sqlite3.connect("inventory.db")
    # Register datetime adapter
    sqlite3.register_adapter(datetime, lambda dt: dt.isoformat())
    sqlite3.register_converter("datetime", lambda s: datetime.fromisoformat(s.decode()))
    return conn

def create_tables():
    conn = connect_db()
    cursor = conn.cursor()
    
    # Create products table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            quantity INTEGER,
            min_stock INTEGER,
            created_date datetime
        )
    """)
    
    # Create quantity_history table without contact fields
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quantity_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            old_quantity INTEGER,
            new_quantity INTEGER,
            change_date datetime,
            seller_name TEXT,
            invoice_number TEXT,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    """)
    
    # Verify tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("Existing tables:", [table[0] for table in tables])
    
    conn.commit()
    conn.close()

def add_product(name, category, quantity, min_stock):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        current_time = datetime.now()
        # Insert the new product with creation date
        cursor.execute("""
            INSERT INTO products (name, category, quantity, min_stock, created_date)
            VALUES (?, ?, ?, ?, ?)
        """, (name, category, quantity, min_stock, current_time))
        
        product_id = cursor.lastrowid
        
        # Record initial quantity in history
        cursor.execute("""
            INSERT INTO quantity_history (product_id, old_quantity, new_quantity, change_date)
            VALUES (?, ?, ?, ?)
        """, (product_id, 0, quantity, current_time))
        
        conn.commit()
        return product_id
    except Exception as e:
        print(f"Error adding product: {str(e)}")
        conn.rollback()
        raise e
    finally:
        conn.close()

def update_product_quantity(product_id, new_quantity, seller_name=None, invoice_number=None):
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # Get current quantity
        cursor.execute("SELECT quantity FROM products WHERE id = ?", (product_id,))
        result = cursor.fetchone()
        if result is None:
            raise Exception("Product not found")
        old_quantity = result[0]
        
        # Update product quantity
        cursor.execute("UPDATE products SET quantity = ? WHERE id = ?", (new_quantity, product_id))
        
        # Record the change in history with seller information
        current_time = datetime.now()
        print(f"Recording history: product_id={product_id}, old={old_quantity}, new={new_quantity}, time={current_time}")
        cursor.execute("""
            INSERT INTO quantity_history (
                product_id, old_quantity, new_quantity, change_date,
                seller_name, invoice_number
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (product_id, old_quantity, new_quantity, current_time,
              seller_name, invoice_number))
        
        conn.commit()
    except Exception as e:
        print(f"Error updating quantity: {str(e)}")
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_quantity_history(product_id):
    conn = connect_db()
    cursor = conn.cursor()
    
    # First check if the history table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='quantity_history'")
    if not cursor.fetchone():
        print("History table does not exist!")
        return []
    
    try:
        cursor.execute("""
            SELECT old_quantity, new_quantity, change_date,
                   seller_name, invoice_number
            FROM quantity_history 
            WHERE product_id = ? 
            ORDER BY change_date DESC
        """, (product_id,))
        history = cursor.fetchall()
        print(f"Found {len(history)} history records for product {product_id}")
        return history
    except Exception as e:
        print(f"Error getting history: {str(e)}")
        return []
    finally:
        conn.close()

def get_product_details(product_id):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT name, category, quantity, min_stock, created_date 
            FROM products 
            WHERE id = ?
        """, (product_id,))
        return cursor.fetchone()
    finally:
        conn.close()
