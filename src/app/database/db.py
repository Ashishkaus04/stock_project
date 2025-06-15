import sqlite3
from datetime import datetime
import os
import bcrypt
import sys

# Global variable to hold the main application's database connection
_main_db_connection = None

def get_app_path():
    """Get the path to the application directory, works in both dev and PyInstaller"""
    if getattr(sys, 'frozen', False):
        # Running in a PyInstaller bundle, the app directory is at the root
        return os.path.dirname(sys.executable)
    else:
        # Running in normal Python environment, navigate up from current file
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def connect_db():
    """Connect to the SQLite database"""
    app_base_path = get_app_path()
    # When bundled, 'app' is a top-level directory within the executable. 'database' is inside 'app'.
    db_path = os.path.join(app_base_path, 'app', 'database', 'inventory.db')
    # Ensure database directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return sqlite3.connect(db_path, check_same_thread=False)

def get_main_db_connection():
    global _main_db_connection
    if _main_db_connection is None:
        _main_db_connection = connect_db()
    return _main_db_connection

def close_main_db_connection():
    global _main_db_connection
    if _main_db_connection:
        _main_db_connection.close()
        _main_db_connection = None # Reset the connection
        print("DEBUG: Main database connection closed.")

def create_tables():
    # Use the main connection for table creation
    conn = get_main_db_connection()
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

        # Explicitly close and re-establish the main connection after table creation/check
        close_main_db_connection() 
        get_main_db_connection() # Re-establish connection

    except Exception as e:
        print(f"Error creating tables: {str(e)}")
        conn.rollback()
        raise e

