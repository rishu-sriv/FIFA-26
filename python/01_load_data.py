import pandas as pd
from sqlalchemy import create_engine
import numpy as np

# ============================================================
# CONFIGURATION — paste your Supabase connection string here
# ============================================================
from dotenv import load_dotenv
import os

load_dotenv()
CONNECTION_STRING = os.getenv("CONNECTION_STRING")
engine = create_engine(CONNECTION_STRING)

print("Connected to Supabase successfully.\n")

# ============================================================
# HELPER — standardise country names using former_names.csv
# This ensures "Dahomey" becomes "Benin" everywhere
# ============================================================
former = pd.read_csv("data/raw/former_names.csv")
name_map = dict(zip(former["former"], former["current"]))

def standardise_team(name):
    return name_map.get(name, name)

# ============================================================
# LOAD 1: former_names (load first — used by other loaders)
# ============================================================
print("Loading former_names...")
df = pd.read_csv("data/raw/former_names.csv")
df.columns = ["current", "former", "start_date", "end_date"]
df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce").dt.date
df["end_date"]   = pd.to_datetime(df["end_date"],   errors="coerce").dt.date
df.to_sql("former_names", engine, if_exists="append", index=False)
print(f"  ✓ {len(df):,} rows loaded")

# ============================================================
# LOAD 2: matches (results.csv)
# ============================================================
print("Loading matches...")
df = pd.read_csv("data/raw/results.csv", low_memory=False)
df.columns = ["date","home_team","away_team","home_score","away_score","tournament","city","country","neutral"]
df["date"]       = pd.to_datetime(df["date"], errors="coerce").dt.date
df["home_score"] = pd.to_numeric(df["home_score"], errors="coerce").astype("Int64")
df["away_score"] = pd.to_numeric(df["away_score"], errors="coerce").astype("Int64")
df["home_team"]  = df["home_team"].apply(standardise_team)
df["away_team"]  = df["away_team"].apply(standardise_team)
df.to_sql("matches", engine, if_exists="append", index=False)
print(f"  ✓ {len(df):,} rows loaded")

# ============================================================
# LOAD 3: goalscorers
# ============================================================
print("Loading goalscorers...")
df = pd.read_csv("data/raw/goalscorers.csv", low_memory=False)
df["date"]      = pd.to_datetime(df["date"], errors="coerce").dt.date
df["home_team"] = df["home_team"].apply(standardise_team)
df["away_team"] = df["away_team"].apply(standardise_team)
df["team"]      = df["team"].apply(standardise_team)
df["minute"]    = pd.to_numeric(df["minute"], errors="coerce")
df.to_sql("goalscorers", engine, if_exists="append", index=False)
print(f"  ✓ {len(df):,} rows loaded")

# ============================================================
# LOAD 4: shootouts
# ============================================================
print("Loading shootouts...")
df = pd.read_csv("data/raw/shootouts.csv", low_memory=False)
df["date"]      = pd.to_datetime(df["date"], errors="coerce").dt.date
df["home_team"] = df["home_team"].apply(standardise_team)
df["away_team"] = df["away_team"].apply(standardise_team)
df["winner"]    = df["winner"].apply(standardise_team)
df.to_sql("shootouts", engine, if_exists="append", index=False)
print(f"  ✓ {len(df):,} rows loaded")

# ============================================================
# LOAD 5: wc_history
# ============================================================
print("Loading wc_history...")
df = pd.read_csv("data/raw/world_cup.csv", low_memory=False)
df.columns = ["year","host","teams","champion","runner_up","top_scorer","attendance","attendance_avg","matches"]
df.to_sql("wc_history", engine, if_exists="append", index=False)
print(f"  ✓ {len(df):,} rows loaded")

# ============================================================
# LOAD 6: wc_matches (only keep columns we need)
# ============================================================
print("Loading wc_matches...")
df = pd.read_csv("data/raw/matches_1930_2022.csv", low_memory=False)

# Clean non-breaking spaces from manager/captain names
for col in ["home_manager","away_manager","home_captain","away_captain"]:
    df[col] = df[col].astype(str).str.replace("\xa0", " ", regex=False).str.strip()

