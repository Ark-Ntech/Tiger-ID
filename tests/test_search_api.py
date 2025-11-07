"""Test search API endpoint"""
import requests
import json
from datetime import datetime, timedelta
import jwt

# Configuration
API_BASE_URL = "http://localhost:8000"
SECRET_KEY = "change-me-in-production"  # This should match your backend config

def create_test_token():
    """Create a test JWT token"""
    payload = {
        "sub": "admin",
        "user_id": "68229ac9-2850-47f0-bc1d-464756bb66c0",
        "role": "admin",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

def test_search_api():
    """Test the search API"""
    print("=" * 60)
    print("Testing Search API")
    print("=" * 60)
    
    # Create auth token
    token = create_test_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test 1: Search for facilities
    print("\nTEST 1: Search for 'zoo'")
    print("-" * 60)
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/search/global",
            params={"q": "zoo", "limit": 5},
            headers=headers
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response structure keys: {list(data.keys())}")
            print(f"Response has 'data' field: {'data' in data}")
            print(f"Response has 'success' field: {'success' in data}")
            
            # Handle both direct results and SuccessResponse wrapper
            results = data.get('data', data)
            
            print(f"\nResults keys: {list(results.keys())}")
            print(f"Total results: {results.get('total_results', 0)}")
            print(f"  Investigations: {len(results.get('investigations', []))}")
            print(f"  Tigers: {len(results.get('tigers', []))}")
            print(f"  Facilities: {len(results.get('facilities', []))}")
            print(f"  Evidence: {len(results.get('evidence', []))}")
            
            if results.get('facilities'):
                print("\nFacility results:")
                for f in results['facilities'][:3]:
                    print(f"  - {f['name']} ({f['city']}, {f['state']})")
                    print(f"    Has 'id' field: {'id' in f}")
                    print(f"    Has 'entity_id' field: {'entity_id' in f}")
        else:
            print(f"Error: {response.text}")
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to API. Is the server running?")
        print(f"Make sure the backend is running at {API_BASE_URL}")
        return
    except Exception as e:
        print(f"ERROR: {e}")
        return
    
    # Test 2: Search for tigers
    print("\n" + "=" * 60)
    print("TEST 2: Search for 'ATRW'")
    print("-" * 60)
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/search/global",
            params={"q": "ATRW", "limit": 5},
            headers=headers
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('data', data)
            
            print(f"\nTotal results: {results.get('total_results', 0)}")
            print(f"  Tigers: {len(results.get('tigers', []))}")
            
            if results.get('tigers'):
                print("\nTiger results:")
                for t in results['tigers'][:3]:
                    print(f"  - {t.get('name', 'Unnamed')}")
                    print(f"    Has 'id' field: {'id' in t}")
                    print(f"    Has 'images' field: {'images' in t}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Test 3: Search with entity type filter
    print("\n" + "=" * 60)
    print("TEST 3: Search for 'texas' (facilities only)")
    print("-" * 60)
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/search/global",
            params={"q": "texas", "entity_types": "facilities", "limit": 5},
            headers=headers
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('data', data)
            
            print(f"\nTotal results: {results.get('total_results', 0)}")
            print(f"  Facilities: {len(results.get('facilities', []))}")
            
            if results.get('facilities'):
                print("\nFacility results:")
                for f in results['facilities'][:3]:
                    print(f"  - {f['name']}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("API tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_search_api()

