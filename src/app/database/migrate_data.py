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
    return sqlite3.connect(r"F:\stock_project-master\dist\main\inventory.db")

def connect_postgres():
    """Connect to the PostgreSQL database"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")
    return psycopg.connect(database_url)

def get_sqlite_table_columns(cursor, table_name):
    """Get the list of columns in a SQLite table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [column[1] for column in cursor.fetchall()]

def migrate_data():
    """Migrate data from SQLite to PostgreSQL"""
    print("Starting data migration...")
    
    # Connect to both databases
    sqlite_conn = connect_sqlite()
    pg_conn = connect_postgres()
    
    try:
        # Create a cursor for each database
        sqlite_cursor = sqlite_conn.cursor()
        pg_cursor = pg_conn.cursor()
        
        # Migrate products from SQLite (Keep this, even if empty, as it sets up the product_cache)
        print("Migrating products from SQLite...")
        sqlite_cursor.execute("SELECT id, name, category, quantity, min_stock, created_date FROM products")
        products = sqlite_cursor.fetchall()
        
        for product in products:
            try:
                pg_cursor.execute(
                    """
                    INSERT INTO products (id, name, category, quantity, min_stock, created_date)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE
                    SET name = EXCLUDED.name,
                        category = EXCLUDED.category,
                        quantity = EXCLUDED.quantity,
                        min_stock = EXCLUDED.min_stock,
                        created_date = EXCLUDED.created_date
                    """,
                    product
                )
            except Exception as e:
                print(f"Error migrating product {product[0]}: {str(e)}")
        
        # Dictionary to store product_id by (name, category) for efficient lookup
        product_cache = {}
        # Populate cache with existing products in PostgreSQL
        pg_cursor.execute("SELECT id, name, category FROM products")
        existing_products = pg_cursor.fetchall()
        for pid, name, category in existing_products:
            product_cache[(name, category)] = pid

        # Dictionary to store user_id by username
        user_cache = {}
        # Populate cache with existing users in PostgreSQL
        # Assuming we can get usernames directly from users table if available
        try:
            pg_cursor.execute("SELECT id, username FROM users")
            existing_users = pg_cursor.fetchall()
            for uid, username in existing_users:
                user_cache[username] = uid
        except Exception as e:
            print(f"Warning: Could not fetch users for caching: {e}. User lookup might be incomplete.")

        # Migrate quantity history from CSV
        print("Migrating quantity history from CSV...")
        csv_file_path = r"C:\Users\DELL\Downloads\exported_2025-04-01_to_2025-06-08.csv"
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile)
            header = [col.strip().lower().replace(' ', '_').replace('/', '_by_') for col in next(csv_reader)]  # Read and sanitize header
            print(f"Sanitized CSV Headers: {header}") # Debugging: print sanitized headers

            # Create a map from sanitized header names to their original index
            header_map = {col_name: i for i, col_name in enumerate(header)}

            # Expected columns in CSV based on the image:
            # Product Name, Category, Date, Old Quantity, New Quantity, Change, Seller/Buyer Name, Invoice Number, Changed By
            required_csv_cols = [
                'product_name',
                'category',
                'date',
                'old_quantity',
                'new_quantity',
                'seller_by_buyer_name',
                'invoice_number',
                'changed_by'
            ]

            # Check if all required columns are present
            if not all(col in header_map for col in required_csv_cols):
                missing_cols = [col for col in required_csv_cols if col not in header_map]
                raise ValueError(f"Missing required columns in CSV: {missing_cols}. Please ensure the CSV header matches: {', '.join(required_csv_cols)}")

            for row_num, row in enumerate(csv_reader):
                if not row or all(not cell.strip() for cell in row): # Skip empty rows
                    print(f"Skipping empty row at line {row_num + 2}.")
                    continue
                try:
                    product_name = row[header_map['product_name']].strip()
                    category = row[header_map['category']].strip() if 'category' in header_map else None
                    change_date_str = row[header_map['date']].strip()
                    old_quantity_str = row[header_map['old_quantity']].strip()
                    new_quantity_str = row[header_map['new_quantity']].strip()
                    seller_name = row[header_map['seller_by_buyer_name']].strip() if 'seller_by_buyer_name' in header_map else None
                    invoice_number = row[header_map['invoice_number']].strip() if 'invoice_number' in header_map else None
                    changed_by_username = row[header_map['changed_by']].strip() if 'changed_by' in header_map else None

                    # Get product_id - create if not exists
                    product_id = product_cache.get((product_name, category))
                    if product_id is None:
                        print(f"Product \'{product_name}\' in category \'{category}\' not found in DB. Creating new product...")
                        # Insert a new product with default quantity/min_stock
                        pg_cursor.execute(
                            "INSERT INTO products (name, category, quantity, min_stock, created_date) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                            (product_name, category, 0, 0, datetime.now())
                        )
                        product_id = pg_cursor.fetchone()[0]
                        product_cache[(product_name, category)] = product_id # Add to cache

                    # Get user_id
                    user_id = user_cache.get(changed_by_username)
                    # If user_id is None and a username was provided, it means the user doesn't exist in PostgreSQL.
                    # As per previous instruction, we will just set user_id to None in this case.

                    # Convert quantities
                    old_quantity = int(old_quantity_str) if old_quantity_str else 0
                    new_quantity = int(new_quantity_str) if new_quantity_str else 0
                    
                    # Parse change_date - try multiple formats
                    date_formats = [
                        "%Y-%m-%d %H:%M:%S", 
                        "%Y-%m-%d",
                        "%m/%d/%Y %H:%M:%S",
                        "%m/%d/%Y",
                        "%d/%m/%Y %H:%M:%S",
                        "%d/%m/%Y",
                        "%m/%d/%Y %H:%M",
                    ]
                    change_date = None
                    for fmt in date_formats:
                        try:
                            change_date = datetime.strptime(change_date_str, fmt)
                            break
                        except ValueError:
                            continue
                    
                    if change_date is None:
                        print(f"Warning: Could not parse date \'{change_date_str}\' for row {row_num + 2}. Skipping record.")
                        continue

                    # Insert into quantity_history
                    # Removed 'id' from INSERT statement as it's SERIAL
                    pg_cursor.execute(
                        """
                        INSERT INTO quantity_history 
                        (product_id, old_quantity, new_quantity, change_date, seller_name, invoice_number, user_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (product_id, old_quantity, new_quantity, change_date, seller_name, invoice_number, user_id)
                    )
                except Exception as e:
                    print(f"Error processing CSV row {row_num + 2}: {str(e)} - Row data: {row}")
        
        # Commit the changes
        pg_conn.commit()
        print("Data migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        pg_conn.rollback()
    finally:
        sqlite_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    migrate_data() 