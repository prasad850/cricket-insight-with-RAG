import sqlite3

DB_NAME = 'cricket_data.db'

def get_all_teams():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT team_name FROM match_players ORDER BY team_name ASC")
    teams = [row[0] for row in cursor.fetchall()]
    conn.close()
    return teams

def get_players_by_team(team_name, season="2026"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    query = "SELECT DISTINCT player_name FROM match_players WHERE team_name = ? AND season = ? ORDER BY player_name ASC"
    cursor.execute(query, (team_name, season))
    players = [row[0] for row in cursor.fetchall()]
    conn.close()
    return players

def get_matchup_stats(batter_name, bowler_name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Global stats (All seasons)
    query = """
    SELECT COUNT(*), SUM(runs), SUM(is_wicket) 
    FROM deliveries 
    WHERE batter = ? AND bowler = ?
    """
    cursor.execute(query, (batter_name, bowler_name))
    res = cursor.fetchone()
    conn.close()
    
    if res and res[0] > 0: # Check if data exists
        return {"balls": res[0], "runs": res[1], "dismissals": res[2] or 0}
    return None