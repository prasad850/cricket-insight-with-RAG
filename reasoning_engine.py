import sqlite3

def get_matchup_stats(batter_name, bowler_name):
    conn = sqlite3.connect('cricket_data.db')
    cursor = conn.cursor()
    
    # Query your analytics view
    query = """
    SELECT total_balls, total_runs, strike_rate, balls_per_dismissal 
    FROM v_player_matchups 
    WHERE batter = ? AND bowler = ?
    """
    cursor.execute(query, (batter_name, bowler_name))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return f"Stats for {batter_name} vs {bowler_name}: {result[1]} runs in {result[0]} balls, Strike Rate: {result[2]}, Balls per dismissal: {result[3]}"
    else:
        return "No matchup data found for these players."