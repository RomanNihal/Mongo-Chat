import time
import threading
import streamlit as st
from datetime import datetime
from src.config import AppConfig
from src.services.user_service import UserService

class RateLimiter:
    def __init__(self):
        self.lock = threading.Lock()
        self.rpm_requests = []  # Memory (Fast)
        # We don't store daily_count here anymore; we ask DB.

    def _cleanup_old_requests(self):
        """Remove requests older than 60 seconds."""
        now = time.time()
        self.rpm_requests = [t for t in self.rpm_requests if now - t < 60]

    def check_limits(self):
        """
        Checks both RPM (Memory) and RPD (Database).
        Returns: "OK", "RPM_LIMIT", or "DAILY_LIMIT"
        """
        with self.lock:
            self._cleanup_old_requests()
            
            # 1. Check RPM (Memory)
            if len(self.rpm_requests) >= AppConfig.MAX_RPM:
                return "RPM_LIMIT"

            # 2. Check RPD (Database)
            # We create a service instance just for this check
            try:
                user_svc = UserService()
                current_daily = user_svc.get_global_daily_usage()
                
                if current_daily >= AppConfig.MAX_RPD:
                    return "DAILY_LIMIT"
                    
            except Exception as e:
                # If DB fails, fail safe (allow request or block? Block is safer)
                print(f"Rate Limit DB Error: {e}")
                return "DAILY_LIMIT" # Block to be safe

            return "OK"

    def record_request(self):
        """Call this ONLY after a successful API call."""
        with self.lock:
            # 1. Record for RPM
            self.rpm_requests.append(time.time())
            
            # 2. Record for RPD
            try:
                user_svc = UserService()
                user_svc.increment_global_usage()
            except Exception:
                pass

# Singleton
@st.cache_resource
def get_rate_limiter():
    return RateLimiter()