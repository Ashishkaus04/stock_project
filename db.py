import psycopg2
from datetime import datetime

def connect_db():
    # Use the provided Render PostgreSQL external database URL
    return psycopg2.connect("postgresql://stack_project_mvd_user:cNnrEDOdsE1dWTK5JDv4FkbzwDbScnyu@dpg-d0r9dgh5pdvs73dpd4pg-a.oregon-postgres.render.com/stack_project_mvd")

def create_tables():
    conn = connect_db()
    cursor = conn.cursor()
    
    # Create products table with unique name
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            category TEXT,
            quantity INTEGER,
            min_stock INTEGER,
            created_date TIMESTAMP
        )
    """)
    
    # Create quantity_history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quantity_history (
            id SERIAL PRIMARY KEY,
            product_id INTEGER REFERENCES products(id),
            old_quantity INTEGER,
            new_quantity INTEGER,
            change_date TIMESTAMP,
            seller_name TEXT,
            invoice_number TEXT
        )
    """)
    
    # Verify tables exist (PostgreSQL version)
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
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
        cursor.execute(
            "INSERT INTO products (name, category, quantity, min_stock, created_date) VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (name, category, quantity, min_stock, current_time)
        )
        product_id = cursor.fetchone()[0]
        
        # Record initial quantity in history
        cursor.execute(
            "INSERT INTO quantity_history (product_id, old_quantity, new_quantity, change_date) VALUES (%s, %s, %s, %s)",
            (product_id, 0, quantity, current_time)
        )
        
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
        cursor.execute("SELECT quantity FROM products WHERE id = %s", (product_id,))
        result = cursor.fetchone()
        if result is None:
            raise Exception("Product not found")
        old_quantity = result[0]
        
        # Update product quantity
        cursor.execute("UPDATE products SET quantity = %s WHERE id = %s", (new_quantity, product_id))
        
        # Record the change in history with seller information
        current_time = datetime.now()
        print(f"Recording history: product_id={product_id}, old={old_quantity}, new={new_quantity}, time={current_time}")
        cursor.execute(
            "INSERT INTO quantity_history (product_id, old_quantity, new_quantity, change_date, seller_name, invoice_number) VALUES (%s, %s, %s, %s, %s, %s)",
            (product_id, old_quantity, new_quantity, current_time, seller_name, invoice_number)
        )
        
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
    try:
        cursor.execute(
            "SELECT old_quantity, new_quantity, change_date, seller_name, invoice_number FROM quantity_history WHERE product_id = %s ORDER BY change_date DESC",
            (product_id,)
        )
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
        cursor.execute(
            "SELECT name, category, quantity, min_stock, created_date FROM products WHERE id = %s",
            (product_id,)
        )
        return cursor.fetchone()
    finally:
        conn.close()

def get_all_products(search_term=None):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        sql_query = "SELECT id, name, category, quantity, min_stock FROM products"
        if search_term:
            # Add WHERE clause to filter by name or category (case-insensitive)
            sql_query += " WHERE LOWER(name) LIKE LOWER(%s) OR LOWER(category) LIKE LOWER(%s)"
            # Add wildcard to search term for LIKE query
            search_pattern = f"%{search_term}%"
            cursor.execute(sql_query, (search_pattern, search_pattern))
        else:
            cursor.execute(sql_query)
            
        return cursor.fetchall()
    except Exception as e:
        print(f"Error getting all products: {str(e)}")
        return []
    finally:
        conn.close()

def get_stock_data():
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name, category, quantity FROM products")
        return cursor.fetchall()
    except Exception as e:
        print(f"Error getting stock data: {str(e)}")
        return []
    finally:
        conn.close()

def delete_product(product_id):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        # Delete related quantity history first
        cursor.execute("DELETE FROM quantity_history WHERE product_id = %s", (product_id,))
        
        # Then delete the product
        cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
        deleted_count = cursor.rowcount
        
        conn.commit()
        return deleted_count
    except Exception as e:
        print(f"Error deleting product: {str(e)}")
        conn.rollback()
        raise e
    finally:
        conn.close()
