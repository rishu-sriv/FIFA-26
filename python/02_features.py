# ============================================================
# FIFA World Cup 2026 Analytics Platform
# 02_features.py
# Phase 2 Part B — Feature Engineering
# ============================================================
# What this script does:
#   Step 6: Calculate Elo ratings for every team (1872-2026)
#   Step 7: Calculate rolling form (last 10 matches)
#   Step 8: Calculate head-to-head record per match
#   Step 9: Assemble match_features table and write to Supabase
# ============================================================

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text

# ── CONFIG ───────────────────────────────────────────────────
from dotenv import load_dotenv
import os

load_dotenv()
CONNECTION_STRING = os.getenv("CONNECTION_STRING")
engine = create_engine(CONNECTION_STRING)

# ============================================================
# STEP 6 — ELO RATING CALCULATION
# ============================================================
# Elo ratings update dynamically after every match.
# A win against a strong team gains more points than a win
# against a weak team. K-factor weights match importance.
#
# Formula:
#   new_elo = old_elo + K * (actual - expected)
#   expected = 1 / (1 + 10^((opponent_elo - your_elo) / 400))
#   actual = 1 (win), 0.5 (draw), 0 (loss)
#
# K-factors by tournament type:
#   World Cup match          → 60 (highest stakes)
#   Continental final        → 50
#   Continental group stage  → 45
#   WC Qualifier             → 40
#   Other competitive        → 35
#   Friendly                 → 20
# ============================================================

print("Step 6: Calculating Elo ratings...")

# Load all matches ordered by date
df = pd.read_sql("""
    SELECT date, home_team, away_team, home_score, away_score,
           tournament, neutral
    FROM matches
    WHERE home_score IS NOT NULL
    ORDER BY date ASC
""", engine)

df['date'] = pd.to_datetime(df['date'])

def get_k_factor(tournament):
    t = tournament.lower()
    if 'world cup' in t and 'qualifier' not in t:
        return 60
    elif any(x in t for x in ['euro', 'copa america', 'africa cup', 'asian cup', 'gold cup']):
        if 'qualifier' in t:
            return 40
        return 45
    elif 'qualifier' in t or 'qualification' in t:
        return 40
    elif 'friendly' in t:
        return 20
    else:
        return 35

def expected_score(elo_a, elo_b):
    return 1 / (1 + 10 ** ((elo_b - elo_a) / 400))

# Starting Elo for all teams
elo_ratings = {}
elo_history = []  # stores elo BEFORE each match (for feature use)

for _, row in df.iterrows():
    home = row['home_team']
    away = row['away_team']

    # Default starting Elo is 1000
    elo_home = elo_ratings.get(home, 1000)
    elo_away = elo_ratings.get(away, 1000)

    # Store pre-match Elo (this is what we use as features)
    elo_history.append({
        'date':        row['date'],
        'home_team':   home,
        'away_team':   away,
        'home_elo':    elo_home,
        'away_elo':    elo_away,
        'elo_diff':    elo_home - elo_away
    })

    # Calculate expected scores
    exp_home = expected_score(elo_home, elo_away)
    exp_away = expected_score(elo_away, elo_home)

    # Actual scores
    if row['home_score'] > row['away_score']:
        act_home, act_away = 1.0, 0.0
    elif row['home_score'] == row['away_score']:
        act_home, act_away = 0.5, 0.5
    else:
        act_home, act_away = 0.0, 1.0

    # K-factor
    k = get_k_factor(row['tournament'])

    # Update Elo
    elo_ratings[home] = elo_home + k * (act_home - exp_home)
    elo_ratings[away] = elo_away + k * (act_away - exp_away)

elo_df = pd.DataFrame(elo_history)
print(f"  ✓ Elo calculated for {len(elo_ratings)} teams across {len(elo_df):,} matches")

# Print current top 10 Elo ratings
current_elo = pd.Series(elo_ratings).sort_values(ascending=False)
print("\n  Current Top 10 Elo ratings:")
for team, elo in current_elo.head(10).items():
    print(f"    {team:<25} {elo:.1f}")


# ============================================================
# STEP 7 — ROLLING FORM CALCULATION
# ============================================================
# For each match, calculate the following for both teams
# based on their last 10 matches BEFORE this match date:
#   - win rate (form)
#   - avg goals scored
#   - avg goals conceded
# ============================================================

print("\nStep 7: Calculating rolling form...")

# Build a flat match results table from each team's perspective
home_results = df[['date','home_team','away_team','home_score','away_score']].copy()
home_results.columns = ['date','team','opponent','goals_for','goals_against']

away_results = df[['date','away_team','home_team','away_score','home_score']].copy()
away_results.columns = ['date','team','opponent','goals_for','goals_against']

