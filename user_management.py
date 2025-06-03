import sqlite3
import hashlib
import secrets
import time
from datetime import datetime, timedelta

class UserManager:
    def __init__(self, db_path='stock.db'):
        self.db_path = db_path
        self.create_tables()
        self.sessions = {}  # In-memory session storage

    def create_tables(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create sessions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        conn.commit()
        conn.close()

    def hash_password(self, password):
        """Hash a password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def create_user(self, username, password, role='user'):
        """Create a new user."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            password_hash = self.hash_password(password)
            cursor.execute(
                'INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)',
                (username, password_hash, role)
            )
            
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # Username already exists
        finally:
            conn.close()

    def verify_user(self, username, password):
        """Verify user credentials."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        password_hash = self.hash_password(password)
        cursor.execute(
            'SELECT id, username, role FROM users WHERE username = ? AND password_hash = ?',
            (username, password_hash)
        )
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'username': user[1],
                'role': user[2]
            }
        return None

    def create_session(self, user_id):
        """Create a new session for a user."""
        token = secrets.token_hex(32)
        expires_at = datetime.now() + timedelta(hours=24)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)',
            (token, user_id, expires_at)
        )
        
        conn.commit()
        conn.close()
        
        return token

    def verify_session(self, token):
        """Verify a session token and return the associated user."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.id, u.username, u.role 
            FROM users u 
            JOIN sessions s ON u.id = s.user_id 
            WHERE s.token = ? AND s.expires_at > ?
        ''', (token, datetime.now()))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'username': user[1],
                'role': user[2]
            }
        return None

    def delete_session(self, token):
        """Delete a session."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM sessions WHERE token = ?', (token,))
        
        conn.commit()
        conn.close()

    def cleanup_expired_sessions(self):
        """Remove expired sessions from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM sessions WHERE expires_at <= ?', (datetime.now(),))
        
        conn.commit()
        conn.close()

# Create a global instance of UserManager
user_manager = UserManager() 