import requests
import json

def test_search():
    url = "http://127.0.0.1:8003/api/products/search?q=iphone+15+pro"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data)} products.")
            if data:
                print("First product sample:")
                print(json.dumps(data[0], indent=2))
                if 'image_url' in data[0]:
                    print(f"Image URL present: {data[0]['image_url']}")
                else:
                    print("Image URL MISSING in response!")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_search()