all_results = pd.concat([home_results, away_results], ignore_index=True)
all_results = all_results.sort_values('date').reset_index(drop=True)
all_results['win'] = (all_results['goals_for'] > all_results['goals_against']).astype(int)

def get_rolling_form(team, before_date, n=10):
    """Get rolling stats for a team across their last n matches before a date."""
    past = all_results[
        (all_results['team'] == team) &
        (all_results['date'] < before_date)
    ].tail(n)

    if len(past) == 0:
        return {'form': 0.5, 'avg_scored': 1.5, 'avg_conceded': 1.5, 'matches': 0}

    return {
        'form':          round(past['win'].mean(), 4),
        'avg_scored':    round(past['goals_for'].mean(), 4),
        'avg_conceded':  round(past['goals_against'].mean(), 4),
        'matches':       len(past)
    }

# Calculate form for every match
form_records = []
total = len(df)

for i, row in df.iterrows():
    if i % 5000 == 0:
        print(f"  Processing match {i:,} / {total:,}...")

    home_form = get_rolling_form(row['home_team'], row['date'])
    away_form = get_rolling_form(row['away_team'], row['date'])

    form_records.append({
        'date':               row['date'],
        'home_team':          row['home_team'],
        'away_team':          row['away_team'],
        'home_form':          home_form['form'],
        'away_form':          away_form['form'],
        'home_avg_scored':    home_form['avg_scored'],
        'away_avg_scored':    away_form['avg_scored'],
        'home_avg_conceded':  home_form['avg_conceded'],
        'away_avg_conceded':  away_form['avg_conceded'],
    })

form_df = pd.DataFrame(form_records)
print(f"  ✓ Rolling form calculated for {len(form_df):,} matches")


# ============================================================
# STEP 8 — HEAD-TO-HEAD FEATURE
# ============================================================
# For each match, count home team's historical win % against
# this specific away team, using only matches BEFORE this date.
# ============================================================

print("\nStep 8: Calculating head-to-head features...")

h2h_records = []

for _, row in df.iterrows():
    home = row['home_team']
    away = row['away_team']
    date = row['date']

    # All prior meetings between these two teams
    prior = df[
        (df['date'] < date) &
        (
            ((df['home_team'] == home) & (df['away_team'] == away)) |
            ((df['home_team'] == away) & (df['away_team'] == home))
        )
    ]

    if len(prior) == 0:
        h2h_records.append({
            'date':          date,
            'home_team':     home,
            'away_team':     away,
            'h2h_matches':   0,
            'h2h_home_wins': 0,
            'h2h_draws':     0,
            'h2h_away_wins': 0,
            'h2h_home_winpct': 0.33  # neutral prior when no history
        })
        continue

    home_wins = (
        ((prior['home_team'] == home) & (prior['home_score'] > prior['away_score'])) |
        ((prior['away_team'] == home) & (prior['away_score'] > prior['home_score']))
    ).sum()

    away_wins = (
        ((prior['home_team'] == away) & (prior['home_score'] > prior['away_score'])) |
        ((prior['away_team'] == away) & (prior['away_score'] > prior['home_score']))
    ).sum()

    draws = (prior['home_score'] == prior['away_score']).sum()
    total = len(prior)

    h2h_records.append({
        'date':              date,
        'home_team':         home,
        'away_team':         away,
        'h2h_matches':       total,
        'h2h_home_wins':     int(home_wins),
        'h2h_draws':         int(draws),
        'h2h_away_wins':     int(away_wins),
        'h2h_home_winpct':   round(home_wins / total, 4)
    })

h2h_df = pd.DataFrame(h2h_records)
print(f"  ✓ H2H features calculated for {len(h2h_df):,} matches")


# ============================================================
# STEP 9 — BUILD match_features TABLE
# ============================================================
# Join Elo + Form + H2H into one row per match.
# Add tournament weight, squad value diff, WC experience diff,
# is_neutral flag, and result (target variable).
#
# Target: result
#   1  = home team wins
#   0  = draw
#  -1  = away team wins
#
# We only use matches from 1990 onwards for ML training —
# pre-1990 football is structurally different (fewer teams,
# different tournament structures, lower data quality).
# ============================================================

print("\nStep 9: Building match_features table...")

# Load squad values from national_teams
squad_values = pd.read_sql("""
    SELECT name AS team,
           COALESCE(total_market_value, 0) / 1000000 AS squad_value_m
    FROM national_teams
""", engine)
squad_val_dict = dict(zip(squad_values['team'], squad_values['squad_value_m']))

