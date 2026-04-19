import sqlite3

# 1. Connect to the CORRECT database (the one that actually has your data)
conn = sqlite3.connect('cricket_data.db')
cursor = conn.cursor()

# 2. Drop the view if it already exists (to avoid errors if you run this multiple times)
cursor.execute("DROP VIEW IF EXISTS v_player_matchups")

# 3. Create the view
cursor.execute('''
CREATE VIEW v_player_matchups AS
SELECT 
    batter, 
    bowler, 
    COUNT(*) as total_balls,
    SUM(runs) as total_runs,
    SUM(is_wicket) as dismissals,
    ROUND((CAST(SUM(runs) AS FLOAT) / NULLIF(COUNT(*), 0)) * 100, 2) as strike_rate,
    ROUND(CAST(COUNT(*) AS FLOAT) / NULLIF(SUM(is_wicket), 0), 2) as balls_per_dismissal
FROM deliveries
GROUP BY batter, bowler
HAVING total_balls >= 10;
''')

conn.commit()
conn.close()

print("View 'v_player_matchups' created successfully in cricket_data.db!")