import sqlite3
from datetime import datetime
import os
import bcrypt

def connect_db():
    # Use a local SQLite database file
    db_path = os.path.join(os.path.dirname(__file__), 'inventory.db')
    return sqlite3.connect(db_path)

def create_tables():
    with connect_db() as conn:
        cursor = conn.cursor()
        try:
            # Create products table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    category TEXT,
                    quantity INTEGER,
                    min_stock INTEGER,
                    created_date TIMESTAMP
                )
            """)
            
            # Create quantity_history table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quantity_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER,
                    old_quantity INTEGER,
                    new_quantity INTEGER,
                    change_date TIMESTAMP,
                    seller_name TEXT,
                    invoice_number TEXT,
                    user_id INTEGER,
                    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
                )
            """)
            
            # Create users table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'user'
                )
            """)

            # Create sessions table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    token TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Verify tables exist (SQLite version)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print("Existing tables:", [table[0] for table in tables])
            
            conn.commit()
            print("Tables created successfully (if they didn't exist).")
        except Exception as e:
            print(f"Error creating tables: {str(e)}")
            conn.rollback()
            raise e

def tables_exist():
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('users', 'sessions')
        """)
        tables = cursor.fetchall()
        return len(tables) == 2

def get_user_count():
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        return cursor.fetchone()[0]

def add_product(name, category, quantity, min_stock, user_id=None):
    with connect_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO products (name, category, quantity, min_stock, created_date) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
                           (name, category, quantity, min_stock))
            product_id = cursor.lastrowid

            # Record initial creation in quantity_history
            cursor.execute("INSERT INTO quantity_history (product_id, old_quantity, new_quantity, change_date, seller_name, invoice_number, user_id) VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?, ?, ?)",
                           (product_id, 0, quantity, "Initial Creation", "N/A", user_id))
            
            conn.commit()
            return product_id
        except Exception as e:
            conn.rollback()
            raise e

def update_product_quantity(product_id, new_quantity, seller_name=None, invoice_number=None, user_id=None):
    with connect_db() as conn:
        cursor = conn.cursor()
        try:
            # Get current quantity
            cursor.execute("SELECT quantity FROM products WHERE id = ?", (product_id,))
            result = cursor.fetchone()
            if result is None:
                raise Exception("Product not found")
            old_quantity = result[0]
            
            # Update product quantity directly to the new_quantity provided
            cursor.execute("UPDATE products SET quantity = ? WHERE id = ?", (new_quantity, product_id))
            
            # Record the change in history with seller information and user_id
            current_time = datetime.now()
            print(f"Recording history: product_id={product_id}, old={old_quantity}, new={new_quantity}, time={current_time}, user_id={user_id}")
            cursor.execute(
                "INSERT INTO quantity_history (product_id, old_quantity, new_quantity, change_date, seller_name, invoice_number, user_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (product_id, old_quantity, new_quantity, current_time, seller_name, invoice_number, user_id)
            )
            
            conn.commit()
        except Exception as e:
            print(f"Error updating quantity: {str(e)}")
            conn.rollback()
            raise e

def get_quantity_history(product_id, start_date=None, end_date=None):
    with connect_db() as conn:
        cursor = conn.cursor()
        try:
            sql_query = """
                SELECT
                    qh.old_quantity,
                    qh.new_quantity,
                    qh.change_date,
                    qh.seller_name,
                    qh.invoice_number,
                    qh.user_id,
                    u.username
                FROM quantity_history qh
                JOIN users u ON qh.user_id = u.id
                WHERE qh.product_id = ?
            """
            params = [product_id]

            if start_date:
                sql_query += " AND qh.change_date >= ?"
                params.append(start_date)
            if end_date:
                sql_query += " AND qh.change_date <= ?"
                params.append(end_date)
            
            sql_query += " ORDER BY qh.change_date DESC"

            cursor.execute(sql_query, tuple(params))
            history = cursor.fetchall()
            print(f"Found {len(history)} history records for product {product_id}")
            return history
        except Exception as e:
            print(f"Error getting history: {str(e)}")
            return []

def get_product_details(product_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT name, category, quantity, min_stock, created_date FROM products WHERE id = ?",
                (product_id,)
            )
            return cursor.fetchone()
        except Exception as e:
            print(f"Error getting product details: {str(e)}")
            return None

def get_all_products(search_term=None):
    with connect_db() as conn:
        cursor = conn.cursor()
        try:
            # SQL query to select product details and the user_id of the latest history entry
            sql_query = """
                SELECT
                    p.id,
                    p.name,
                    p.category,
                    p.quantity,
                    p.min_stock,
                    (SELECT user_id FROM quantity_history qh WHERE qh.product_id = p.id ORDER BY qh.change_date DESC LIMIT 1) as last_changed_by_user_id
                FROM products p
            """
            params = ()

            if search_term:
                # Add WHERE clause to filter by name or category (case-insensitive)
                sql_query += " WHERE LOWER(p.name) LIKE LOWER(?) OR LOWER(p.category) LIKE LOWER(?)"
                # Add wildcard to search term for LIKE query
                search_pattern = f"%{search_term}%"
                params = (search_pattern, search_pattern)

            cursor.execute(sql_query, params)
            return cursor.fetchall()
        except Exception as e:
            print(f"Error getting all products: {str(e)}")
            return []

