# ============================================================
# FIFA World Cup 2026 Analytics Platform
# 04_monte_carlo.py
# Phase 3 — Monte Carlo Tournament Simulator
# ============================================================

import pandas as pd
import numpy as np
import pickle
import os
import random
import time
import xgboost as xgb
from sqlalchemy import create_engine
from dotenv import load_dotenv
from collections import defaultdict


# ── Logging helper ───────────────────────────────────────────
def log(msg, indent=0):
    prefix = "  " * indent
    print(f"{prefix}{msg}", flush=True)

def log_step(step, msg):
    print(f"\n[{step}] {msg}", flush=True)

def elapsed(start):
    s = time.time() - start
    if s < 60:
        return f"{s:.1f}s"
    return f"{int(s//60)}m {int(s%60)}s"

SCRIPT_START = time.time()

load_dotenv()
engine = create_engine(os.getenv("CONNECTION_STRING"))

N_SIMULATIONS = 10000
random.seed(42)
np.random.seed(42)

# ============================================================
# OFFICIAL 2026 WORLD CUP GROUPS
# ============================================================

GROUPS = {
    'A': ['Mexico', 'South Africa', 'South Korea', 'Czech Republic'],
    'B': ['Canada', 'Bosnia and Herzegovina', 'Qatar', 'Switzerland'],
    'C': ['Brazil', 'Morocco', 'Haiti', 'Scotland'],
    'D': ['United States', 'Paraguay', 'Australia', 'Turkey'],
    'E': ['Germany', 'Curaçao', 'Ivory Coast', 'Ecuador'],
    'F': ['Netherlands', 'Japan', 'Sweden', 'Tunisia'],
    'G': ['Belgium', 'Egypt', 'Iran', 'New Zealand'],
    'H': ['Spain', 'Cape Verde', 'Saudi Arabia', 'Uruguay'],
    'I': ['France', 'Senegal', 'Iraq', 'Norway'],
    'J': ['Argentina', 'Algeria', 'Austria', 'Jordan'],
    'K': ['Portugal', 'DR Congo', 'Uzbekistan', 'Colombia'],
    'L': ['England', 'Croatia', 'Ghana', 'Panama'],
}

ALL_WC_TEAMS = set(t for teams in GROUPS.values() for t in teams)

# ============================================================
# LOAD MODEL
# ============================================================

log_step("1/6", "Loading XGBoost model")
t = time.time()
model = xgb.XGBClassifier()
model.load_model('ml/xgboost_model.json')
log(f"✓ Model loaded ({elapsed(t)})", indent=1)

# ============================================================
# LOAD AND CACHE ALL REFERENCE DATA UPFRONT
# Everything is calculated once before simulations start
# ============================================================

log_step("2/6", "Loading match history from Supabase")
t = time.time()
matches = pd.read_sql("""
    SELECT date, home_team, away_team, home_score, away_score, tournament
    FROM matches
    WHERE home_score IS NOT NULL
    ORDER BY date ASC
""", engine)
matches['date'] = pd.to_datetime(matches['date'])
log(f"✓ {len(matches):,} matches loaded ({elapsed(t)})", indent=1)

# ── Elo ratings ──────────────────────────────────────────────
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

log_step("3/6", "Calculating Elo ratings & building caches")
t = time.time()
log("Computing Elo ratings for all 336 teams...", indent=1)
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
log(f"✓ Elo ratings calculated for {len(elo_ratings)} teams ({elapsed(t)})", indent=1)

log("Building form cache...", indent=1)
t = time.time()

# ── Form cache — calculated once per team ───────────────────
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

form_cache = {}
for team in ALL_WC_TEAMS:
    past = results_df[results_df['team'] == team].tail(10)
    if len(past) == 0:
        form_cache[team] = {'form': 0.5, 'avg_scored': 1.5, 'avg_conceded': 1.5}
    else:
        form_cache[team] = {
            'form':         round(float(past['win'].mean()), 4),
            'avg_scored':   round(float(past['goals_for'].mean()), 4),
            'avg_conceded': round(float(past['goals_against'].mean()), 4)
        }
