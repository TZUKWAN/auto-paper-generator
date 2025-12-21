import requests
import json

def test_searxng():
    url = "http://localhost:8080/search"
    query = "test"
    
    # 模拟 core/external_search.py 中的请求参数 (format=json)
    params = {
        "q": query,
        "format": "json",
        "pageno": 1,
        "language": "zh-CN"
    }
    
    # 模拟当前的 headers
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    print(f"Testing URL: {url}")
    print(f"Headers: {headers}")
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("Success!")
            # print(response.json())
        else:
            print("Failed.")
            print(response.text[:500])
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_searxng()
