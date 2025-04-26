import csv
import os
from dotenv import load_dotenv
from flask_login import UserMixin
from werkzeug.security import check_password_hash
import logging
load_dotenv()

logger = logging.getLogger(__name__)
USERS_FILE = os.getenv("OWNER_IDS_RECORD")

class User(UserMixin):
    def __init__(self, username, password_hash):
        self.id = username # Flask-Login uses get_id(), which defaults to self.id
        self.username = username
        self.password_hash = password_hash

    def check_password(self, password):
        """Checks if the provided password matches the stored hash."""
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def get(user_id):
        """Loads a user by username (user_id) from the CSV file."""
        if not os.path.exists(USERS_FILE):
            logger.error(f"Users file not found: {USERS_FILE}")
            return None
        try:
            with open(USERS_FILE, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['username'] == user_id:
                        return User(row['username'], row['password_hash'])
        except FileNotFoundError:
            logger.error(f"Users file not found during get: {USERS_FILE}")
            return None
        except Exception as e:
             logger.exception(f"Error reading users file {USERS_FILE}: {e}")
             return None
        return None # User not found