log(f"✓ Form cache built for {len(form_cache)} teams ({elapsed(t)})", indent=1)

# ── Squad values ─────────────────────────────────────────────
squad_vals = pd.read_sql("""
    SELECT name AS team,
           COALESCE(total_market_value, 0) / 1000000 AS squad_value_m
    FROM national_teams
""", engine)
squad_val_dict = dict(zip(squad_vals['team'], squad_vals['squad_value_m']))
log(f"✓ Squad values loaded for {len(squad_val_dict)} teams", indent=1)

# ── WC experience ────────────────────────────────────────────
wc_exp = pd.read_sql("""
    SELECT team, COUNT(DISTINCT year) AS wc_apps
    FROM (
        SELECT year, home_team AS team FROM wc_matches
        UNION ALL
        SELECT year, away_team AS team FROM wc_matches
    ) t GROUP BY team
""", engine)
wc_exp_dict = dict(zip(wc_exp['team'], wc_exp['wc_apps']))
log(f"✓ WC experience loaded for {len(wc_exp_dict)} teams", indent=1)

# ── H2H cache — most important optimisation ──────────────────
# Without cache: scans 49k rows per lookup × millions of calls = 1hr+
# With cache: dictionary lookup = microseconds
log("Building H2H cache (~30 seconds)...", indent=1)
t = time.time()
h2h_data = pd.read_sql("""
    SELECT home_team, away_team, home_score, away_score
    FROM matches WHERE home_score IS NOT NULL
""", engine)

h2h_cache = {}
teams_list = list(ALL_WC_TEAMS)
for i, team_a in enumerate(teams_list):
    for team_b in teams_list:
        if team_a == team_b:
            continue
        prior = h2h_data[
            ((h2h_data['home_team'] == team_a) & (h2h_data['away_team'] == team_b)) |
            ((h2h_data['home_team'] == team_b) & (h2h_data['away_team'] == team_a))
        ]
        if len(prior) == 0:
            h2h_cache[(team_a, team_b)] = 0.33
        else:
            wins = (
                ((prior['home_team'] == team_a) & (prior['home_score'] > prior['away_score'])) |
                ((prior['away_team'] == team_a) & (prior['away_score'] > prior['home_score']))
            ).sum()
            h2h_cache[(team_a, team_b)] = round(float(wins) / len(prior), 4)

log(f"✓ H2H cache built for {len(h2h_cache)} team pairs ({elapsed(t)})", indent=1)

# ── Pre-build feature matrix for all possible matchups ───────
# This is the biggest speedup — build all XGBoost inputs once
log_step("4/6", "Pre-computing match probabilities (batch XGBoost call)")
t = time.time()
team_pairs = [(a, b) for a in ALL_WC_TEAMS for b in ALL_WC_TEAMS if a != b]
match_prob_cache = {}
log(f"Computing probabilities for {len(team_pairs)} team pairs in one batch...", indent=1)

feature_rows = []
pair_keys = []
for team_a, team_b in team_pairs:
    elo_a  = elo_ratings.get(team_a, 1000)
    elo_b  = elo_ratings.get(team_b, 1000)
    form_a = form_cache.get(team_a, {'form': 0.5, 'avg_scored': 1.5, 'avg_conceded': 1.5})
    form_b = form_cache.get(team_b, {'form': 0.5, 'avg_scored': 1.5, 'avg_conceded': 1.5})
    feature_rows.append({
        'home_elo':          elo_a,
        'away_elo':          elo_b,
        'elo_diff':          elo_a - elo_b,
        'home_form':         form_a['form'],
        'away_form':         form_b['form'],
        'home_avg_scored':   form_a['avg_scored'],
        'away_avg_scored':   form_b['avg_scored'],
        'home_avg_conceded': form_a['avg_conceded'],
        'away_avg_conceded': form_b['avg_conceded'],
        'h2h_home_winpct':   h2h_cache.get((team_a, team_b), 0.33),
        'squad_value_diff':  squad_val_dict.get(team_a, 0) - squad_val_dict.get(team_b, 0),
        'wc_exp_diff':       wc_exp_dict.get(team_a, 0) - wc_exp_dict.get(team_b, 0),
        'tournament_weight': 3,
        'is_neutral':        1
    })
    pair_keys.append((team_a, team_b))