def tables_exist():
    # Use the main connection for this check
    conn = get_main_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('users', 'sessions')
        """)
    tables = cursor.fetchall()
    return len(tables) == 2

def get_user_count():
    # Use the main connection for this check
    conn = get_main_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    return cursor.fetchone()[0]

def add_product(name, category, quantity, min_stock, user_id=None):
    # Use the main connection
    conn = get_main_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO products (name, category, quantity, min_stock, created_date) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
                       (name, category, quantity, min_stock))
        product_id = cursor.lastrowid

        # Record initial creation in quantity_history
        cursor.execute("INSERT INTO quantity_history (product_id, old_quantity, new_quantity, change_date, seller_name, invoice_number, user_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (product_id, 0, quantity, datetime.now(), "Initial Creation", "N/A", user_id))
        
        conn.commit()
        return product_id
    except Exception as e:
        conn.rollback()
        raise e

def update_product_quantity(product_id, new_quantity, seller_name=None, invoice_number=None, user_id=None):
    # Use the main connection
    conn = get_main_db_connection()
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
    # Use the main connection
    conn = get_main_db_connection()
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
            LEFT JOIN users u ON qh.user_id = u.id
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
    # Use the main connection
    conn = get_main_db_connection()
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
    # Use the main connection
    conn = get_main_db_connection()
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
    # Use the main connection
    conn = get_main_db_connection()
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
    # Use the main connection
    conn = get_main_db_connection()
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
    # Use the main connection
    conn = get_main_db_connection()
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
    # Use the main connection
    conn = get_main_db_connection()
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
    # Use the main connection
    conn = get_main_db_connection()
    cursor = conn.cursor()
    try:
        print(f"DEBUG: Attempting to get user by credentials for username: {username}")
        cursor.execute("SELECT id, username, password_hash, role FROM users WHERE username = ?", (username,))
        user_data = cursor.fetchone()
        print(f"DEBUG: Retrieved user_data: {user_data}")
        if user_data:
            stored_password_hash = user_data[2]
            print(f"DEBUG: Stored password hash: {stored_password_hash}")
            if check_password(password, stored_password_hash):
                print("DEBUG: Password check successful.")
                return {'id': user_data[0], 'username': user_data[1], 'password_hash': user_data[2], 'role': user_data[3]}
            else:
                print("DEBUG: Password check failed.")
        else:
            print(f"DEBUG: User '{username}' not found.")
        return None
    finally:
        # Do NOT close connection here, it's managed by the global variable
        pass

def get_user_by_id(user_id):
    # Use the main connection
    conn = get_main_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, username, role, password_hash FROM users WHERE id = ?", (user_id,))
        user_data = cursor.fetchone()
        if user_data:
            return {'id': user_data[0], 'username': user_data[1], 'role': user_data[2], 'password_hash': user_data[3]}
        return None
    except Exception as e:
        print(f"Error getting user by ID: {str(e)}")
        return None

def update_user_password(user_id, new_password):
    # Use the main connection
    conn = get_main_db_connection()
    cursor = conn.cursor()
    try:
        hashed_password = hash_password(new_password)
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hashed_password, user_id))
        conn.commit()
        messagebox.showinfo("Success", "Password updated successfully!")
    except Exception as e:
        conn.rollback()
        messagebox.showerror("Error", f"Failed to update password: {e}")

def debug_get_all_history():
    # Use the main connection
    conn = get_main_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM quantity_history")
        records = cursor.fetchall()
        print("\n--- ALL QUANTITY HISTORY RECORDS (DEBUG) ---")
        for record in records:
            print(record)
        print("-------------------------------------------")
    except Exception as e:
        print(f"Error getting all history for debug: {str(e)}")

def debug_get_all_users():
    # Use the main connection
    conn = get_main_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, username, role FROM users")
        users = cursor.fetchall()
        print("\n--- ALL USERS (DEBUG) ---")
        for user in users:
            print(user)
        print("-------------------------")
    except Exception as e:
        print(f"Error getting all users for debug: {str(e)}")

def add_session_to_db(token, user_id, expires_at):
    # Use the main connection
    conn = get_main_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)", (token, user_id, expires_at))
        conn.commit()
    except Exception as e:
        print(f"Error adding session to database: {str(e)}")
        conn.rollback()
        raise e

def get_session_from_db(token):
    # Use the main connection
    conn = get_main_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT user_id, expires_at FROM sessions WHERE token = ?", (token,))
        result = cursor.fetchone()
        if result:
            # Assuming expires_at is stored as a string in ISO format (YYYY-MM-DD HH:MM:SS.ffffff)
            user_id, expires_at_str = result
            # Convert string back to datetime object
            expires_at = datetime.strptime(expires_at_str, '%Y-%m-%d %H:%M:%S.%f')
            return {'user_id': user_id, 'expires_at': expires_at}
        return None
    except Exception as e:
        print(f"Error getting session from database: {str(e)}")
        return None

def remove_session_from_db(token):
    # Use the main connection
    conn = get_main_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()
    except Exception as e:
        print(f"Error removing session from database: {str(e)}")
        conn.rollback()
        raise e

def remove_expired_sessions():
    # Use the main connection
    conn = get_main_db_connection()
    cursor = conn.cursor()
    try:
        current_time = datetime.now()
        cursor.execute("DELETE FROM sessions WHERE expires_at < ?", (current_time,))
        conn.commit()
    except Exception as e:
        print(f"Error removing expired sessions: {str(e)}")
        conn.rollback()

def delete_user(user_id):
    # Use the main connection
    conn = get_main_db_connection()
    cursor = conn.cursor()
    try:
        # Delete related sessions first
        cursor.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        # Then delete the user
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        print(f"User {user_id} and associated sessions deleted.")
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
    print(f"DEBUG: check_password - Checking plain: {password} against hash: {hashed_password}")
    result = bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    print(f"DEBUG: check_password result: {result}")
    return result

def add_user(username, password, role='user'):
    # Use the main connection
    conn = get_main_db_connection()
    cursor = conn.cursor()
    try:
        hashed_password = hash_password(password)
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", (username, hashed_password, role))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError: # Catch specific error for unique constraint
        raise ValueError(f"Username '{username}' already exists.")
    except Exception as e:
        conn.rollback()
        raise e

def get_user_by_username(username):
    # Use the main connection
    conn = get_main_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, username, password_hash, role FROM users WHERE username = ?", (username,))
        user_data = cursor.fetchone()
        if user_data:
            return {'id': user_data[0], 'username': user_data[1], 'password_hash': user_data[2], 'role': user_data[3]}
        return None
    except Exception as e:
        print(f"Error getting user by username: {str(e)}")
        return None

def recreate_users_table():
    # Use the main connection
    conn = get_main_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DROP TABLE IF EXISTS users;")
        # Handle case where sqlite_sequence might not exist yet
        try:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='users';")
        except sqlite3.OperationalError as e:
            if "no such table: sqlite_sequence" in str(e):
                print("Warning: sqlite_sequence table does not exist yet. Skipping reset.")
                # Do NOT re-raise here, simply proceed
            else:
                raise # Re-raise other operational errors

        # Recreate the users table
        cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user'
            )
        """)
        conn.commit()
        print("Users table recreated successfully.")

        # Run VACUUM to ensure database is clean and auto-increment is truly reset
        cursor.execute("VACUUM;")
        conn.commit()
        print("Database vacuumed after users table recreation.")

    except Exception as e:
        conn.rollback()
        print(f"Error recreating users table: {e}")
        raise e

def reset_auto_increment_sequence(table_name):
    # Use the main connection
    conn = get_main_db_connection()
    cursor = conn.cursor()
    try:
        # Get the maximum ID from the table
        cursor.execute(f"SELECT MAX(id) FROM {table_name}")
        max_id = cursor.fetchone()[0]
        if max_id is None:
            max_id = 0 # If table is empty, start from 0

        # Update sqlite_sequence table
        # If the entry exists, update it; otherwise, insert it.
        cursor.execute("""
            INSERT OR REPLACE INTO sqlite_sequence (name, seq) VALUES (?, ?)
        """, (table_name, max_id))
        conn.commit()
        print(f"Auto-increment sequence for {table_name} reset to {max_id}.")
    except Exception as e:
        conn.rollback()
        print(f"Error resetting auto-increment sequence for {table_name}: {e}")
        raise e
