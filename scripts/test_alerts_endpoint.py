import requests

def main():
    url = "http://localhost:5000/api/alerts"
    try:
        print(f"Making GET request to: {url}")
        res = requests.get(url)
        print(f"Status Code: {res.status_code}")
        try:
            data = res.json()
            import pprint
            pprint.pprint(data)
        except Exception:
            print("Raw text response:", res.text)
    except Exception as e:
        print("HTTP request failed:", e)

if __name__ == "__main__":
    main()
