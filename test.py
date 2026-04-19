import sqlite3
import time
conn = sqlite3.connect('cricket_data.db')
start = time.time()
res = conn.execute("SELECT COUNT(*) FROM deliveries").fetchone()
dur = time.time() - start
print(res, dur)
