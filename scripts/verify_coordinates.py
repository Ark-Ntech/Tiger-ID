"""Verify facility coordinates were properly seeded."""
import json
import sqlite3

conn = sqlite3.connect('data/tiger_id.db')
cursor = conn.cursor()

# Count facilities with coordinates
cursor.execute("SELECT COUNT(*) FROM facilities WHERE coordinates IS NOT NULL AND coordinates != ''")
with_coords = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM facilities")
total = cursor.fetchone()[0]

print(f"Facilities with coordinates: {with_coords}/{total}")
print()

# Verify coordinate data structure
cursor.execute("SELECT facility_id, exhibitor_name, state, coordinates FROM facilities WHERE coordinates IS NOT NULL AND coordinates != '' LIMIT 5")
for fid, name, state, coords_str in cursor.fetchall():
    coords = json.loads(coords_str)
    print(f"  {name[:45]:45s} ({state})")
    print(f"    latitude:   {coords.get('latitude')}")
    print(f"    longitude:  {coords.get('longitude')}")
    print(f"    confidence: {coords.get('confidence')}")
    print(f"    source:     {coords.get('source')}")
    print()

# Confidence distribution
cursor.execute("SELECT coordinates FROM facilities WHERE coordinates IS NOT NULL AND coordinates != ''")
confidence_counts = {"high": 0, "medium": 0, "low": 0, "unknown": 0}
for (coords_str,) in cursor.fetchall():
    try:
        coords = json.loads(coords_str)
        conf = coords.get("confidence", "unknown")
        confidence_counts[conf] = confidence_counts.get(conf, 0) + 1
    except Exception:
        confidence_counts["unknown"] += 1

print("Confidence distribution:")
for conf, count in sorted(confidence_counts.items()):
    print(f"  {conf:10s}: {count}")

# Check facilities without coordinates
cursor.execute("SELECT exhibitor_name, state FROM facilities WHERE coordinates IS NULL OR coordinates = ''")
missing = cursor.fetchall()
print(f"\nFacilities without coordinates ({len(missing)}):")
for name, state in missing:
    print(f"  {name} (state={state})")

# Test that the API response would have lat/lng
cursor.execute("SELECT exhibitor_name, coordinates FROM facilities WHERE coordinates IS NOT NULL LIMIT 3")
print("\nSimulated API response fields:")
for name, coords_str in cursor.fetchall():
    coords = json.loads(coords_str)
    lat = coords.get("latitude")
    lon = coords.get("longitude")
    print(f"  {name[:35]:35s} -> latitude={lat}, longitude={lon}")

conn.close()
