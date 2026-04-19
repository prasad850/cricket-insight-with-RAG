import json
import sqlite3
import os

DB_NAME = 'cricket_data.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Deliveries (Global Stats)
    cursor.execute('''CREATE TABLE IF NOT EXISTS deliveries 
                      (match_id TEXT, batter TEXT, bowler TEXT, runs INTEGER, is_wicket INTEGER)''')
    # Match Players (Selection Logic - now includes SEASON)
    cursor.execute('''CREATE TABLE IF NOT EXISTS match_players 
                      (match_id TEXT, team_name TEXT, player_name TEXT, season TEXT)''')
    conn.commit()
    conn.close()

def process_file(filepath):
    with open(filepath, 'r') as f:
        data = json.load(f)
        match_id = os.path.basename(filepath)
        season = data['info'].get('season', '2026')
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Ingest Players
        for team_name, players in data['info']['players'].items():
            for player in players:
                cursor.execute("INSERT INTO match_players VALUES (?, ?, ?, ?)", 
                               (match_id, team_name, player, season))
        
        # Ingest Deliveries
        for inning in data['innings']:
            for over_data in inning['overs']:
                for delivery in over_data['deliveries']:
                    is_wicket = 1 if 'wickets' in delivery else 0
                    cursor.execute("INSERT INTO deliveries VALUES (?, ?, ?, ?, ?)",
                                   (match_id, delivery['batter'], delivery['bowler'], 
                                    delivery['runs']['total'], is_wicket))
        conn.commit()
        conn.close()

init_db()
for filename in os.listdir('./data'):
    if filename.endswith(".json"):
        process_file(os.path.join('./data', filename))