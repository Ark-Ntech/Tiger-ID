"""Quick script to inspect facility data in the database."""
import sqlite3

conn = sqlite3.connect('data/tiger_id.db')
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM facilities WHERE city IS NOT NULL AND city != ''")
print(f"Facilities with city: {cursor.fetchone()[0]}")

cursor.execute("SELECT exhibitor_name, city, state, address FROM facilities LIMIT 20")
rows = cursor.fetchall()
print()
for r in rows:
    name = str(r[0])[:42] if r[0] else "None"
    city = str(r[1])[:15] if r[1] else "None"
    state = str(r[2]) if r[2] else "None"
    addr = str(r[3])[:25] if r[3] else "None"
    print(f"  {name:42s} | city={city:15s} state={state:5s} addr={addr}")

# Check those with NULL state
cursor.execute("SELECT exhibitor_name, city, state, address FROM facilities WHERE state IS NULL")
nullrows = cursor.fetchall()
print(f"\n=== FACILITIES WITH NO STATE ({len(nullrows)}) ===")
for r in nullrows:
    print(f"  {r[0]}")

conn.close()
