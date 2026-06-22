# FIFA World Cup 2026 — Analytics & Prediction Platform

Who is going to win the 2026 World Cup?

This project answers that question using 150 years of international football data, machine learning, and tournament simulation.

---

## Objective

Predict the most likely winner of the FIFA World Cup 2026 by:
- Analysing historical match data from 1872 to 2026
- Building a machine learning model that predicts match outcomes
- Simulating the entire 2026 tournament 10,000 times
- Visualising insights and predictions in an interactive dashboard

---

## Data Sources

| Dataset | Source | What it contains |
|---|---|---|
| International match results | Kaggle (martj42) | Every international match since 1872 — 49,477 matches |
| FIFA World Cup history | Kaggle (piterfm) | Every WC match 1930–2022 with xG, managers, captains |
| FIFA World Rankings | Kaggle | Historical rankings for every team since 1992 |
| 2026 WC Schedule | Kaggle (piterfm) | Full fixture list for the 2026 tournament |
| Squad & player data | Transfermarkt (Kaggle) | 47,716 players with market values and international caps |

---

## Methodology

### Step 1 — Store (PostgreSQL on Supabase)
All raw data lives in 11 tables in a PostgreSQL database.
Think of this as the filing cabinet everything else draws from.

### Step 2 — Analyse (SQL)
SQL queries answer questions like:
- Which countries win the most?
- Does home advantage matter at World Cups?
- How do confederations compare in squad value?

### Step 3 — Engineer features (Python)
Raw data alone doesn't predict winners. We calculate signals that actually matter:

| Feature | What it means |
|---|---|
| Elo rating | A dynamic team strength score that updates after every match |
| Recent form | Win % across the last 10 matches |
| Avg goals scored | Attacking threat over recent matches |
| Avg goals conceded | Defensive solidity over recent matches |
| Head-to-head record | Historical record between these two specific teams |
| Squad market value | Total transfer value of the squad — a proxy for player quality |
| World Cup experience | How many World Cups has this team played in |
| Host advantage | Whether the team is playing on home soil |

### Step 4 — Predict (Machine Learning)
An XGBoost model is trained on 30 years of matches (1990–2020) and tested on recent matches (2021–2024).

For any match it outputs:
```
Brazil vs France
→ Brazil win:  38%
→ Draw:        24%
→ France win:  38%
```

A Poisson model also predicts the most likely scoreline.

### Step 5 — Simulate (Monte Carlo)
The 2026 tournament bracket is simulated 10,000 times using the match predictor.

Every group stage match, round of 32, quarter final, semi final, and final is played out — 10,000 times. The result is a win probability for every team:

```
Spain       22%
France      18%
Brazil      16%
Argentina   14%
England     11%
...
```

### Step 6 — Visualise (Power BI)
Three dashboard pages:
- **Historical** — which teams dominated, goals over the decades, host nation effect
- **Team explorer** — pick any team and see their full history, form, Elo trajectory
- **2026 Predictions** — tournament winner probabilities, stage-by-stage breakdown

---

## Key Findings

> To be updated after analysis is complete.

---

## Tools Used

| Tool | Purpose |
|---|---|
| PostgreSQL (Supabase) | Database — stores all raw and processed data |
| Python (pandas, numpy) | Data cleaning and feature engineering |
| XGBoost | Match outcome prediction model |
| SciPy | Poisson distribution for scoreline prediction |
| Monte Carlo simulation | Tournament winner probability |
| Power BI | Interactive dashboards |
| GitHub | Version control and project showcase |

---

## Project Structure

```
fifa/
├── sql/
│   ├── 01_create_tables.sql    — database schema
│   └── 02_analytics.sql        — SQL insight queries
├── python/
│   ├── 01_load_data.py         — loads raw CSVs into PostgreSQL
│   └── 02_features.py          — calculates Elo, form, H2H features
├── ml/
│   ├── 03_train_model.py       — trains XGBoost match predictor
│   └── 04_monte_carlo.py       — simulates 2026 tournament 10,000 times
├── powerbi/
│   └── screenshots/            — dashboard screenshots
├── requirements.txt
└── README.md
```

---

## How to Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up database
# Run sql/01_create_tables.sql in your PostgreSQL instance

# 3. Load data
python python/01_load_data.py

# 4. Build features
python python/02_features.py

# 5. Train model and simulate
python ml/03_train_model.py
python ml/04_monte_carlo.py
```

---

## Limitations

- Real-time injury data is not available — squad adjustments applied manually before simulation
- Club-level form in the weeks before the tournament is not captured
- Tactical matchup nuances and managerial changes are not modelled
- Player ratings frozen at last available Transfermarkt snapshot

---

*Built as a portfolio project demonstrating SQL, Python, machine learning, and business intelligence skills.*# FIFA-26
