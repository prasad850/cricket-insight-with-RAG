import json
import sqlite3
import os

# Connect to database
conn = sqlite3.connect('cricket_data.db')
cursor = conn.cursor()

# Define Tables
cursor.execute('''CREATE TABLE IF NOT EXISTS deliveries 
                  (match_id, inning, over, ball, batter, bowler, runs, is_wicket)''')

def process_file(filepath):
    with open(filepath, 'r') as f:
        data = json.load(f)
        
        for inning_idx, inning in enumerate(data['innings']):
            for over_data in inning['overs']:
                # ADDED enumerate here to get the ball index (delivery_idx)
                for delivery_idx, delivery in enumerate(over_data['deliveries']):
                    
                    # 1. Extract data
                    batter = delivery['batter']
                    bowler = delivery['bowler']
                    runs = delivery['runs']['total']
                    is_wicket = 1 if 'wickets' in delivery else 0
                    
                    # 2. Insert into database
                    # delivery_idx replaces the 'delivery' dict object
                    cursor.execute("INSERT INTO deliveries VALUES (?,?,?,?,?,?,?,?)", 
                                   (None, inning_idx, over_data['over'], delivery_idx, batter, bowler, runs, is_wicket))

# Iterate through all files
folder_path = './data' 
for filename in os.listdir(folder_path):
    if filename.endswith(".json"):
        process_file(os.path.join(folder_path, filename))

conn.commit()