# Load WC appearances from wc_matches
wc_appearances = pd.read_sql("""
    SELECT team, COUNT(DISTINCT year) AS wc_appearances
    FROM (
        SELECT year, home_team AS team FROM wc_matches
        UNION ALL
        SELECT year, away_team AS team FROM wc_matches
    ) t
    GROUP BY team
""", engine)
wc_app_dict = dict(zip(wc_appearances['team'], wc_appearances['wc_appearances']))

# Tournament weight (reuse K-factor logic)
def get_tournament_weight(tournament):
    t = tournament.lower()
    if 'world cup' in t and 'qualifier' not in t:
        return 3
    elif any(x in t for x in ['euro', 'copa america', 'africa cup', 'asian cup']):
        return 2
    elif 'qualifier' in t or 'qualification' in t:
        return 2
    elif 'friendly' in t:
        return 1
    else:
        return 2

# Merge all features
features = df.copy()
features = features.merge(elo_df,  on=['date','home_team','away_team'], how='left')
features = features.merge(form_df, on=['date','home_team','away_team'], how='left')
features = features.merge(h2h_df,  on=['date','home_team','away_team'], how='left')

# Add derived features
features['squad_value_home'] = features['home_team'].map(squad_val_dict).fillna(0)
features['squad_value_away'] = features['away_team'].map(squad_val_dict).fillna(0)
features['squad_value_diff'] = features['squad_value_home'] - features['squad_value_away']

features['wc_exp_home'] = features['home_team'].map(wc_app_dict).fillna(0)
features['wc_exp_away'] = features['away_team'].map(wc_app_dict).fillna(0)
features['wc_exp_diff'] = features['wc_exp_home'] - features['wc_exp_away']

features['tournament_weight'] = features['tournament'].apply(get_tournament_weight)
features['is_neutral'] = features['neutral'].astype(int)

# Target variable
features['result'] = np.where(
    features['home_score'] > features['away_score'], 1,
    np.where(features['home_score'] == features['away_score'], 0, -1)
)

# Filter to 1990 onwards for ML relevance
features['year'] = features['date'].dt.year
features_ml = features[features['year'] >= 1990].copy()

# Select final columns for match_features table
final_cols = [
    'date', 'home_team', 'away_team',
    'home_score', 'away_score', 'tournament',
    'home_elo', 'away_elo', 'elo_diff',
    'home_form', 'away_form',
    'home_avg_scored', 'away_avg_scored',
    'home_avg_conceded', 'away_avg_conceded',
    'h2h_matches', 'h2h_home_winpct',
    'squad_value_diff',
    'wc_exp_diff',
    'tournament_weight',
    'is_neutral',
    'result'
]

match_features = features_ml[final_cols].copy()
match_features['date'] = match_features['date'].dt.date

print(f"  match_features shape: {match_features.shape}")
print(f"  Date range: {match_features['date'].min()} to {match_features['date'].max()}")
print(f"  Result distribution:")
print(match_features['result'].value_counts().to_string())

# Write to Supabase
print("\n  Writing match_features to Supabase...")

# Create table first
with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS match_features"))
    conn.execute(text("""
        CREATE TABLE match_features (
            id                  SERIAL PRIMARY KEY,
            date                DATE NOT NULL,
            home_team           TEXT NOT NULL,
            away_team           TEXT NOT NULL,
            home_score          SMALLINT,
            away_score          SMALLINT,
            tournament          TEXT,
            home_elo            NUMERIC(8,2),
            away_elo            NUMERIC(8,2),
            elo_diff            NUMERIC(8,2),
            home_form           NUMERIC(6,4),
            away_form           NUMERIC(6,4),
            home_avg_scored     NUMERIC(6,4),
            away_avg_scored     NUMERIC(6,4),
            home_avg_conceded   NUMERIC(6,4),
            away_avg_conceded   NUMERIC(6,4),
            h2h_matches         SMALLINT,
            h2h_home_winpct     NUMERIC(6,4),
            squad_value_diff    NUMERIC(10,2),
            wc_exp_diff         SMALLINT,
            tournament_weight   SMALLINT,
            is_neutral          SMALLINT,
            result              SMALLINT NOT NULL
        )
    """))
    conn.commit()

match_features.to_sql(
    'match_features', engine,
    if_exists='append', index=False,
    chunksize=1000, method='multi'
)

print(f"  ✓ {len(match_features):,} rows written to match_features table")

# Quick verification
verify = pd.read_sql("SELECT COUNT(*) AS cnt FROM match_features", engine)
print(f"  ✓ Verified: {verify['cnt'].iloc[0]:,} rows in Supabase")

print("\n✅ Phase 2 Part B complete.")
print("   match_features table is ready for XGBoost training in Phase 3.")