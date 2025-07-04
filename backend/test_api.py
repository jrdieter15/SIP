import requests
import json

# Test the API endpoints
BASE_URL = "http://localhost:8000"

def test_health_check():
    response = requests.get(f"{BASE_URL}/health")
    print(f"Health check: {response.status_code} - {response.json()}")

def test_login():
    login_data = {
        "username": "admin",
        "password": "password"
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"Login: {response.status_code} - {response.json()}")
    
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def test_make_call(token):
    headers = {"Authorization": f"Bearer {token}"}
    call_data = {
        "from_number": "+1234567890",
        "to_number": "+0987654321"
    }
    response = requests.post(f"{BASE_URL}/calls/make", json=call_data, headers=headers)
    print(f"Make call: {response.status_code} - {response.json()}")

if __name__ == "__main__":
    print("Testing API endpoints...")
    test_health_check()
    token = test_login()
    if token:
        test_make_call(token)