def get_stock_data(start_date=None, end_date=None):
    with connect_db() as conn:
        cursor = conn.cursor()
        try:
            sql_query = "SELECT name, category, quantity FROM products"
            params = []

            if start_date:
                sql_query += " WHERE created_date >= ?"
                params.append(start_date)
            if end_date:
                # Use AND if start_date is already present, otherwise WHERE
                if start_date:
                    sql_query += " AND created_date <= ?"
                else:
                    sql_query += " WHERE created_date <= ?"
                params.append(end_date)

            cursor.execute(sql_query, tuple(params))
            return cursor.fetchall()
        except Exception as e:
            print(f"Error getting stock data: {str(e)}")
            return []

def delete_product(product_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        try:
            # Delete related quantity history first
            cursor.execute("DELETE FROM quantity_history WHERE product_id = ?", (product_id,))
            
            # Then delete the product
            cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
            deleted_count = cursor.rowcount
            
            conn.commit()
            return deleted_count
        except Exception as e:
            print(f"Error deleting product: {str(e)}")
            conn.rollback()
            raise e

def get_all_users():
    with connect_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, username, role FROM users")
            users = cursor.fetchall()
            print(f"Found {len(users)} users.")
            return users
        except Exception as e:
            print(f"Error getting all users: {str(e)}")
            return []

def add_user_to_db(username, password_hash, role):
    with connect_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", (username, password_hash, role))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Error adding user to database: {str(e)}")
            conn.rollback()
            raise e

def get_user_by_credentials(username, password):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, username, password_hash, role FROM users WHERE username = ?", (username,))
        user_data = cursor.fetchone()
        if user_data:
            stored_password_hash = user_data[2]
            if check_password(password, stored_password_hash):
                return {'id': user_data[0], 'username': user_data[1], 'password_hash': user_data[2], 'role': user_data[3]}
        return None
    finally:
        conn.close()

def get_user_by_id(user_id):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, username, password_hash, role FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if user:
            return {'id': user[0], 'username': user[1], 'password_hash': user[2], 'role': user[3]}
        return None
    finally:
        conn.close()

def update_user_password(user_id, new_password):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        hashed_password = hash_password(new_password)
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hashed_password, user_id))
        conn.commit()
    finally:
        conn.close()

def debug_get_all_history():
    """Temporary function to retrieve and print all quantity history records."""
    with connect_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM quantity_history")
            all_history = cursor.fetchall()
            print("\n--- ALL QUANTITY HISTORY RECORDS (DEBUG) ---")
            for record in all_history:
                print(record)
            print("-------------------------------------------")
            return all_history
        except Exception as e:
            print(f"Error debugging history: {str(e)}")
            return []

def add_session_to_db(token, user_id, expires_at):
    with connect_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)", (token, user_id, expires_at))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding session to database: {str(e)}")
            conn.rollback()
            raise e

def get_session_from_db(token):
    with connect_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT user_id, expires_at FROM sessions WHERE token = ? AND expires_at > CURRENT_TIMESTAMP", (token,))
            session_data = cursor.fetchone()
            return session_data
        except Exception as e:
            print(f"Error getting session from database: {str(e)}")
            return None

def remove_session_from_db(token):
    with connect_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error removing session from database: {str(e)}")
            conn.rollback()
            return False

def remove_expired_sessions():
    with connect_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM sessions WHERE expires_at < CURRENT_TIMESTAMP")
            conn.commit()
            print("Expired sessions cleaned up.")
        except Exception as e:
            print(f"Error cleaning up expired sessions: {str(e)}")

def delete_user(user_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            deleted_count = cursor.rowcount
            conn.commit()
            print(f"Deleted {deleted_count} user(s) with ID {user_id}.")
            return deleted_count
        except Exception as e:
            print(f"Error deleting user: {str(e)}")
            conn.rollback()
            raise e

def hash_password(password):
    # Hash a password for storage
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')

def check_password(password, hashed_password):
    # Check a clear-text password against a hashed one
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def add_user(username, password, role='user'):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        hashed_password = hash_password(password)
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", (username, hashed_password, role))
        conn.commit()
    finally:
        conn.close()

def get_user_by_username(username):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, username, password_hash FROM users WHERE username = ?", (username,))
        user_data = cursor.fetchone()
        if user_data:
            # Return as dictionary for consistency with get_user_by_credentials
            return {'id': user_data[0], 'username': user_data[1], 'password_hash': user_data[2]}
        return None
    finally:
        conn.close()