keep = ["Year","Date","Round","Host","home_team","away_team",
        "home_score","away_score","home_xg","away_xg",
        "home_penalty","away_penalty",
        "home_manager","away_manager","home_captain","away_captain",
        "Venue","Attendance","Referee","Notes"]
df = df[keep].copy()
df.columns = ["year","date","round","host","home_team","away_team",
              "home_score","away_score","home_xg","away_xg",
              "home_penalty","away_penalty",
              "home_manager","away_manager","home_captain","away_captain",
              "venue","attendance","referee","notes"]
df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
df["home_team"] = df["home_team"].apply(standardise_team)
df["away_team"] = df["away_team"].apply(standardise_team)
df.to_sql("wc_matches", engine, if_exists="append", index=False)
print(f"  ✓ {len(df):,} rows loaded")

# ============================================================
# LOAD 7: schedule_2026
# ============================================================
print("Loading schedule_2026...")
df = pd.read_csv("data/raw/schedule_2026.csv", low_memory=False)
df = df[["Round","Date","home_team","away_team","Time"]].copy()
df.columns = ["round","date","home_team","away_team","kickoff"]
df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
df.to_sql("schedule_2026", engine, if_exists="append", index=False)
print(f"  ✓ {len(df):,} rows loaded")

# ============================================================
# LOAD 8: rankings_historical
# ============================================================
print("Loading rankings_historical...")
df = pd.read_csv("data/raw/fifa_ranking-2026-01-19.csv", low_memory=False)
df = df.drop(columns=["Unnamed: 0"], errors="ignore")
df.columns = ["rank","country_full","country_abrv","total_points",
              "previous_points","rank_change","confederation","rank_date"]
df["rank_date"] = pd.to_datetime(df["rank_date"], errors="coerce").dt.date
df["rank"]      = pd.to_numeric(df["rank"], errors="coerce").astype("Int64")
df.to_sql("rankings_historical", engine, if_exists="append", index=False)
print(f"  ✓ {len(df):,} rows loaded")

# ============================================================
# LOAD 9: national_teams
# ============================================================
print("Loading national_teams...")
df = pd.read_csv("data/raw/national_teams.csv", low_memory=False)
keep = ["national_team_id","name","country_name","confederation",
        "squad_size","average_age","total_market_value",
        "foreigners_number","foreigners_percentage","fifa_ranking","last_season","url"]
df = df[keep].copy()
df["total_market_value"] = pd.to_numeric(df["total_market_value"], errors="coerce")
df.to_sql("national_teams", engine, if_exists="append", index=False)
print(f"  ✓ {len(df):,} rows loaded")

# ============================================================
# LOAD 10: players
# ============================================================
print("Loading players...")
df = pd.read_csv("data/raw/players.csv", low_memory=False)
keep = ["player_id","name","first_name","last_name",
        "country_of_citizenship","date_of_birth","position","sub_position",
        "foot","height_in_cm","market_value_in_eur","highest_market_value_in_eur",
        "international_caps","international_goals",
        "current_national_team_id","current_club_name","last_season"]
df = df[keep].copy()
df["date_of_birth"] = pd.to_datetime(df["date_of_birth"], errors="coerce").dt.date
df["international_caps"]  = pd.to_numeric(df["international_caps"],  errors="coerce").astype("Int64")
df["international_goals"] = pd.to_numeric(df["international_goals"], errors="coerce").astype("Int64")
df["current_national_team_id"] = pd.to_numeric(df["current_national_team_id"], errors="coerce").astype("Int64")
df.to_sql("players", engine, if_exists="append", index=False)
print(f"  ✓ {len(df):,} rows loaded")

# ============================================================
# LOAD 11: player_valuations
# ============================================================
print("Loading player_valuations...")
df = pd.read_csv("data/raw/player_valuations.csv", low_memory=False)
keep = ["player_id","date","market_value_in_eur","current_club_name","current_club_id"]
df = df[keep].copy()
df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
df["market_value_in_eur"] = pd.to_numeric(df["market_value_in_eur"], errors="coerce")
# Load in chunks — 507k rows, chunking avoids memory issues
df.to_sql("player_valuations", engine, if_exists="append", index=False,
          chunksize=10000, method="multi")
print(f"  ✓ {len(df):,} rows loaded")

print("\n✅ All tables loaded successfully.")