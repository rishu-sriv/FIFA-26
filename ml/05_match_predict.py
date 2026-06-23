# ============================================================
# FIFA World Cup 2026 Analytics Platform
# 05_predict_match.py
# Match Outcome Predictor — Interactive CLI
# ============================================================
# Usage:
#   python ml/05_predict_match.py
#   Then enter any two teams when prompted
# ============================================================

import pandas as pd
import numpy as np
import xgboost as xgb
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("CONNECTION_STRING"))

# ============================================================
# LOAD MODEL AND REFERENCE DATA
# ============================================================

print("Loading model and data...")

model = xgb.XGBClassifier()
model.load_model('ml/xgboost_model.json')

# Load matches for Elo calculation
matches = pd.read_sql("""
    SELECT date, home_team, away_team, home_score, away_score, tournament
    FROM matches
    WHERE home_score IS NOT NULL
    ORDER BY date ASC
""", engine)
matches['date'] = pd.to_datetime(matches['date'])

# Elo
def get_k_factor(tournament):
    t = tournament.lower()
    if 'world cup' in t and 'qualifier' not in t:
        return 60
    elif any(x in t for x in ['euro','copa america','africa cup','asian cup','gold cup']):
        return 45
    elif 'qualifier' in t or 'qualification' in t:
        return 40
    elif 'friendly' in t:
        return 20
    else:
        return 35

def expected_score(elo_a, elo_b):
    return 1 / (1 + 10 ** ((elo_b - elo_a) / 400))

elo_ratings = {}
for _, row in matches.iterrows():
    home, away = row['home_team'], row['away_team']
    elo_home = elo_ratings.get(home, 1000)
    elo_away = elo_ratings.get(away, 1000)
    exp_home = expected_score(elo_home, elo_away)
    exp_away = expected_score(elo_away, elo_home)
    if row['home_score'] > row['away_score']:
        act_home, act_away = 1.0, 0.0
    elif row['home_score'] == row['away_score']:
        act_home, act_away = 0.5, 0.5
    else:
        act_home, act_away = 0.0, 1.0
    k = get_k_factor(row['tournament'])
    elo_ratings[home] = elo_home + k * (act_home - exp_home)
    elo_ratings[away] = elo_away + k * (act_away - exp_away)

# Form
results_list = []
for _, row in matches.iterrows():
    results_list.append({
        'date': row['date'], 'team': row['home_team'],
        'goals_for': row['home_score'], 'goals_against': row['away_score'],
        'win': 1 if row['home_score'] > row['away_score'] else 0
    })
    results_list.append({
        'date': row['date'], 'team': row['away_team'],
        'goals_for': row['away_score'], 'goals_against': row['home_score'],
        'win': 1 if row['away_score'] > row['home_score'] else 0
    })
results_df = pd.DataFrame(results_list).sort_values('date').reset_index(drop=True)

def get_form(team, n=10):
    past = results_df[results_df['team'] == team].tail(n)
    if len(past) == 0:
        return {'form': 0.5, 'avg_scored': 1.5, 'avg_conceded': 1.5}
    return {
        'form':         round(float(past['win'].mean()), 4),
        'avg_scored':   round(float(past['goals_for'].mean()), 4),
        'avg_conceded': round(float(past['goals_against'].mean()), 4)
    }

# Squad values
squad_vals = pd.read_sql("""
    SELECT name AS team,
           COALESCE(total_market_value, 0) / 1000000 AS squad_value_m
    FROM national_teams
""", engine)
squad_val_dict = dict(zip(squad_vals['team'], squad_vals['squad_value_m']))

# WC experience
wc_exp = pd.read_sql("""
    SELECT team, COUNT(DISTINCT year) AS wc_apps
    FROM (
        SELECT year, home_team AS team FROM wc_matches
        UNION ALL
        SELECT year, away_team AS team FROM wc_matches
    ) t GROUP BY team
""", engine)
wc_exp_dict = dict(zip(wc_exp['team'], wc_exp['wc_apps']))

# H2H
h2h_data = pd.read_sql("""
    SELECT home_team, away_team, home_score, away_score
    FROM matches WHERE home_score IS NOT NULL
""", engine)

def get_h2h_winpct(team_a, team_b):
    prior = h2h_data[
        ((h2h_data['home_team'] == team_a) & (h2h_data['away_team'] == team_b)) |
        ((h2h_data['home_team'] == team_b) & (h2h_data['away_team'] == team_a))
    ]
    if len(prior) == 0:
        return 0.33
    wins = (
        ((prior['home_team'] == team_a) & (prior['home_score'] > prior['away_score'])) |
        ((prior['away_team'] == team_a) & (prior['away_score'] > prior['home_score']))
    ).sum()
    return round(float(wins) / len(prior), 4)

# All known teams
all_teams = sorted(elo_ratings.keys())
print(f"✓ Ready. {len(all_teams)} teams available.\n")


# ============================================================
# PREDICTION FUNCTION
# ============================================================

