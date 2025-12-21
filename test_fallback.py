from core.external_search import SearXNGSearcher
import logging

logging.basicConfig(level=logging.INFO)

def test_fallback():
    searcher = SearXNGSearcher()
    # 这里的search内部会自动检测403并尝试HTML fallback
    results = searcher.search("test")
    
    print(f"Got {len(results)} results")
    if results:
        print("First result:", results[0])

if __name__ == "__main__":
    test_fallback()
