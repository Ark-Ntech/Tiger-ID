"""Manual test for search functionality"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path.parent))

from backend.database.sqlite_connection import get_sqlite_session
from backend.services.global_search_service import GlobalSearchService
from backend.database.models import Investigation, Tiger, Facility, Evidence

def test_search():
    """Test the search functionality"""
    print("=" * 60)
    print("Testing Search Functionality")
    print("=" * 60)
    
    with get_sqlite_session() as db:
        # Check what data exists
        inv_count = db.query(Investigation).count()
        tiger_count = db.query(Tiger).count()
        facility_count = db.query(Facility).count()
        evidence_count = db.query(Evidence).count()
        
        print(f"\nDatabase stats:")
        print(f"  Investigations: {inv_count}")
        print(f"  Tigers: {tiger_count}")
        print(f"  Facilities: {facility_count}")
        print(f"  Evidence: {evidence_count}")
        
        # Sample some data
        print("\n" + "-" * 60)
        print("Sample Facilities:")
        facilities = db.query(Facility).limit(3).all()
        for f in facilities:
            print(f"  - {f.exhibitor_name} ({f.city}, {f.state})")
        
        print("\n" + "-" * 60)
        print("Sample Tigers:")
        tigers = db.query(Tiger).limit(3).all()
        for t in tigers:
            name = t.name if hasattr(t, 'name') and t.name else "Unnamed"
            print(f"  - {name}")
        
        print("\n" + "-" * 60)
        print("Sample Investigations:")
        investigations = db.query(Investigation).limit(3).all()
        for inv in investigations:
            print(f"  - {inv.title}")
        
        # Test search service
        service = GlobalSearchService(db)
        
        # Test 1: Search for facilities
        print("\n" + "=" * 60)
        print("TEST 1: Search for 'zoo'")
        print("=" * 60)
        results = service.search(query="zoo", limit=5)
        print(f"\nTotal results: {results['total_results']}")
        print(f"  Investigations: {len(results['investigations'])}")
        print(f"  Tigers: {len(results['tigers'])}")
        print(f"  Facilities: {len(results['facilities'])}")
        print(f"  Evidence: {len(results['evidence'])}")
        
        if results['facilities']:
            print("\nFacility results:")
            for f in results['facilities'][:3]:
                print(f"  - {f['name']} ({f['city']}, {f['state']})")
                print(f"    ID: {f['id']}")
                print(f"    Entity Type: {f['entity_type']}")
        
        # Test 2: Search by state
        print("\n" + "=" * 60)
        print("TEST 2: Search for 'texas'")
        print("=" * 60)
        results = service.search(query="texas", limit=5)
        print(f"\nTotal results: {results['total_results']}")
        print(f"  Facilities: {len(results['facilities'])}")
        
        if results['facilities']:
            print("\nFacility results:")
            for f in results['facilities'][:3]:
                print(f"  - {f['name']} ({f['city']}, {f['state']})")
        
        # Test 3: Search tigers
        print("\n" + "=" * 60)
        print("TEST 3: Search for tigers (if any have names)")
        print("=" * 60)
        # Check if any tigers have names
        named_tigers = db.query(Tiger).filter(Tiger.name.isnot(None)).limit(1).all()
        if named_tigers and named_tigers[0].name:
            search_term = named_tigers[0].name.split()[0]  # Get first word
            print(f"Searching for: '{search_term}'")
            results = service.search(query=search_term, limit=5)
            print(f"\nTotal results: {results['total_results']}")
            print(f"  Tigers: {len(results['tigers'])}")
            
            if results['tigers']:
                print("\nTiger results:")
                for t in results['tigers'][:3]:
                    print(f"  - {t.get('name', 'Unnamed')}")
                    print(f"    ID: {t['id']}")
        else:
            print("No named tigers found in database")
        
        # Test 4: Search investigations
        print("\n" + "=" * 60)
        print("TEST 4: Search investigations")
        print("=" * 60)
        if inv_count > 0:
            inv = db.query(Investigation).first()
            if inv and inv.title:
                search_term = inv.title.split()[0]  # Get first word
                print(f"Searching for: '{search_term}'")
                results = service.search(query=search_term, limit=5)
                print(f"\nTotal results: {results['total_results']}")
                print(f"  Investigations: {len(results['investigations'])}")
                
                if results['investigations']:
                    print("\nInvestigation results:")
                    for i in results['investigations'][:3]:
                        print(f"  - {i['title']}")
                        print(f"    ID: {i['id']}")
                        print(f"    Status: {i['status']}")
        else:
            print("No investigations found in database")
        
        print("\n" + "=" * 60)
        print("Search tests completed!")
        print("=" * 60)

if __name__ == "__main__":
    test_search()

