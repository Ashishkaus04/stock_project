import sqlite3
import psycopg
import os
import csv
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

def get_table_structure(pg_conn, table_name):
    with pg_conn.cursor() as cursor:
        cursor.execute(f"""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position;
        """)
        return cursor.fetchall()

def create_sqlite_table(sqlite_conn, table_name, columns):
    with sqlite_conn:
        cursor = sqlite_conn.cursor()
        
        # Drop existing table if it exists
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        
        # Create table with the same structure
        column_defs = []
        for col_name, data_type, is_nullable in columns:
            sqlite_type = 'TEXT'  # Default to TEXT for unknown types
            nullable = 'NOT NULL' if is_nullable == 'NO' else ''
            primary_key = ''

            # Convert PostgreSQL data types to SQLite
            if col_name == 'id' and data_type == 'integer':
                sqlite_type = 'INTEGER'
                primary_key = 'PRIMARY KEY AUTOINCREMENT'
            elif data_type == 'integer':
                sqlite_type = 'INTEGER'
            elif data_type == 'text':
                sqlite_type = 'TEXT'
            elif data_type == 'timestamp without time zone':
                sqlite_type = 'TIMESTAMP'
            elif data_type == 'boolean':
                sqlite_type = 'INTEGER'  # SQLite uses INTEGER for boolean
            
            column_defs.append(f"{col_name} {sqlite_type} {nullable} {primary_key}".strip())
        
        create_table_sql = f"CREATE TABLE {table_name} ({', '.join(column_defs)})"
        print(f"Creating table {table_name} with SQL: {create_table_sql}")
        cursor.execute(create_table_sql)

def migrate_data(postgresql_db_url):
    print("Starting data migration from PostgreSQL to SQLite...")
    print("PROGRESS:0") # Initial progress
    
    # Connect to both databases
    pg_conn = connect_postgres(postgresql_db_url)
    sqlite_conn = connect_sqlite()
    
    try:
        # Get and create table structures
        tables = ['users', 'products', 'quantity_history', 'sessions']
        for table in tables:
            print(f"\nGetting structure for table {table}...")
            columns = get_table_structure(pg_conn, table)
            print(f"Columns in {table}:", columns)
            create_sqlite_table(sqlite_conn, table, columns)
        
        # Migrate users
        print("\nMigrating users...")
        with pg_conn.cursor() as pg_cursor:
            pg_cursor.execute("SELECT * FROM users")
            users = pg_cursor.fetchall()
            print(f"Found {len(users)} users to migrate")
            
            with sqlite_conn:
                sqlite_cursor = sqlite_conn.cursor()
                for user in users:
                    try:
                        placeholders = ','.join(['?' for _ in user])
                        sqlite_cursor.execute(
                            f"INSERT INTO users VALUES ({placeholders})",
                            user
                        )
                    except sqlite3.IntegrityError as e:
                        print(f"Error inserting user: {str(e)}")
        print("PROGRESS:25") # Progress after users table
        
        # Migrate products
        print("\nMigrating products...")
        with pg_conn.cursor() as pg_cursor:
            pg_cursor.execute("SELECT * FROM products")
            products = pg_cursor.fetchall()
            print(f"Found {len(products)} products to migrate")
            
            with sqlite_conn:
                sqlite_cursor = sqlite_conn.cursor()
                for product in products:
                    try:
                        placeholders = ','.join(['?' for _ in product])
                        sqlite_cursor.execute(
                            f"INSERT INTO products VALUES ({placeholders})",
                            product
                        )
                    except sqlite3.IntegrityError as e:
                        print(f"Error inserting product: {str(e)}")
        print("PROGRESS:50") # Progress after products table
        
        # Migrate quantity history
        print("\nMigrating quantity history...")
        with pg_conn.cursor() as pg_cursor:
            pg_cursor.execute("SELECT * FROM quantity_history")
            history = pg_cursor.fetchall()
            print(f"Found {len(history)} history records to migrate")
            
            with sqlite_conn:
                sqlite_cursor = sqlite_conn.cursor()
                for record in history:
                    try:
                        placeholders = ','.join(['?' for _ in record])
                        sqlite_cursor.execute(
                            f"INSERT INTO quantity_history VALUES ({placeholders})",
                            record
                        )
                    except sqlite3.IntegrityError as e:
                        print(f"Error inserting history record: {str(e)}")
        print("PROGRESS:75") # Progress after quantity_history table
        
        # Migrate sessions
        print("\nMigrating sessions...")
        with pg_conn.cursor() as pg_cursor:
            pg_cursor.execute("SELECT * FROM sessions")
            sessions = pg_cursor.fetchall()
            print(f"Found {len(sessions)} sessions to migrate")
            
            with sqlite_conn:
                sqlite_cursor = sqlite_conn.cursor()
                for session in sessions:
                    try:
                        placeholders = ','.join(['?' for _ in session])
                        sqlite_cursor.execute(
                            f"INSERT INTO sessions VALUES ({placeholders})",
                            session
                        )
                    except sqlite3.IntegrityError as e:
                        print(f"Error inserting session: {str(e)}")
        print("PROGRESS:100") # Progress after sessions table
        
        print("\nData migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        raise e
    finally:
        pg_conn.close()
        sqlite_conn.close()

if __name__ == "__main__":
    # Get PostgreSQL DATABASE_URL from environment variable
    cloud_db_url = os.environ.get("DATABASE_URL")
    if not cloud_db_url:
        print("DATABASE_URL environment variable not set. Cannot run migration.")
        sys.exit(1)
    migrate_data(cloud_db_url) 