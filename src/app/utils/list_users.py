import sqlite3

def list_users(db_path='stock.db'):
    """Connects to the SQLite database and lists all users with their IDs."""
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, username, role FROM users')
        users = cursor.fetchall()
        
        if users:
            print("User ID | Username | Role")
            print("---------------------------")
            for user in users:
                print(f"{user[0]:<7} | {user[1]:<9} | {user[2]}")
        else:
            print("No users found in the database.")
            
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    list_users() 