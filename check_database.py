
import sqlite3

connection = sqlite3.connect("wildlife.db")
cursor = connection.cursor()

print("========== DATABASE CHECK ==========")

print("\nTABLES:")
tables = cursor.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
).fetchall()
print(tables)

print("\nDETECTIONS COLUMNS:")
columns = cursor.execute(
    "PRAGMA table_info(detections)"
).fetchall()
for column in columns:
    print(column)

print("\nTOTAL DETECTIONS:")
total = cursor.execute(
    "SELECT COUNT(*) FROM detections"
).fetchone()[0]
print(total)

connection.close()

print("\nDATABASE CHECK COMPLETE!")
