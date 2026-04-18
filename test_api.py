import requests
import time
import subprocess
import sys

def test_api():
    """
    Test the Address Verification API.
    Ensure you have the FastAPI server running first:
    'python main.py' or 'uvicorn main:app --reload'
    """
    # Example address to verify
    address = {
        "street": "123 main street",
        "city": "new york",
        "state": "ny",
        "zip_code": "10001",
        "country": "usa"
    }

    # Headers with API Key
    headers = {
        "X-API-Key": "your-secret-key-123"
    }

    print(f"Testing with address: {address}")
    
    try:
        response = requests.post("http://localhost:8001/verify", json=address, headers=headers)
        if response.status_code == 200:
            result = response.json()
            print("\n--- API Response ---")
            print(f"Status: {response.status_code}")
            print(f"Is Valid: {result['is_valid']}")
            print(f"Standardized Address: {result['formatted_address']}")
            print(f"Confidence Score: {result['confidence_score']}")
            print("--------------------\n")
        else:
            print(f"Error: Received status code {response.status_code}")
            print(response.text)
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the API. Is the server running?")

if __name__ == "__main__":
    test_api()
