import pymongo
from pymongo.errors import ConnectionFailure, OperationFailure
import json
from typing import List, Dict, Any, Optional

class MongoService:
    def __init__(self):
        self.client = None
        self.collection = None

    def connect(self, uri: str, db_name: str, collection_name: str) -> bool:
        """Establishes connection to the specific collection."""
        try:
            self.client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
            # Trigger a quick command to verify connection
            self.client.admin.command('ping')
            
            db = self.client[db_name]
            self.collection = db[collection_name]
            return True
        except Exception as e:
            raise ConnectionError(f"Failed to connect to MongoDB: {str(e)}")

    def fetch_documents(self, limit: int = 50) -> str:
        """
        Fetches documents and returns them as a JSON string.
        Handles ObjectId serialization automatically.
        """
        if self.collection is None:
            raise ConnectionError("Collection not initialized. Call connect() first.")

        try:
            cursor = self.collection.find().limit(limit)
            docs = list(cursor)
            
            # Serialize non-JSON serializable fields (like ObjectId)
            cleaned_docs = self._serialize_docs(docs)
            return json.dumps(cleaned_docs, indent=2)
        except Exception as e:
            raise RuntimeError(f"Error fetching data: {str(e)}")

    def _serialize_docs(self, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Helper to convert MongoDB types to strings."""
        for doc in docs:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
            # Add handlers for Dates or Binary data here if needed
        return docs