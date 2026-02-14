import bcrypt
import pymongo
import re
from datetime import datetime, timezone, timedelta
from cryptography.fernet import Fernet
from src.config import AppConfig

class UserService:
    def __init__(self):
        AppConfig.validate_secrets()
        self.client = pymongo.MongoClient(AppConfig.MASTER_MONGO_URI)
        self.db = self.client["mongochat_master"]
        self.users_col = self.db["users"]
        
        # Ensure encryption key is bytes
        key = AppConfig.ENCRYPTION_KEY
        if isinstance(key, str):
            key = key.encode()
        self.cipher = Fernet(key)

    def create_user(self, email, username, password):
        """Register a new user."""
        # 1. Basic Email Validation
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_regex, email):
            raise ValueError("Invalid email format.")

        if self.users_col.find_one({"email": email}):
            raise ValueError("User with this email already exists.")
            
        # 2. Hash Password
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        user_doc = {
            "email": email,
            "username": username,
            "password_hash": hashed_pw,
            "created_at": datetime.now(timezone.utc),
            # Usage Tracking
            "message_count": 0,
            "last_reset_time": datetime.now(timezone.utc),
            # Saved Config Placeholders
            "saved_mongo_uri": None, 
            "saved_db_name": None,
            "saved_collection": None
        }
        self.users_col.insert_one(user_doc)
        return True

    def verify_user(self, email, password):
        """Login check."""
        user = self.users_col.find_one({"email": email})
        if not user:
            return None
        
        if bcrypt.checkpw(password.encode('utf-8'), user["password_hash"]):
            return user
        return None

    def save_user_config(self, email, mongo_uri, db_name, col_name):
        """Encrypts and saves the user's connection details."""
        if not mongo_uri:
            return
            
        encrypted_uri = self.cipher.encrypt(mongo_uri.encode())
        
        self.users_col.update_one(
            {"email": email},
            {"$set": {
                "saved_mongo_uri": encrypted_uri,
                "saved_db_name": db_name,
                "saved_collection": col_name
            }}
        )

    def get_user_config(self, email):
        """Retrieves and decrypts user config."""
        user = self.users_col.find_one({"email": email})
        if not user or not user.get("saved_mongo_uri"):
            return None
            
        try:
            decrypted_uri = self.cipher.decrypt(user["saved_mongo_uri"]).decode()
            return {
                "mongo_uri": decrypted_uri,
                "db_name": user.get("saved_db_name"),
                "collection": user.get("saved_collection")
            }
        except Exception:
            return None

    def get_usage_stats(self, email):
        """
        Checks usage limits. 
        If > 24 hours since last reset, resets count to 0.
        Returns: (current_count, max_limit, hours_until_reset)
        """
        user = self.users_col.find_one({"email": email})
        if not user:
            return 0, AppConfig.MAX_FREE_MESSAGES, 0

        last_reset = user.get("last_reset_time", datetime.now(timezone.utc))
        if last_reset.tzinfo is None:
            last_reset = last_reset.replace(tzinfo=timezone.utc)
            
        now = datetime.now(timezone.utc)
        time_diff = now - last_reset
        
        # Reset if > 24 hours
        if time_diff > timedelta(hours=24):
            self.users_col.update_one(
                {"email": email},
                {"$set": {"message_count": 0, "last_reset_time": now}}
            )
            return 0, AppConfig.MAX_FREE_MESSAGES, 24
        
        hours_left = 24 - (time_diff.total_seconds() / 3600)
        current_count = user.get("message_count", 0)
        
        return current_count, AppConfig.MAX_FREE_MESSAGES, max(0, hours_left)

    def increment_usage(self, email):
        """Increments the message counter by 1."""
        self.users_col.update_one(
            {"email": email},
            {"$inc": {"message_count": 1}}
        )

    def get_global_daily_usage(self):
        """
        Returns the total number of AI requests made by ALL users today.
        """
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        # We use a collection called 'system_stats'
        stats_col = self.db["system_stats"]
        
        doc = stats_col.find_one({"date": today_str})
        if not doc:
            # Initialize for today
            stats_col.insert_one({"date": today_str, "count": 0})
            return 0
            
        return doc["count"]

    def increment_global_usage(self):
        """Increments the global counter for today."""
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        stats_col = self.db["system_stats"]
        
        stats_col.update_one(
            {"date": today_str},
            {"$inc": {"count": 1}},
            upsert=True
        )