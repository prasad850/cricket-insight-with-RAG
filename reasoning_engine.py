import sqlite3
import os

# Ensure the DB path is correct
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'cricket_data.db')

def get_all_teams():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT team_name FROM match_players ORDER BY team_name ASC")
    teams = [row[0] for row in cursor.fetchall()]
    conn.close()
    return teams

def get_players_by_team(team_name, season="2026"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if team_name == "Any" or team_name is None:
        cursor.execute("SELECT DISTINCT player_name FROM match_players WHERE season = ? ORDER BY player_name ASC", (season,))
    else:
        cursor.execute("SELECT DISTINCT player_name FROM match_players WHERE team_name = ? AND season = ? ORDER BY player_name ASC", (team_name, season))
    
    players = [row[0] for row in cursor.fetchall()]
    conn.close()
    return players

def get_stats(batter, bowler, match_type=None):
    """Retrieves stats. Returns None if no data exists."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = "SELECT COUNT(*), SUM(runs), SUM(is_wicket) FROM deliveries WHERE batter = ? AND bowler = ?"
    params = [batter, bowler]
    
    if match_type:
        query += " AND match_type = ?"
        params.append(match_type)
        
    cursor.execute(query, params)
    res = cursor.fetchone()
    conn.close()
    
    if res and res[0] > 0:
        balls, runs, wickets = res[0], (res[1] or 0), (res[2] or 0)
        strike_rate = (runs / balls) * 100 if balls > 0 else 0
        return {
            "balls": balls, 
            "runs": runs, 
            "wickets": wickets, 
            "strike_rate": round(strike_rate, 2)
        }
    return None

def get_tactical_report(global_stats):
    """
    Returns a structured dictionary with insights. 
    Perfect for Chatbot (text) AND Home Dashboard (data objects).
    """
    if not global_stats or global_stats['balls'] < 10:
        return {
            "status": "Insufficient Data",
            "message": "Not enough historical data to provide a tactical report.",
            "type": "neutral"
        }
    
    balls_per_dismissal = global_stats['balls'] / max(1, global_stats['wickets'])
    
    # Tactical Logic
    if balls_per_dismissal < 15:
        return {
            "status": "Weakness Detected",
            "message": "High dismissal risk. The bowler has dominated this matchup historically.",
            "type": "danger"
        }
    elif global_stats['strike_rate'] > 130:
        return {
            "status": "Strong Advantage",
            "message": "The batter scores aggressively. High strike rate observed against this bowler.",
            "type": "success"
        }
    else:
        return {
            "status": "Balanced",
            "message": "The matchup is neutral. Play with standard discipline.",
            "type": "neutral"
        }

# Maintain backward compatibility for your Home Dashboard
def determine_strategy(global_stats):
    report = get_tactical_report(global_stats)
    return f"{report['status']}: {report['message']}"