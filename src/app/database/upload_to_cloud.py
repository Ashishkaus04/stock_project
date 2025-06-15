import sqlite3
import psycopg
import os
from datetime import datetime
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

def get_app_path():
    """Get the path to the application directory, works in both dev and PyInstaller"""
    if getattr(sys, 'frozen', False):
        # Running in a PyInstaller bundle, the app directory is at the root
        return os.path.dirname(sys.executable)
    else:
        # Running in normal Python environment, navigate up from current file
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def connect_sqlite():
    """Connect to the SQLite database"""
    app_base_path = get_app_path()
    # When bundled, 'app' is a top-level directory within the executable. 'database' is inside 'app'.
    db_path = os.path.join(app_base_path, 'app', 'database', 'inventory.db')
    # Ensure database directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return sqlite3.connect(db_path)

def connect_postgres(database_url):
    """Connect to the PostgreSQL database"""
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")
    return psycopg.connect(database_url)

def get_table_structure(sqlite_conn, table_name):
    with sqlite_conn:
        cursor = sqlite_conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        return cursor.fetchall()

def create_postgres_table(pg_conn, table_name, columns):
    with pg_conn.cursor() as cursor:
        # Drop existing table if it exists
        cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
        
        # Create table with the same structure
        column_defs = []
        for col in columns:
            col_id, col_name, col_type, not_null, default_val, pk = col
            # Convert SQLite data types to PostgreSQL
            if col_type == 'INTEGER':
                pg_type = 'INTEGER'
            elif col_type == 'TEXT':
                pg_type = 'TEXT'
            elif col_type == 'TIMESTAMP':
                pg_type = 'TIMESTAMP'
            elif col_type == 'BOOLEAN':
                pg_type = 'BOOLEAN'
            else:
                pg_type = 'TEXT'  # Default to TEXT for unknown types
            
            nullable = 'NOT NULL' if not_null else ''
            column_defs.append(f"{col_name} {pg_type} {nullable}")
        
        create_table_sql = f"CREATE TABLE {table_name} ({', '.join(column_defs)})"
        print(f"Creating table {table_name} with SQL: {create_table_sql}")
        cursor.execute(create_table_sql)
        pg_conn.commit()

def upload_data(postgresql_db_url):
    print("Starting data upload from SQLite to PostgreSQL...")
    print("PROGRESS:0") # Initial progress
    
    # Connect to both databases
    sqlite_conn = connect_sqlite()
    pg_conn = connect_postgres(postgresql_db_url)
    
    try:
        # Get and create table structures
        tables = ['users', 'products', 'quantity_history', 'sessions']
        for table in tables:
            print(f"\nGetting structure for table {table}...")
            columns = get_table_structure(sqlite_conn, table)
            print(f"Columns in {table}:", columns)
            create_postgres_table(pg_conn, table, columns)
        
        # Upload users
        print("\nUploading users...")
        with sqlite_conn:
            sqlite_cursor = sqlite_conn.cursor()
            sqlite_cursor.execute("SELECT * FROM users")
            users = sqlite_cursor.fetchall()
            print(f"Found {len(users)} users to upload")
            
            with pg_conn.cursor() as pg_cursor:
                for user in users:
                    try:
                        placeholders = ','.join(['%s' for _ in user])
                        pg_cursor.execute(
                            f"INSERT INTO users VALUES ({placeholders})",
                            user
                        )
                    except Exception as e:
                        print(f"Error inserting user: {str(e)}")
                pg_conn.commit()
        print("PROGRESS:25") # Progress after users table
        
        # Upload products
        print("\nUploading products...")
        with sqlite_conn:
            sqlite_cursor = sqlite_conn.cursor()
            sqlite_cursor.execute("SELECT * FROM products")
            products = sqlite_cursor.fetchall()
            print(f"Found {len(products)} products to upload")
            
            with pg_conn.cursor() as pg_cursor:
                for product in products:
                    try:
                        placeholders = ','.join(['%s' for _ in product])
                        pg_cursor.execute(
                            f"INSERT INTO products VALUES ({placeholders})",
                            product
                        )
                    except Exception as e:
                        print(f"Error inserting product: {str(e)}")
                pg_conn.commit()
        print("PROGRESS:50") # Progress after products table
        
        # Upload quantity history
        print("\nUploading quantity history...")
        with sqlite_conn:
            sqlite_cursor = sqlite_conn.cursor()
            sqlite_cursor.execute("SELECT * FROM quantity_history")
            history = sqlite_cursor.fetchall()
            print(f"Found {len(history)} history records to upload")
            
            with pg_conn.cursor() as pg_cursor:
                for record in history:
                    try:
                        placeholders = ','.join(['%s' for _ in record])
                        pg_cursor.execute(
                            f"INSERT INTO quantity_history VALUES ({placeholders})",
                            record
                        )
                    except Exception as e:
                        print(f"Error inserting history record: {str(e)}")
                pg_conn.commit()
        print("PROGRESS:75") # Progress after quantity_history table
        
        # Upload sessions
        print("\nUploading sessions...")
        with sqlite_conn:
            sqlite_cursor = sqlite_conn.cursor()
            sqlite_cursor.execute("SELECT * FROM sessions")
            sessions = sqlite_cursor.fetchall()
            print(f"Found {len(sessions)} sessions to upload")
            
            with pg_conn.cursor() as pg_cursor:
                for session in sessions:
                    try:
                        placeholders = ','.join(['%s' for _ in session])
                        pg_cursor.execute(
                            f"INSERT INTO sessions VALUES ({placeholders})",
                            session
                        )
                    except Exception as e:
                        print(f"Error inserting session: {str(e)}")
                pg_conn.commit()
        print("PROGRESS:100") # Progress after sessions table
        
        print("\nData upload completed successfully!")
        
    except Exception as e:
        print(f"Error during upload: {str(e)}")
        raise e
    finally:
        sqlite_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    # Get PostgreSQL DATABASE_URL from environment variable
    cloud_db_url = os.environ.get("DATABASE_URL")
    if not cloud_db_url:
        print("DATABASE_URL environment variable not set. Cannot upload to cloud.")
        sys.exit(1)
    upload_data(cloud_db_url) 