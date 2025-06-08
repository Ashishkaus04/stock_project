import hashlib
import secrets
from datetime import datetime, timedelta

from app.database import db # Import the db module

# Assuming db module provides functions for database interaction

class UserManager:
    def __init__(self):
        self.sessions = {}  # In-memory session storage (can be moved to db for persistence)

    def hash_password(self, password):
        """Hash a password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def create_user(self, username, password, role='user'):
        """Create a new user using the database module."""
        password_hash = self.hash_password(password)
        return db.add_user_to_db(username, password_hash, role)

    def verify_user(self, username, password):
        """Verify user credentials using the database module."""
        print(f"Attempting to verify user: {username}") # Debug print
        password_hash = self.hash_password(password)
        print(f"Generated password hash for '{username}': {password_hash}") # Debug print
        user = db.get_user_by_credentials(username, password_hash)
        
        if user:
            print(f"User '{username}' verified successfully.") # Debug print
            return {
                'id': user[0],
                'username': user[1],
                'role': user[2]
            }
        print(f"User '{username}' verification failed.") # Debug print
        return None

    def create_session(self, user_id):
        """Create a new session for a user."""
        token = secrets.token_hex(32)
        expires_at = datetime.now() + timedelta(hours=24)
        
        return db.add_session_to_db(token, user_id, expires_at)

    def verify_session(self, token):
        """Verify a session token and return the associated user."""
        session_data = db.get_session_from_db(token)
        
        if session_data:
            user_id = session_data[0] # Assuming first element is user_id
            user = db.get_user_by_id(user_id)
            if user:
                return {
                    'id': user[0],
                    'username': user[1],
                    'role': user[2]
                }
        return None

    def delete_session(self, token):
        """Delete a session."""
        db.remove_session_from_db(token)

    def cleanup_expired_sessions(self):
        """Remove expired sessions from the database."""
        db.remove_expired_sessions()

# Create a global instance of UserManager
user_manager = UserManager() 