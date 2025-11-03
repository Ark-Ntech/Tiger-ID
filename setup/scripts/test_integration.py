#!/usr/bin/env python3
"""Integration tests for frontend-backend communication"""

import sys
from pathlib import Path
import requests

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

API_URL = "http://localhost:8000"


class IntegrationTester:
    def __init__(self):
        self.token = None
        self.session = requests.Session()
        self.results = []
        
    def log(self, message, success=None):
        prefix = "✅ " if success is True else "❌ " if success is False else "ℹ️  "
        print(f"{prefix}{message}")
        self.results.append((message, success))
    
    def test_api_health(self):
        try:
            response = self.session.get(f"{API_URL}/api/v1/health")
            if response.status_code == 200:
                self.log("API health check", True)
                return True
            else:
                self.log(f"API health check (status: {response.status_code})", False)
                return False
        except Exception as e:
            self.log(f"API connection failed: {e}", False)
            return False
    
    def test_login(self):
        try:
            response = self.session.post(
                f"{API_URL}/api/auth/login",
                json={"username": "admin", "password": "admin", "remember_me": False}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                self.log("Login successful", True)
                return True
            else:
                self.log(f"Login failed (status: {response.status_code})", False)
                return False
        except Exception as e:
            self.log(f"Login error: {e}", False)
            return False
    
    def test_dashboard_stats(self):
        if not self.token:
            return False
        try:
            response = self.session.get(f"{API_URL}/api/v1/dashboard/stats")
            if response.status_code == 200:
                self.log("Dashboard stats", True)
                return True
            else:
                self.log(f"Dashboard stats failed", False)
                return False
        except Exception as e:
            self.log(f"Dashboard error: {e}", False)
            return False
    
    def run_all_tests(self):
        print("\n" + "="*60)
        print("🧪 Tiger ID - Integration Tests")
        print("="*60 + "\n")
        
        if not self.test_api_health():
            print("\n❌ API not accessible. Start backend first.")
            return False
        
        self.test_login()
        self.test_dashboard_stats()
        
        print("\n" + "="*60)
        passed = sum(1 for _, s in self.results if s is True)
        failed = sum(1 for _, s in self.results if s is False)
        print(f"✅ Passed: {passed} | ❌ Failed: {failed}")
        print("="*60 + "\n")
        
        return failed == 0


if __name__ == "__main__":
    tester = IntegrationTester()
    sys.exit(0 if tester.run_all_tests() else 1)

