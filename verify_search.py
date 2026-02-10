import requests
import sys

try:
    response = requests.get("http://127.0.0.1:8001/api/products/search?q=iphone")
    if response.status_code == 200:
        print("Success: Search returned 200 OK")
        print(response.json()[:1]) # Print first result summary
    else:
        print(f"Failed: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"Error: {e}")
