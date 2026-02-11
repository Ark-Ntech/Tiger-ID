"""Verify the API would return proper lat/lng for facilities."""
import json
import sqlite3
import sys

conn = sqlite3.connect('data/tiger_id.db')
cursor = conn.cursor()

# Simulate API response
cursor.execute("""
    SELECT facility_id, exhibitor_name, state, coordinates
    FROM facilities
    WHERE coordinates IS NOT NULL AND coordinates != ''
""")

total_with_coords = 0
total_without = 0
sample = []

for fid, name, state, coords_str in cursor.fetchall():
    lat, lon = None, None
    if coords_str:
        try:
            coords = json.loads(coords_str)
            lat = coords.get("latitude")
            lon = coords.get("longitude")
        except Exception:
            pass

    if lat is not None and lon is not None:
        total_with_coords += 1
        if len(sample) < 3:
            sample.append({"name": name, "state": state, "latitude": lat, "longitude": lon})
    else:
        total_without += 1

cursor.execute("SELECT COUNT(*) FROM facilities WHERE coordinates IS NULL OR coordinates = ''")
no_coords = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM facilities")
total = cursor.fetchone()[0]

print("=== API FACILITY RESPONSE VERIFICATION ===")
print(f"Total facilities:              {total}")
print(f"Will have lat/lng in API:      {total_with_coords}")
print(f"Missing coordinates in DB:     {no_coords}")
print(f"Have coords but parse failed:  {total_without}")
print()
print("Sample API responses:")
for s in sample:
    print(f"  {json.dumps(s, indent=4)}")

# Verify frontend expectations
print()
print("=== FRONTEND COMPATIBILITY CHECK ===")
print("Frontend Facility type expects: latitude?: number, longitude?: number")
print(f"Backend returns: latitude={type(sample[0]['latitude']).__name__}, longitude={type(sample[0]['longitude']).__name__}")
print("PASS" if isinstance(sample[0]['latitude'], (int, float)) and isinstance(sample[0]['longitude'], (int, float)) else "FAIL")

# Verify map component filter
print()
print("=== MAP COMPONENT CHECK ===")
print(f"FacilityMapView filters: f.latitude !== undefined && f.longitude !== undefined")
print(f"Facilities that will show on map: {total_with_coords}")
print(f"Facilities missing from map: {no_coords + total_without}")

conn.close()
sys.exit(0)
