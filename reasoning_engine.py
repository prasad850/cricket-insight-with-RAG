import sqlite3
import os
import re

from rapidfuzz import process, fuzz

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'cricket_data.db')

IPL_TEAMS = {
    'Kolkata Knight Riders','Royal Challengers Bangalore','Chennai Super Kings',
    'Mumbai Indians','Deccan Chargers','Delhi Daredevils','Rising Pune Supergiants',
    'Sunrisers Hyderabad','Gujarat Titans','Royal Challengers Bengaluru',
    'Kings XI Punjab','Rajasthan Royals','Kochi Tuskers Kerala','Pune Warriors',
    'Delhi Capitals','Lucknow Super Giants','Punjab Kings','Gujarat Lions',
    'Rising Pune Supergiant'
}

def db():
    return sqlite3.connect(DB_PATH)

# ---------------- TEAM / PLAYER ----------------
def get_all_teams(match_type):
    with db() as conn:
        teams = [t[0] for t in conn.execute("SELECT DISTINCT team_name FROM match_players WHERE match_type=?", ('T20' if match_type in ('IPL','T20') else match_type,))]
        return sorted([t for t in teams if (t in IPL_TEAMS) == (match_type == 'IPL')] if match_type in ('IPL','T20') else teams)

def get_all_seasons():
    with db() as conn:
        return [s[0] for s in conn.execute("SELECT DISTINCT season FROM match_players WHERE season IS NOT NULL ORDER BY season DESC")]

def get_players_by_team(team_name, match_type, role="any", season="All Time"):
    db_m = 'T20' if match_type == 'IPL' else match_type
    q, params = ["match_type=?"], [db_m]

    if team_name != "Any": q.append("team_name=?"); params.append(team_name)
    if season != "All Time": q.append("season=?"); params.append(season)

    with db() as conn:
        players = [p[0] for p in conn.execute(f"SELECT DISTINCT player_name FROM match_players WHERE {' AND '.join(q)}", params)]
        if role in ("batter", "bowler"):
            valid = {r[0] for r in conn.execute(f"SELECT DISTINCT {role} FROM deliveries WHERE match_type=?", (db_m,))}
            players = [p for p in players if p in valid]
        return sorted(players)

# ---------------- MATCHUP STATS ----------------
def get_stats(batter, bowler, match_type):
    with db() as conn:
        res = conn.execute("""
            SELECT COUNT(*), SUM(runs), SUM(is_wicket), SUM(runs=4), SUM(runs=6), SUM(runs=0)
            FROM deliveries WHERE batter=? AND bowler=? AND match_type=?
        """, (batter, bowler, 'T20' if match_type == 'IPL' else match_type)).fetchone()

    if res and res[0] > 0:
        b, r, w, f, s, d = res
        return {
            "balls": b, "runs": r, "wickets": w,
            "strike_rate": round(r/b*100, 2) if b else 0,
            "dot_pct": round(d/b*100, 2) if b else 0,
            "boundary_pct": round((f+s)/b*100, 2) if b else 0,
            "quality": "high" if b >= 20 else "medium" if b >= 8 else "low"
        }
    return None

# ---------------- OVERALL PLAYER ----------------
def get_player_overall(batter=None, bowler=None, match_type="T20"):
    tb = 'T20' if match_type == 'IPL' else match_type
    bat, bwl = None, None
    with db() as c:
        if batter:
            res = c.execute("SELECT COUNT(*), SUM(runs), SUM(runs=0), SUM(runs=4), SUM(runs=6) FROM deliveries WHERE batter=? AND match_type=?", (batter, tb)).fetchone()
            if res and res[0]: bat = {"balls": res[0], "runs": res[1], "strike_rate": round(res[1]/res[0]*100, 2), "dot_pct": round(res[2]/res[0]*100, 2), "boundary_pct": round((res[3]+res[4])/res[0]*100, 2)}
        if bowler:
            res = c.execute("SELECT COUNT(*), SUM(runs), SUM(is_wicket), SUM(runs=0) FROM deliveries WHERE bowler=? AND match_type=?", (bowler, tb)).fetchone()
            if res and res[0]: bwl = {"balls": res[0], "runs": res[1], "wickets": res[2], "economy": round(res[1]/(res[0]/6), 2), "dot_pct": round(res[3]/res[0]*100, 2)}
    return bat, bwl

# ---------------- FALLBACK ----------------
def get_fallback_stats(batter, bowler, match_type):
    batter_stats, bowler_stats = get_player_overall(batter, bowler, match_type)

    if not batter_stats and not bowler_stats:
        return None

    return {
        "runs": batter_stats["runs"] if batter_stats else 0,
        "balls": batter_stats["balls"] if batter_stats else 1,
        "wickets": bowler_stats["wickets"] if bowler_stats else 0,
        "strike_rate": batter_stats["strike_rate"] if batter_stats else 0,
        "dot_pct": max(
            batter_stats["dot_pct"] if batter_stats else 0,
            bowler_stats["dot_pct"] if bowler_stats else 0
        ),
        "boundary_pct": batter_stats["boundary_pct"] if batter_stats else 0,
        "quality": "fallback"
    }

# ---------------- TACTICAL ----------------
def get_tactical_report(stats):
    if not stats or stats["balls"] < 5:
        return {"title": "Limited Data", "content": "Play safe and observe.", "style": "info"}

    if stats.get("quality") == "fallback":
        return {
            "title": "📊 Derived Analysis",
            "content": "No direct matchup data. Strategy based on overall player patterns.",
            "style": "info"
        }

    sr = stats["strike_rate"]
    dots = stats["dot_pct"]
    boundary = stats["boundary_pct"]
    wkts = stats["wickets"]

    if wkts > 0 and stats["balls"]/max(1,wkts) < 10:
        return {
            "title": "🚨 High Risk Matchup",
            "content": "Bowler dominates. Play late and avoid attacking early.",
            "style": "error"
        }

    if dots > 50:
        return {
            "title": "🧱 Pressure Bowler",
            "content": "High dot ball pressure. Rotate strike.",
            "style": "info"
        }

    if boundary > 25:
        return {
            "title": "🔥 Attacking Batter",
            "content": "Good boundary rate. Attack loose balls.",
            "style": "success"
        }

    if sr < 100:
        return {
            "title": "🐌 Slow Scoring",
            "content": "Increase intent and take calculated risks.",
            "style": "info"
        }

    return {
        "title": "⚖️ Balanced Contest",
        "content": "Play according to situation.",
        "style": "info"
    }

# ---------------- PLAYER RESOLVE (FUZZY) ----------------


def resolve_player_name(name):
    conn = db(); cursor = conn.cursor()
    cursor.execute("SELECT player_name FROM match_players GROUP BY player_name ORDER BY COUNT(*) DESC")
    players = [r[0] for r in cursor.fetchall()]
    conn.close()

    if not players or not name.strip(): return None

    # 1. Direct substring match (sorted by match count)
    for p in players:
        if name.lower() in p.lower(): return p

    # 2. Fuzzy match with WRatio for better robustness
    match = process.extractOne(name, players, scorer=fuzz.WRatio)
    return match[0] if match and match[1] >= 60 else None