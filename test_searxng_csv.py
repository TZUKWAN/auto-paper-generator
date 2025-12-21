import requests

def test_searxng_csv():
    url = "http://localhost:8080/search"
    query = "test"
    
    params = {
        "q": query,
        "format": "csv",
        "pageno": 1,
        "language": "zh-CN"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    print(f"Testing URL (CSV): {url}")
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("Success!")
            print(f"Content length: {len(response.text)}")
            print(response.text[:500])
        else:
            print("Failed.")
            print(response.text[:500])
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_searxng_csv()
