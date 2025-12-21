import requests

def test_searxng_html():
    url = "http://localhost:8080/search"
    query = "test"
    
    # 不加 format=json，默认HTML
    params = {
        "q": query,
        "pageno": 1,
        "language": "zh-CN"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    print(f"Testing URL (HTML): {url}")
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("Success!")
            print(f"Content length: {len(response.text)}")
        else:
            print("Failed.")
            print(response.text[:500])
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_searxng_html()
