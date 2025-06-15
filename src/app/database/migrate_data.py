import sqlite3
import psycopg
import os
import csv
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def connect_sqlite():
    """Connect to the SQLite database"""
    db_path = os.path.join(os.path.dirname(__file__), 'inventory.db')
    return sqlite3.connect(db_path)

def connect_postgres():
    """Connect to the PostgreSQL database"""
    database_url = os.getenv('DATABASE_URL')
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
            # Convert PostgreSQL data types to SQLite
            if data_type == 'integer':
                sqlite_type = 'INTEGER'
            elif data_type == 'text':
                sqlite_type = 'TEXT'
            elif data_type == 'timestamp without time zone':
                sqlite_type = 'TIMESTAMP'
            elif data_type == 'boolean':
                sqlite_type = 'INTEGER'  # SQLite uses INTEGER for boolean
            else:
                sqlite_type = 'TEXT'  # Default to TEXT for unknown types
            
            nullable = 'NOT NULL' if is_nullable == 'NO' else ''
            column_defs.append(f"{col_name} {sqlite_type} {nullable}")
        
        create_table_sql = f"CREATE TABLE {table_name} ({', '.join(column_defs)})"
        print(f"Creating table {table_name} with SQL: {create_table_sql}")
        cursor.execute(create_table_sql)

def migrate_data():
    print("Starting data migration from PostgreSQL to SQLite...")
    
    # Connect to both databases
    pg_conn = connect_postgres()
    sqlite_conn = connect_sqlite()
    
    try:
        # Get and create table structures
        tables = ['users', 'products', 'quantity_history', 'sessions']
        for table in tables:
            print(f"\nGetting structure for table {table}...")
            columns = get_table_structure(pg_conn, table)
            print(f"Columns in {table}:", columns)
            create_sqlite_table(sqlite_conn, table, columns)
        
        # Migrate users (Commented out to prevent old password hashes from being migrated)
        # print("\nMigrating users...")
        # with pg_conn.cursor() as pg_cursor:
        #     pg_cursor.execute("SELECT * FROM users")
        #     users = pg_cursor.fetchall()
        #     print(f"Found {len(users)} users to migrate")
        #     
        #     with sqlite_conn:
        #         sqlite_cursor = sqlite_conn.cursor()
        #         for user in users:
        #             try:
        #                 placeholders = ','.join(['?' for _ in user])
        #                 sqlite_cursor.execute(
        #                     f"INSERT INTO users VALUES ({placeholders})",
        #                     user
        #                 )
        #             except sqlite3.IntegrityError as e:
        #                 print(f"Error inserting user: {str(e)}")
        
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
        
        print("\nData migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        raise e
    finally:
        pg_conn.close()
        sqlite_conn.close()

if __name__ == "__main__":
    migrate_data() 