# Batch predict all pairs at once — single model call
features_df = pd.DataFrame(feature_rows)
all_probs   = model.predict_proba(features_df)

for idx, (team_a, team_b) in enumerate(pair_keys):
    probs = np.array(all_probs[idx], dtype=np.float64)
    probs = probs / probs.sum()  # normalise
    match_prob_cache[(team_a, team_b)] = {
        'p_away': probs[0],
        'p_draw': probs[1],
        'p_home': probs[2]
    }

log(f"✓ Match probability cache built for {len(match_prob_cache)} pairs ({elapsed(t)})", indent=1)

log_step("5/6", "Verifying team name matches")
log("Elo ratings for all 48 tournament teams:", indent=1)
for team in sorted(ALL_WC_TEAMS):
    elo  = elo_ratings.get(team, None)
    flag = " ⚠️  NAME MISMATCH" if elo is None else ""
    log(f"{team:<30} {elo_ratings.get(team, 1000):.1f}{flag}", indent=2)

mismatches = [t for t in ALL_WC_TEAMS if t not in elo_ratings]
if mismatches:
    log(f"\n⚠️  {len(mismatches)} name mismatches found — fix before trusting results", indent=1)
else:
    log("✓ All 48 team names matched successfully", indent=1)


# ============================================================
# MATCH PREDICTION — NOW USES CACHE (microseconds per call)
# ============================================================

def predict_match(team_a, team_b, knockout=False):
    probs  = match_prob_cache[(team_a, team_b)]
    p_away = probs['p_away']
    p_draw = probs['p_draw']
    p_home = probs['p_home']

    if knockout:
        decisive   = p_home + p_away
        p_home_adj = (p_home + p_draw * (p_home / decisive))
        p_away_adj = (p_away + p_draw * (p_away / decisive))
        total_adj  = p_home_adj + p_away_adj
        p_home_adj = p_home_adj / total_adj
        p_away_adj = p_away_adj / total_adj
        outcome = np.random.choice(['home','away'], p=[p_home_adj, p_away_adj])
        return team_a if outcome == 'home' else team_b
    else:
        outcome = np.random.choice(['home','draw','away'], p=[p_home, p_draw, p_away])
        if outcome == 'home':
            return (3, 0, 2, 0)
        elif outcome == 'draw':
            return (1, 1, 1, 1)
        else:
            return (0, 3, 0, 2)


# ============================================================
# TIEBREAKER FUNCTIONS — 2026 FIFA RULES
# ============================================================

def get_h2h_group_tiebreaker(tied_teams, match_results):
    h2h = {t: {'pts': 0, 'gd': 0, 'gf': 0} for t in tied_teams}
    for m in match_results:
        if m['home'] in tied_teams and m['away'] in tied_teams:
            h2h[m['home']]['pts'] += m['pts_home']
            h2h[m['home']]['gf']  += m['gf_home']
            h2h[m['home']]['gd']  += m['gf_home'] - m['gf_away']
            h2h[m['away']]['pts'] += m['pts_away']
            h2h[m['away']]['gf']  += m['gf_away']
            h2h[m['away']]['gd']  += m['gf_away'] - m['gf_home']
    return h2h

