import os
import subprocess
import tkinter as tk
from tkinter import messagebox
from sqlalchemy import create_engine, MetaData, Table, inspect, text
from sqlalchemy.engine import URL
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_neon_connection_url():
    """Get the Neon database connection URL from environment variables."""
    return os.getenv('DATABASE_URL')

def create_sqlite_engine():
    """Create SQLite engine."""
    # Remove existing database file if it exists
    if os.path.exists('local_stock_management.db'):
        os.remove('local_stock_management.db')
    return create_engine('sqlite:///local_stock_management.db')

def get_all_tables(engine):
    """Get all table names from the database."""
    inspector = inspect(engine)
    return inspector.get_table_names()

def copy_table_data(source_engine, target_engine, table_name):
    """Copy data from source table to target table."""
    try:
        # Read data from source
        with source_engine.connect() as source_conn:
            result = source_conn.execute(text(f"SELECT * FROM {table_name}"))
            data = result.fetchall()
            if not data:
                logger.info(f"No data in table {table_name}")
                return
            columns = result.keys()

            # Insert data into target
            with target_engine.connect() as target_conn:
                insert_stmt = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(['?' for _ in columns])})"
                try:
                    target_conn.connection.executemany(insert_stmt, [tuple(row) for row in data])
                    target_conn.commit()
                    logger.info(f"Successfully copied table {table_name}")
                except Exception as e:
                    if "UNIQUE constraint failed" in str(e):
                        logger.warning(f"Skipping duplicate entries in table {table_name}: {str(e)}")
                    else:
                        raise e
    except Exception as e:
        logger.error(f"Error copying table {table_name}: {str(e)}")

def show_migration_status(success, message):
    """Display a window showing the migration status."""
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    if success:
        messagebox.showinfo("Migration Status", message)
    else:
        messagebox.showerror("Migration Status", message)
    root.destroy()

def main():
    # Get connection URLs
    neon_url = get_neon_connection_url()
    if not neon_url:
        logger.error("DATABASE_URL environment variable not found")
        show_migration_status(False, "DATABASE_URL environment variable not found")
        return

    # Create engines
    source_engine = create_engine(neon_url)
    target_engine = create_sqlite_engine()

    try:
        # Run schema generation script to create tables in SQLite
        logger.info("Generating SQLite schema...")
        subprocess.run(["python", "generate_sqlite_models.py"], check=True)

        # Get all tables
        tables = get_all_tables(source_engine)
        logger.info(f"Found {len(tables)} tables to migrate")

        # Copy each table
        for table in tables:
            logger.info(f"Migrating table: {table}")
            copy_table_data(source_engine, target_engine, table)

        logger.info("Migration completed successfully!")
        show_migration_status(True, "Migration completed successfully!")

    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        show_migration_status(False, f"Migration failed: {str(e)}")
    finally:
        source_engine.dispose()
        target_engine.dispose()

if __name__ == "__main__":
    main() 