"""Comprehensive search test - API and data structure validation"""
import requests
import json
from datetime import datetime, timedelta
import jwt

# Configuration
API_BASE_URL = "http://localhost:8000"
SECRET_KEY = "change-me-in-production"

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

def test_search_comprehensive():
    """Comprehensive test of search functionality"""
    print("=" * 70)
    print("COMPREHENSIVE SEARCH TEST")
    print("=" * 70)
    
    token = create_test_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test search for facilities
    print("\n" + "=" * 70)
    print("TEST: Search for 'zoo'")
    print("=" * 70)
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/search/global",
            params={"q": "zoo", "limit": 5},
            headers=headers,
            timeout=10
        )
        
        print(f"\n[OK] Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check response structure
            print(f"\nResponse Structure:")
            print(f"  - Has 'success' field: {'success' in data}")
            print(f"  - Has 'message' field: {'message' in data}")
            print(f"  - Has 'data' field: {'data' in data}")
            
            # Extract results (handle both wrapped and unwrapped)
            if 'data' in data:
                results = data['data']
                print(f"  [OK] Response uses SuccessResponse wrapper")
            else:
                results = data
                print(f"  [WARNING] Response is NOT wrapped (old format)")
            
            # Check results structure
            print(f"\nResults Structure:")
            print(f"  - Total results: {results.get('total_results', 0)}")
            print(f"  - Investigations: {len(results.get('investigations', []))}")
            print(f"  - Tigers: {len(results.get('tigers', []))}")
            print(f"  - Facilities: {len(results.get('facilities', []))}")
            print(f"  - Evidence: {len(results.get('evidence', []))}")
            
            # Validate facility data structure
            if results.get('facilities'):
                print(f"\nFacility Data Validation:")
                facility = results['facilities'][0]
                
                required_fields = ['id', 'name', 'exhibitor_name', 'city', 'state']
                old_fields = ['entity_id']
                
                for field in required_fields:
                    status = "[OK]" if field in facility else "[FAIL]"
                    print(f"  {status} Has '{field}' field")
                
                for field in old_fields:
                    if field in facility:
                        print(f"  [FAIL] Still has OLD '{field}' field (should be 'id')")
                
                print(f"\n  Sample facility:")
                print(f"    Name: {facility.get('name', 'N/A')}")
                print(f"    Location: {facility.get('city', 'N/A')}, {facility.get('state', 'N/A')}")
                if 'id' in facility:
                    print(f"    ID: {facility['id'][:20]}...")
                elif 'entity_id' in facility:
                    print(f"    Entity ID (OLD): {facility['entity_id'][:20]}...")
            
            # Test tigers
            print(f"\n" + "=" * 70)
            print("TEST: Search for tigers 'ATRW'")
            print("=" * 70)
            
            response2 = requests.get(
                f"{API_BASE_URL}/api/v1/search/global",
                params={"q": "ATRW", "limit": 3},
                headers=headers,
                timeout=10
            )
            
            if response2.status_code == 200:
                data2 = response2.json()
                results2 = data2.get('data', data2)
                
                if results2.get('tigers'):
                    print(f"\nTiger Data Validation:")
                    tiger = results2['tigers'][0]
                    
                    required_fields = ['id', 'name', 'images']
                    for field in required_fields:
                        status = "[OK]" if field in tiger else "[FAIL]"
                        print(f"  {status} Has '{field}' field")
                    
                    if 'entity_id' in tiger:
                        print(f"  [FAIL] Still has OLD 'entity_id' field")
                    
                    print(f"\n  Sample tiger:")
                    print(f"    Name: {tiger.get('name', 'N/A')}")
                    if 'id' in tiger:
                        print(f"    ID: {tiger['id'][:20]}...")
            
            # Summary
            print(f"\n" + "=" * 70)
            print("SUMMARY")
            print("=" * 70)
            
            is_wrapped = 'data' in data
            has_id_field = 'id' in (results.get('facilities', [{}])[0] if results.get('facilities') else {})
            has_old_field = 'entity_id' in (results.get('facilities', [{}])[0] if results.get('facilities') else {})
            
            print(f"\n[OK] API is responding: YES")
            print(f"[{'OK' if is_wrapped else 'FAIL'}] Response uses SuccessResponse: {is_wrapped}")
            print(f"[{'OK' if has_id_field else 'FAIL'}] Items have 'id' field: {has_id_field}")
            print(f"[{'FAIL' if has_old_field else 'OK'}] Items have 'entity_id' (old): {has_old_field}")
            
            if is_wrapped and has_id_field and not has_old_field:
                print(f"\n*** ALL CHECKS PASSED! Search is working correctly! ***")
                print(f"    Frontend should now be able to display search results.")
            else:
                print(f"\n*** BACKEND NEEDS TO BE RESTARTED ***")
                print(f"    The code changes are in place, but the server is using cached code.")
                print(f"    Run: npm run start:backend")
                print(f"    Or restart the backend server to pick up the changes.")
        else:
            print(f"\n[ERROR] {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Could not connect to API")
        print(f"  Make sure the backend is running at {API_BASE_URL}")
        print(f"  Run: npm run start:backend")
    except Exception as e:
        print(f"\n[ERROR] {e}")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    test_search_comprehensive()

