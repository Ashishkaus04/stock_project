import sqlite3
import os
import psycopg2
from urllib.parse import urlparse
from datetime import datetime

# Local SQLite database path
local_db_path = os.path.join(os.path.dirname(__file__), 'inventory.db')

def connect_local_db():
    return sqlite3.connect(local_db_path)

def connect_cloud_db(db_url):
    result = urlparse(db_url)
    username = result.username
    password = result.password
    database = result.path[1:]
    hostname = result.hostname
    port = result.port
    
    conn = psycopg2.connect(
        database = database,
        user = username,
        password = password,
        host = hostname,
        port = port,
        sslmode = 'require'
    )
    return conn

def clear_cloud_data(cloud_conn):
    print("Clearing existing data in cloud database...")
    cloud_cursor = cloud_conn.cursor()
    try:
        # Delete from tables in correct order to avoid foreign key issues
        cloud_cursor.execute("DELETE FROM sessions;")
        cloud_cursor.execute("DELETE FROM quantity_history;")
        cloud_cursor.execute("DELETE FROM products;")
        cloud_cursor.execute("DELETE FROM users;") # Users last, as others might reference it
        
        cloud_conn.commit()
        print("Cloud data cleared successfully.")
    except Exception as e:
        cloud_conn.rollback()
        print(f"Error clearing cloud data: {e}")
        raise

def upload_data(cloud_db_url):
    local_conn = None
    cloud_conn = None
    try:
        local_conn = connect_local_db()
        local_cursor = local_conn.cursor()

        cloud_conn = connect_cloud_db(cloud_db_url)
        cloud_cursor = cloud_conn.cursor()

        # Clear cloud data before uploading
        clear_cloud_data(cloud_conn)

        # 1. Upload Users
        print("Uploading users...")
        local_cursor.execute("SELECT id, username, password_hash, role FROM users")
        users = local_cursor.fetchall()
        for user_id, username, password_hash, role in users:
            try:
                cloud_cursor.execute(
                    "INSERT INTO users (id, username, password_hash, role) VALUES (%s, %s, %s, %s)",
                    (user_id, username, password_hash, role)
                )
            except psycopg2.errors.UniqueViolation:
                # Handle cases where user might already exist (e.g., admin user)
                print(f"User {username} already exists in cloud, skipping.")
                cloud_conn.rollback() # Rollback the failed insert
            except Exception as e:
                print(f"Error inserting user {username}: {e}")
                cloud_conn.rollback()
                raise e
        cloud_conn.commit()
        print(f"Uploaded {len(users)} users.")

        # 2. Upload Products
        print("Uploading products...")
        local_cursor.execute("SELECT id, name, category, quantity, min_stock, created_date FROM products")
        products = local_cursor.fetchall()
        for product_id, name, category, quantity, min_stock, created_date in products:
            # Ensure created_date is a datetime object for psycopg2
            if isinstance(created_date, str):
                try:
                    created_date = datetime.strptime(created_date, '%Y-%m-%d %H:%M:%S.%f')
                except ValueError:
                    # Fallback for dates without microseconds or just date
                    created_date = datetime.strptime(created_date.split('.')[0], '%Y-%m-%d %H:%M:%S')
            
            cloud_cursor.execute(
                "INSERT INTO products (id, name, category, quantity, min_stock, created_date) VALUES (%s, %s, %s, %s, %s, %s)",
                (product_id, name, category, quantity, min_stock, created_date)
            )
        cloud_conn.commit()
        print(f"Uploaded {len(products)} products.")

        # 3. Upload Quantity History
        print("Uploading quantity history...")
        local_cursor.execute("SELECT id, product_id, old_quantity, new_quantity, change_date, seller_name, invoice_number, user_id FROM quantity_history")
        history_records = local_cursor.fetchall()
        for hist_id, product_id, old_quantity, new_quantity, change_date, seller_name, invoice_number, user_id in history_records:
            # Ensure change_date is a datetime object for psycopg2
            if isinstance(change_date, str):
                try:
                    change_date = datetime.strptime(change_date, '%Y-%m-%d %H:%M:%S.%f')
                except ValueError:
                    # Fallback for dates without microseconds or just date
                    change_date = datetime.strptime(change_date.split('.')[0], '%Y-%m-%d %H:%M:%S')

            cloud_cursor.execute(
                "INSERT INTO quantity_history (id, product_id, old_quantity, new_quantity, change_date, seller_name, invoice_number, user_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (hist_id, product_id, old_quantity, new_quantity, change_date, seller_name, invoice_number, user_id)
            )
        cloud_conn.commit()
        print(f"Uploaded {len(history_records)} quantity history records.")
        
        # 4. Upload Sessions (if applicable and desired to sync)
        print("Uploading sessions...")
        local_cursor.execute("SELECT token, user_id, created_at, expires_at FROM sessions")
        sessions = local_cursor.fetchall()
        for token, user_id, created_at, expires_at in sessions:
            if isinstance(created_at, str):
                try:
                    created_at = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S.%f')
                except ValueError:
                    created_at = datetime.strptime(created_at.split('.')[0], '%Y-%m-%d %H:%M:%S')
            if isinstance(expires_at, str):
                try:
                    expires_at = datetime.strptime(expires_at, '%Y-%m-%d %H:%M:%S.%f')
                except ValueError:
                    expires_at = datetime.strptime(expires_at.split('.')[0], '%Y-%m-%d %H:%M:%S')

            cloud_cursor.execute(
                "INSERT INTO sessions (token, user_id, created_at, expires_at) VALUES (%s, %s, %s, %s)",
                (token, user_id, created_at, expires_at)
            )
        cloud_conn.commit()
        print(f"Uploaded {len(sessions)} sessions.")


        print("Data upload completed successfully!")

    except Exception as e:
        print(f"Error during data upload: {e}")
        if cloud_conn:
            cloud_conn.rollback()
        raise
    finally:
        if local_conn:
            local_conn.close()
        if cloud_conn:
            cloud_conn.close()

if __name__ == "__main__":
    # Get PostgreSQL DATABASE_URL from environment variable
    cloud_db_url = os.environ.get("DATABASE_URL")
    if not cloud_db_url:
        print("DATABASE_URL environment variable not set. Cannot upload to cloud.")
        exit(1)
    
    upload_data(cloud_db_url) 