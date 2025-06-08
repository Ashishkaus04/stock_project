import psycopg
from datetime import datetime
import os

def connect_db():
    # Use the DATABASE_URL environment variable
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")
    return psycopg.connect(database_url)

def create_tables():
    with connect_db() as conn:
        with conn.cursor() as cursor:
            try:
                # Drop existing tables if they exist
                cursor.execute("DROP TABLE IF EXISTS quantity_history")
                cursor.execute("DROP TABLE IF EXISTS products")
                
                # Create products table with unique name
                cursor.execute("""
                    CREATE TABLE products (
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
                    CREATE TABLE quantity_history (
                        id SERIAL PRIMARY KEY,
                        product_id INTEGER REFERENCES products(id),
                        old_quantity INTEGER,
                        new_quantity INTEGER,
                        change_date TIMESTAMP,
                        seller_name TEXT,
                        invoice_number TEXT,
                        user_id INTEGER
                    )
                """)
                
                # Verify tables exist (PostgreSQL version)
                cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
                tables = cursor.fetchall()
                print("Existing tables:", [table[0] for table in tables])
                
                conn.commit()
            except Exception as e:
                print(f"Error creating tables: {str(e)}")
                conn.rollback()
                raise e

def add_product(name, category, quantity, min_stock):
    with connect_db() as conn:
        with conn.cursor() as cursor:
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

def update_product_quantity(product_id, new_quantity, seller_name=None, invoice_number=None, user_id=None):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            try:
                # Get current quantity
                cursor.execute("SELECT quantity FROM products WHERE id = %s", (product_id,))
                result = cursor.fetchone()
                if result is None:
                    raise Exception("Product not found")
                old_quantity = result[0]
                
                # Update product quantity
                cursor.execute("UPDATE products SET quantity = %s WHERE id = %s", (new_quantity, product_id))
                
                # Record the change in history with seller information and user_id
                current_time = datetime.now()
                print(f"Recording history: product_id={product_id}, old={old_quantity}, new={new_quantity}, time={current_time}, user_id={user_id}")
                cursor.execute(
                    "INSERT INTO quantity_history (product_id, old_quantity, new_quantity, change_date, seller_name, invoice_number, user_id) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (product_id, old_quantity, new_quantity, current_time, seller_name, invoice_number, user_id)
                )
                
                conn.commit()
            except Exception as e:
                print(f"Error updating quantity: {str(e)}")
                conn.rollback()
                raise e

def get_quantity_history(product_id):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            try:
                # Select history without joining with users table
                cursor.execute(
                    """
                    SELECT
                        qh.old_quantity,
                        qh.new_quantity,
                        qh.change_date,
                        qh.seller_name,
                        qh.invoice_number,
                        qh.user_id
                    FROM quantity_history qh
                    WHERE qh.product_id = %s
                    ORDER BY qh.change_date DESC
                    """,
                    (product_id,)
                )
                history = cursor.fetchall()
                print(f"Found {len(history)} history records for product {product_id}")
                return history
            except Exception as e:
                print(f"Error getting history: {str(e)}")
                return []

def get_product_details(product_id):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute(
                    "SELECT name, category, quantity, min_stock, created_date FROM products WHERE id = %s",
                    (product_id,)
                )
                return cursor.fetchone()
            except Exception as e:
                print(f"Error getting product details: {str(e)}")
                return None

def get_all_products(search_term=None):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            try:
                # SQL query to select product details and the user_id of the latest history entry
                sql_query = """
                    SELECT
                        p.id,
                        p.name,
                        p.category,
                        p.quantity,
                        p.min_stock,
                        -- Select the user_id from the most recent history entry for this product
                        (SELECT user_id FROM quantity_history qh WHERE qh.product_id = p.id ORDER BY qh.change_date DESC LIMIT 1) as last_changed_by_user_id
                    FROM products p
                """
                params = ()

                if search_term:
                    # Add WHERE clause to filter by name or category (case-insensitive)
                    sql_query += " WHERE LOWER(p.name) LIKE LOWER(%s) OR LOWER(p.category) LIKE LOWER(%s)"
                    # Add wildcard to search term for LIKE query
                    search_pattern = f"%{search_term}%"
                    params = (search_pattern, search_pattern)

                cursor.execute(sql_query, params)
                return cursor.fetchall()
            except Exception as e:
                print(f"Error getting all products: {str(e)}")
                return []

def get_stock_data():
    with connect_db() as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute("SELECT name, category, quantity FROM products")
                return cursor.fetchall()
            except Exception as e:
                print(f"Error getting stock data: {str(e)}")
                return []

def delete_product(product_id):
    with connect_db() as conn:
        with conn.cursor() as cursor:
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