def predict_match(team_a, team_b):
    elo_a  = elo_ratings.get(team_a, 1000)
    elo_b  = elo_ratings.get(team_b, 1000)
    form_a = get_form(team_a)
    form_b = get_form(team_b)
    h2h    = get_h2h_winpct(team_a, team_b)
    sv_a   = squad_val_dict.get(team_a, 0)
    sv_b   = squad_val_dict.get(team_b, 0)
    we_a   = wc_exp_dict.get(team_a, 0)
    we_b   = wc_exp_dict.get(team_b, 0)

    features = pd.DataFrame([{
        'home_elo':          elo_a,
        'away_elo':          elo_b,
        'elo_diff':          elo_a - elo_b,
        'home_form':         form_a['form'],
        'away_form':         form_b['form'],
        'home_avg_scored':   form_a['avg_scored'],
        'away_avg_scored':   form_b['avg_scored'],
        'home_avg_conceded': form_a['avg_conceded'],
        'away_avg_conceded': form_b['avg_conceded'],
        'h2h_home_winpct':   h2h,
        'squad_value_diff':  sv_a - sv_b,
        'wc_exp_diff':       we_a - we_b,
        'tournament_weight': 3,
        'is_neutral':        1
    }])

    probs = model.predict_proba(features)[0]
    probs = np.array(probs, dtype=np.float64)
    probs = probs / probs.sum()
    p_away, p_draw, p_home = probs[0], probs[1], probs[2]

    return {
        'team_a':      team_a,
        'team_b':      team_b,
        'p_home':      round(p_home * 100, 1),
        'p_draw':      round(p_draw * 100, 1),
        'p_away':      round(p_away * 100, 1),
        'elo_a':       round(elo_a, 1),
        'elo_b':       round(elo_b, 1),
        'form_a':      round(form_a['form'] * 100, 1),
        'form_b':      round(form_b['form'] * 100, 1),
        'h2h':         round(h2h * 100, 1),
        'sv_a':        round(sv_a, 1),
        'sv_b':        round(sv_b, 1),
    }

def display_prediction(r):
    winner = r['team_a'] if r['p_home'] > r['p_away'] else r['team_b']
    if abs(r['p_home'] - r['p_away']) < 5:
        winner = "Too close to call"

    w = 60
    print("\n" + "="*w)
    print(f"  ⚽  {r['team_a']}  vs  {r['team_b']}")
    print("="*w)

    # Win probabilities
    print(f"\n  {'OUTCOME':<20} {'PROBABILITY':>12}  {'BAR'}")
    print(f"  {'-'*55}")

    bar_home = '█' * int(r['p_home'] / 2)
    bar_draw = '█' * int(r['p_draw'] / 2)
    bar_away = '█' * int(r['p_away'] / 2)

    print(f"  {r['team_a']:<20} {r['p_home']:>10.1f}%  {bar_home}")
    print(f"  {'Draw':<20} {r['p_draw']:>10.1f}%  {bar_draw}")
    print(f"  {r['team_b']:<20} {r['p_away']:>10.1f}%  {bar_away}")

    print(f"\n  🏆 Predicted winner: {winner}")

    # Feature breakdown
    print(f"\n  {'FEATURE':<25} {r['team_a']:>15} {r['team_b']:>15}")
    print(f"  {'-'*57}")
    print(f"  {'Elo Rating':<25} {r['elo_a']:>15.1f} {r['elo_b']:>15.1f}")
    print(f"  {'Recent Form (win%)':<25} {r['form_a']:>14.1f}% {r['form_b']:>14.1f}%")
    print(f"  {'Squad Value (€M)':<25} {r['sv_a']:>15.1f} {r['sv_b']:>15.1f}")
    print(f"  {'H2H Win% ({})'.format(r['team_a']):<25} {r['h2h']:>14.1f}%")
    print("="*w + "\n")

def find_team(query, all_teams):
    """Fuzzy team name matching."""
    query = query.strip().lower()
    # Exact match first
    for t in all_teams:
        if t.lower() == query:
            return t
    # Partial match
    matches_found = [t for t in all_teams if query in t.lower()]
    if len(matches_found) == 1:
        return matches_found[0]
    elif len(matches_found) > 1:
        print(f"  Multiple matches found: {matches_found}")
        print(f"  Please be more specific.")
        return None
    print(f"  Team '{query}' not found.")
    print(f"  Try one of: {[t for t in all_teams if query[:3].lower() in t.lower()][:5]}")
    return None


# ============================================================
# INTERACTIVE CLI
# ============================================================

print("=" * 60)
print("  ⚽  FIFA 2026 Match Predictor")
print("  Type two team names to get a prediction")
print("  Type 'quit' to exit")
print("=" * 60)

while True:
    print()
    team_a_input = input("  Enter Team 1: ").strip()
    if team_a_input.lower() in ['quit', 'exit', 'q']:
        print("\n  Goodbye!\n")
        break

    team_b_input = input("  Enter Team 2: ").strip()
    if team_b_input.lower() in ['quit', 'exit', 'q']:
        print("\n  Goodbye!\n")
        break

    team_a = find_team(team_a_input, all_teams)
    team_b = find_team(team_b_input, all_teams)

    if team_a and team_b:
        if team_a == team_b:
            print("  Please enter two different teams.")
            continue
        result = predict_match(team_a, team_b)
        display_prediction(result)

    again = input("  Predict another match? (y/n): ").strip().lower()
    if again != 'y':
        print("\n  Goodbye!\n")
        break