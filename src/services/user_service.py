import bcrypt
import pymongo
from datetime import datetime, timezone
from cryptography.fernet import Fernet
from src.config import AppConfig

class UserService:
    def __init__(self):
        # Validate keys exist before connecting
        AppConfig.validate_secrets()

        self.client = pymongo.MongoClient(AppConfig.MASTER_MONGO_URI)
        self.db = self.client["mongochat_master"]
        self.users_col = self.db["users"]
        
        # FIX: Ensure key is bytes for Fernet
        key = AppConfig.ENCRYPTION_KEY
        if isinstance(key, str):
            key = key.encode() # Fernet prefers bytes
            
        self.cipher = Fernet(key) # <--- No more type error

    def create_user(self, email, username, password):
        """Register a new user."""
        if self.users_col.find_one({"email": email}):
            raise ValueError("User with this email already exists.")
            
        # Hash Password
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        user_doc = {
            "email": email,
            "username": username,
            "password_hash": hashed_pw,
            "created_at": datetime.now(timezone.utc),
            # Placeholders for their saved config
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
        # Encrypt the URI
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
            # Decrypt URI
            decrypted_uri = self.cipher.decrypt(user["saved_mongo_uri"]).decode()
            return {
                "mongo_uri": decrypted_uri,
                "db_name": user["saved_db_name"],
                "collection": user["saved_collection"]
            }
        except Exception:
            return None