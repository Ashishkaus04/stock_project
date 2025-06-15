import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'inventory.db')

def get_schema(table_name):
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        schema = cursor.fetchall()
        print(f"Schema for table {table_name}:")
        for col in schema:
            print(col)
    except Exception as e:
        print(f"Error getting schema: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    get_schema("quantity_history") 