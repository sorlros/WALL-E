import requests
import json
import uuid

# Backend URL
BASE_URL = "http://127.0.0.1:8000"

def test_auth_flow():
    print(f"Talking to backend at: {BASE_URL}")

    # Generate random email to avoid conflicts
    unique_suffix = str(uuid.uuid4())[:8]
    email = f"wall.e.tester+{unique_suffix}@gmail.com"
    password = "TestPassword123!"
    name = "Test User"

    print(f"Testing with Email: {email}")

    # 1. Sign Up
    print("\n--- 1. Testing Sign Up ---")
    signup_payload = {
        "email": email,
        "password": password,
        "name": name
    }
    try:
        signup_res = requests.post(f"{BASE_URL}/auth/signup", json=signup_payload)
        print(f"Status Code: {signup_res.status_code}")
        if signup_res.status_code == 200:
            print("Response:", json.dumps(signup_res.json(), indent=2))
        else:
            print("Error Response:", signup_res.text)
    except Exception as e:
        print(f"Request Failed: {e}")
        return

    # 2. Login
    print("\n--- 2. Testing Login ---")
    login_payload = {
        "email": email,
        "password": password
    }
    try:
        login_res = requests.post(f"{BASE_URL}/auth/login", json=login_payload)
        print(f"Status Code: {login_res.status_code}")
        if login_res.status_code == 200:
            data = login_res.json()
            print("Login Successful!")
            print(f"Access Token (len={len(data.get('access_token', ''))}): {data.get('access_token')[:20]}...")
            print(f"User Email: {data.get('user', {}).get('email')}")
        else:
            print("Login Failed:", login_res.text)
    except Exception as e:
        print(f"Request Failed: {e}")

if __name__ == "__main__":
    test_auth_flow()
