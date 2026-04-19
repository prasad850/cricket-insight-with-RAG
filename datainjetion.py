import json
import sqlite3
import os

# Configuration
DB_NAME = 'cricket_data.db'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, DB_NAME)
DATA_DIR = os.path.join(BASE_DIR, 'data')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Matches Table: Stores metadata
    cursor.execute('''CREATE TABLE IF NOT EXISTS matches 
                      (match_id TEXT PRIMARY KEY, match_type TEXT, season TEXT, venue TEXT)''')
    
    # 2. Deliveries Table: Stores ball-by-ball data (with match_type for format-specific analysis)
    cursor.execute('''CREATE TABLE IF NOT EXISTS deliveries 
                      (match_id TEXT, match_type TEXT, batter TEXT, bowler TEXT, runs INTEGER, is_wicket INTEGER)''')
    
    # 3. Match Players Table: Stores squads (with season for team filtering)
    cursor.execute('''CREATE TABLE IF NOT EXISTS match_players 
                      (match_id TEXT, team_name TEXT, player_name TEXT, season TEXT)''')
                      
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully.")

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    info = data['info']
    match_id = os.path.basename(filepath)
    match_type = info.get('match_type', 'T20')
    season = str(info.get('season', '2026'))
    venue = info.get('venue', 'Unknown')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Ingest Match Info
    cursor.execute("INSERT OR IGNORE INTO matches VALUES (?, ?, ?, ?)", 
                   (match_id, match_type, season, venue))

    # Ingest Squads
    for team_name, players in info.get('players', {}).items():
        for player in players:
            cursor.execute("INSERT INTO match_players VALUES (?, ?, ?, ?)", 
                           (match_id, team_name, player, season))
        
    # Ingest Deliveries
    for inning in data.get('innings', []):
        for over_data in inning.get('overs', []):
            for delivery in over_data.get('deliveries', []):
                batter = delivery['batter']
                bowler = delivery['bowler']
                runs = delivery['runs']['total']
                is_wicket = 1 if 'wickets' in delivery else 0
                
                cursor.execute("INSERT INTO deliveries VALUES (?, ?, ?, ?, ?, ?)",
                               (match_id, match_type, batter, bowler, runs, is_wicket))
    
    conn.commit()
    conn.close()
    print(f"✅ Ingested: {match_id} ({match_type})")

if __name__ == "__main__":
    init_db()
    if os.path.exists(DATA_DIR):
        for filename in os.listdir(DATA_DIR):
            if filename.endswith(".json"):
                process_file(os.path.join(DATA_DIR, filename))
    else:
        print(f"❌ Error: 'data' folder not found in {BASE_DIR}")