def sort_group(standings, match_results):
    teams_list = list(standings.keys())
    teams_list.sort(key=lambda t: standings[t]['pts'], reverse=True)
    final_order = []
    i = 0
    while i < len(teams_list):
        same_pts = [teams_list[i]]
        j = i + 1
        while j < len(teams_list) and \
              standings[teams_list[j]]['pts'] == standings[teams_list[i]]['pts']:
            same_pts.append(teams_list[j])
            j += 1
        if len(same_pts) == 1:
            final_order.append(same_pts[0])
        else:
            h2h = get_h2h_group_tiebreaker(set(same_pts), match_results)
            same_pts.sort(key=lambda t: (
                h2h[t]['pts'],
                h2h[t]['gd'],
                h2h[t]['gf'],
                standings[t]['gf'] - standings[t]['ga'],
                standings[t]['gf'],
                elo_ratings.get(t, 1000)
            ), reverse=True)
            final_order.extend(same_pts)
        i = j
    return final_order


# ============================================================
# SIMULATE ONE FULL TOURNAMENT
# ============================================================

def simulate_tournament():
    stage_results = {
        'group_exit': set(), 'r32': set(), 'r16': set(),
        'qf': set(), 'sf': set(), 'final': set(), 'winner': None
    }

    all_third_place  = []
    group_qualifiers = []

    for group_name, teams in GROUPS.items():
        standings     = {t: {'pts': 0, 'gf': 0, 'ga': 0} for t in teams}
        match_results = []

        for i in range(len(teams)):
            for j in range(i + 1, len(teams)):
                pts_home, pts_away, gf_home, gf_away = predict_match(
                    teams[i], teams[j], knockout=False
                )
                standings[teams[i]]['pts'] += pts_home
                standings[teams[i]]['gf']  += gf_home
                standings[teams[i]]['ga']  += gf_away
                standings[teams[j]]['pts'] += pts_away
                standings[teams[j]]['gf']  += gf_away
                standings[teams[j]]['ga']  += gf_home
                match_results.append({
                    'home': teams[i], 'away': teams[j],
                    'pts_home': pts_home, 'pts_away': pts_away,
                    'gf_home': gf_home,  'gf_away': gf_away
                })

        sorted_teams = sort_group(standings, match_results)
        group_qualifiers.append(sorted_teams[0])
        group_qualifiers.append(sorted_teams[1])

        third = sorted_teams[2]
        all_third_place.append({
            'team': third,
            'pts':  standings[third]['pts'],
            'gd':   standings[third]['gf'] - standings[third]['ga'],
            'gf':   standings[third]['gf']
        })
        stage_results['group_exit'].add(sorted_teams[3])

    third_df     = pd.DataFrame(all_third_place).sort_values(
        ['pts','gd','gf'], ascending=False
    )
    best_thirds  = third_df.head(8)['team'].tolist()
    worst_thirds = third_df.tail(4)['team'].tolist()
    for t in worst_thirds:
        stage_results['group_exit'].add(t)

    current_round = group_qualifiers + best_thirds

    for round_name in ['r32', 'r16', 'qf', 'sf']:
        next_round = []
        random.shuffle(current_round)
        for i in range(0, len(current_round), 2):
            if i + 1 >= len(current_round):
                next_round.append(current_round[i])
                continue
            team_a = current_round[i]
            team_b = current_round[i + 1]
            winner = predict_match(team_a, team_b, knockout=True)
            loser  = team_b if winner == team_a else team_a
            stage_results[round_name].add(loser)
            next_round.append(winner)
        current_round = next_round

    if len(current_round) >= 2:
        finalist_a = current_round[0]
        finalist_b = current_round[1]
        stage_results['final'].add(finalist_a)
        stage_results['final'].add(finalist_b)
        winner = predict_match(finalist_a, finalist_b, knockout=True)
        stage_results['winner'] = winner

    return stage_results


# ============================================================
# RUN 10,000 SIMULATIONS
# ============================================================

