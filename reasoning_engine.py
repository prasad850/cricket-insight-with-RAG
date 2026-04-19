import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'cricket_data.db')

IPL_TEAMS = {'Kolkata Knight Riders', 'Royal Challengers Bangalore', 'Chennai Super Kings', 'Mumbai Indians', 'Deccan Chargers', 'Delhi Daredevils', 'Rising Pune Supergiants', 'Sunrisers Hyderabad', 'Gujarat Titans', 'Royal Challengers Bengaluru', 'Kings XI Punjab', 'Rajasthan Royals', 'Kochi Tuskers Kerala', 'Pune Warriors', 'Delhi Capitals', 'Lucknow Super Giants', 'Punjab Kings', 'Gujarat Lions', 'Rising Pune Supergiant'}


def get_all_teams(match_type):
    """Fetches teams specific to the selected format (IPL, T20, or ODI)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if match_type == 'IPL':
        cursor.execute("SELECT DISTINCT team_name FROM match_players WHERE match_type = 'T20' ORDER BY team_name ASC")
        teams = [row[0] for row in cursor.fetchall() if row[0] in IPL_TEAMS]
    elif match_type == 'T20':
        cursor.execute("SELECT DISTINCT team_name FROM match_players WHERE match_type = 'T20' ORDER BY team_name ASC")
        teams = [row[0] for row in cursor.fetchall() if row[0] not in IPL_TEAMS]
    else:
        cursor.execute("SELECT DISTINCT team_name FROM match_players WHERE match_type = ? ORDER BY team_name ASC", (match_type,))
        teams = [row[0] for row in cursor.fetchall()]
        
    conn.close()
    return teams

def get_all_seasons():
    """Fetches all unique seasons available."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT season FROM match_players ORDER BY season DESC")
    seasons = [row[0] for row in cursor.fetchall() if row[0]]
    conn.close()
    return seasons

def get_players_by_team(team_name, match_type, role="any", season="All Time"):
    """Fetches players specific to a team, format, role (batter, bowler, any), and optionally season."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    db_match_type = 'T20' if match_type == 'IPL' else match_type
    
    query = "SELECT DISTINCT player_name FROM match_players WHERE match_type = ?"
    params = [db_match_type]
    
    if team_name != "Any":
        query += " AND team_name = ?"
        params.append(team_name)
        
    if season != "All Time":
        query += " AND season = ?"
        params.append(season)
        
    cursor.execute(query, tuple(params))
    players = [row[0] for row in cursor.fetchall()]
    
    if role == "batter":
        query_batters = "SELECT DISTINCT batter FROM deliveries WHERE match_type = ?"
        cursor.execute(query_batters, (db_match_type,))
        batters_set = {row[0] for row in cursor.fetchall()}
        players = [p for p in players if p in batters_set]
    elif role == "bowler":
        query_bowlers = "SELECT DISTINCT bowler FROM deliveries WHERE match_type = ?"
        cursor.execute(query_bowlers, (db_match_type,))
        bowlers_set = {row[0] for row in cursor.fetchall()}
        players = [p for p in players if p in bowlers_set]
        
    conn.close()
    return sorted(players)

def get_stats(batter, bowler, match_type):
    """Retrieves stats filtered by specific format."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    db_match_type = 'T20' if match_type == 'IPL' else match_type
    
    query = "SELECT COUNT(*), SUM(runs), SUM(is_wicket) FROM deliveries WHERE batter = ? AND bowler = ? AND match_type = ?"
    cursor.execute(query, (batter, bowler, db_match_type))
    res = cursor.fetchone()
    conn.close()
    
    if res and res[0] > 0:
        balls, runs, wickets = res[0], (res[1] or 0), (res[2] or 0)
        return {
            "balls": balls, 
            "runs": runs, 
            "wickets": wickets, 
            "strike_rate": round((runs / balls) * 100, 2) if balls > 0 else 0
        }
    return None

def get_tactical_report(stats):
    """Generates strategy based on performance stats."""
    if not stats or stats["balls"] < 5:
        return {"title": "Limited Data", "content": "Too few deliveries to form a strong strategy. Play conventional cricket.", "style": "info"}
    
    balls_per_dismissal = stats["balls"] / max(1, stats["wickets"])
    
    if balls_per_dismissal < 8 and stats["wickets"] > 0:
        return {"title": "⚠️ Weakness Detected", "content": f"High dismissal risk against this bowler (out every {int(balls_per_dismissal)} balls). Prioritize strike rotation and avoid big shots early.", "style": "error"}
    elif stats["strike_rate"] > 130:
        return {"title": "🔥 Strength Detected", "content": f"Dominant scoring rate ({stats['strike_rate']}). Capitalize on loose deliveries and maintain aggressive intent.", "style": "success"}
    elif stats["strike_rate"] < 100:
        return {"title": "🐌 Defensive Matchup", "content": f"Focusing on survival (SR: {stats['strike_rate']}). Consider taking more calculated risks if the run rate demands it.", "style": "info"}
    else:
        return {"title": "⚖️ Neutral Matchup", "content": "Performance is standard. Play on merit and look for the bad ball.", "style": "info"}