log_step("6/6", f"Running {N_SIMULATIONS:,} Monte Carlo simulations")
t = time.time()
log("Each simulation = full 2026 WC (group stage + 5 knockout rounds)", indent=1)
log("Progress updates every 500 simulations\n", indent=1)

all_teams    = [t for teams in GROUPS.values() for t in teams]
win_counts   = defaultdict(int)
final_counts = defaultdict(int)
sf_counts    = defaultdict(int)
qf_counts    = defaultdict(int)
r16_counts   = defaultdict(int)
r32_counts   = defaultdict(int)

for sim in range(N_SIMULATIONS):
    if (sim + 1) % 500 == 0:
        pct       = (sim + 1) / N_SIMULATIONS * 100
        eta_secs  = (time.time() - t) / (sim + 1) * (N_SIMULATIONS - sim - 1)
        eta_str   = elapsed(time.time() - eta_secs) if eta_secs > 0 else "—"
        # Current top 3 leaders
        leaders   = sorted(win_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        leader_str = " | ".join(f"{tm}: {cnt/(sim+1)*100:.1f}%" for tm, cnt in leaders)
        log(f"[{pct:5.1f}%] {sim+1:,}/{N_SIMULATIONS:,} sims | "
            f"ETA: ~{elapsed(time.time() - eta_secs)} | "
            f"Leaders → {leader_str}", indent=1)
    result = simulate_tournament()
    if result['winner']:
        win_counts[result['winner']] += 1
    for team in result['final']:  final_counts[team] += 1
    for team in result['sf']:     sf_counts[team]    += 1
    for team in result['qf']:     qf_counts[team]    += 1
    for team in result['r16']:    r16_counts[team]   += 1
    for team in result['r32']:    r32_counts[team]   += 1

log(f"\n✓ {N_SIMULATIONS:,} simulations complete in {elapsed(t)}", indent=1)


# ============================================================
# COMPILE AND EXPORT RESULTS
# ============================================================

log("\nCompiling results...")

simulation_results = []
for team in all_teams:
    simulation_results.append({
        'team':            team,
        'group':           next(g for g, teams in GROUPS.items() if team in teams),
        'elo':             round(elo_ratings.get(team, 1000), 1),
        'squad_value_m':   round(squad_val_dict.get(team, 0), 1),
        'win_prob':        round(win_counts[team]   / N_SIMULATIONS * 100, 2),
        'final_prob':      round(final_counts[team] / N_SIMULATIONS * 100, 2),
        'sf_prob':         round(sf_counts[team]    / N_SIMULATIONS * 100, 2),
        'qf_prob':         round(qf_counts[team]    / N_SIMULATIONS * 100, 2),
        'r16_prob':        round(r16_counts[team]   / N_SIMULATIONS * 100, 2),
        'group_exit_prob': round(r32_counts[team]   / N_SIMULATIONS * 100, 2),
    })

results_df = pd.DataFrame(simulation_results).sort_values('win_prob', ascending=False)

print("\n" + "="*65)
print("  🏆 2026 WORLD CUP WINNER PREDICTIONS")
print("="*65)
print(f"  {'Team':<22} {'Win%':>6} {'Final%':>8} {'SF%':>6} {'QF%':>6}")
print(f"  {'-'*55}")
for _, row in results_df.head(15).iterrows():
    bar = '█' * int(row['win_prob'] / 2)
    print(f"  {row['team']:<22} {row['win_prob']:>5.1f}%  "
          f"{row['final_prob']:>6.1f}%  "
          f"{row['sf_prob']:>5.1f}%  "
          f"{row['qf_prob']:>5.1f}%  "
          f"{bar}")
print("="*65)

os.makedirs('ml', exist_ok=True)
results_df.to_csv('ml/simulation_results.csv', index=False)
log(f"\n  ✓ Results exported to ml/simulation_results.csv")
log(f"\n✅ Phase 3 complete — total runtime: {elapsed(SCRIPT_START)}")