# FIFA World Cup 2026 — Analytics & Prediction Platform

> *Built by a Ronaldo fan who couldn't handle uncertainty.*

Who is going to win the 2026 World Cup? I built a data platform to find out — using 150 years of international football history, machine learning, and 10,000 tournament simulations.

**[Live Dashboard →](https://fifa-26.vercel.app)**

---

## What It Does

- Analyses **49,477 international matches** from 1872 to 2026
- Calculates **Elo ratings** for 336 national teams across all of history
- Trains an **XGBoost model** that predicts match outcomes at 60.2% accuracy (+12.3pp over baseline)
- Runs **10,000 Monte Carlo simulations** of the full 2026 World Cup bracket
- Surfaces insights through an **interactive analytics dashboard**

---

## The Answer

After 10,000 simulations of the 2026 World Cup:

| Team | Win Probability | Final % |
|---|---|---|
| 🇦🇷 Argentina | 23.2% | 35.3% |
| 🇪🇸 Spain | 17.1% | 27.3% |
| 🇧🇷 Brazil | 10.8% | 19.4% |
| 🏴󠁧󠁢󠁥󠁮󠁧󠁿 England | 9.2% | 17.5% |
| 🇩🇪 Germany | 8.8% | 17.4% |
| 🇫🇷 France | 7.7% | 14.9% |
| 🇵🇹 Portugal | 3.5% | 8.8% |

*Portugal at 3.5%. I built this project for Ronaldo and the data did this to me.*

---

## Key Findings

**Brazil is the greatest international team of all time**
63.4% all-time win rate across 1,060 matches. The only nation to qualify for every World Cup ever played — 22 consecutive tournaments.

**Football became dramatically more defensive**
Average goals per match dropped from 5.6 in the 1880s to 2.7 in the modern era. The defensive revolution happened in the 1960s and the game never recovered.

**Home advantage is real and statistically significant**
Teams win 50.7% of matches on home soil vs 44.2% at neutral venues — a 6.5 percentage point gap. But it only helps strong nations: Italy never lost a home World Cup match (83.3% win rate). Qatar lost all three in 2022 (0%).

**Elo difference explains 36% of all match outcomes**
The single most powerful predictor in the model. More predictive than FIFA rankings, recent form, or squad value combined.

**Argentina has never lost to Nigeria at a World Cup**
5 meetings. 5 Argentina wins. 0 draws. Pure psychological dominance.

**Netherlands is Brazil's kryptonite at World Cups**
Brazil leads the all-time H2H record but Netherlands leads 3-1 specifically at World Cup tournaments.

---

## How It Works

```
Raw Data (774,059 rows across 11 tables)
        ↓
PostgreSQL on Supabase
        ↓
SQL Analytics (historical patterns, H2H, squad strength)
        ↓
Python Feature Engineering
  → Elo ratings (49k matches, tournament-weighted K-factor)
  → Rolling form (last 10 matches per team)
  → Head-to-head records
  → Squad market values (Transfermarkt)
        ↓
XGBoost Match Predictor
  → Train: 1990–2017 (24,179 matches)
  → Test:  2018–2024 (8,150 matches)
  → Accuracy: 60.2% | Baseline: 47.9% | +12.3pp improvement
  → Backtested: 54.7% on 2018 WC | 56.1% on 2022 WC
        ↓
Monte Carlo Simulation (10,000 runs)
  → Real 2026 group structure (official FIFA draw)
  → 2026 FIFA tiebreaker rules (H2H before goal difference)
  → Knockout bracket with proportional draw redistribution
        ↓
Interactive Dashboard (React + Recharts)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Database | PostgreSQL (Supabase) |
| Data Engineering | Python, pandas, numpy |
| Analytics | SQL (PostgreSQL) |
| Machine Learning | XGBoost, scikit-learn |
| Simulation | Monte Carlo, custom tournament engine |
| Frontend | React, Tailwind CSS, Recharts |
| Deployment | Vercel |

---

## Project Structure

```
fifa/
├── sql/
│   ├── 01_create_tables.sql     — database schema (11 tables)
│   └── 02_analytics.sql         — SQL insight queries
├── python/
│   ├── 01_load_data.py          — loads raw CSVs into PostgreSQL
│   └── 02_features.py           — Elo, form, H2H feature engineering
├── ml/
│   ├── 03_train_model.py        — XGBoost training + backtesting
│   ├── 04_monte_carlo.py        — 10,000 tournament simulations
│   └── 05_match_predict.py      — interactive match predictor CLI
├── dashboard/                   — React analytics dashboard
├── powerbi/
│   └── screenshots/             — dashboard screenshots
├── .env.example                 — environment variable template
├── requirements.txt
└── README.md
```

---

## Data Sources

| Dataset | Source | Rows |
|---|---|---|
| International match results (1872–2026) | Kaggle (martj42) | 49,477 |
| FIFA World Cup history (1930–2022) | Kaggle (piterfm) | 964 |
| FIFA World Rankings (1992–2026) | Kaggle | 69,992 |
| 2026 WC Schedule (official) | Kaggle (piterfm) | 72 |
| Player & squad data | Transfermarkt (Kaggle) | 555,531 |

---

## How to Run

```bash
# 1. Clone the repo
git clone https://github.com/rishu-sriv/FIFA-26
cd FIFA-26

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment
cp .env.example .env
# Add your Supabase connection string to .env

# 4. Set up database
# Run sql/01_create_tables.sql in your PostgreSQL instance

# 5. Load data
python python/01_load_data.py

# 6. Build features
python python/02_features.py

# 7. Train model + simulate
python ml/03_train_model.py
python ml/04_monte_carlo.py

# 8. Predict any match
python ml/05_match_predict.py

# 9. Run dashboard locally
cd dashboard && npm install && npm run dev
```

---

## Model Performance

| Metric | Value |
|---|---|
| Training set | 24,179 matches (1990–2017) |
| Test set | 8,150 matches (2018–2024) |
| Accuracy | 60.2% |
| Naive baseline | 47.9% |
| Improvement | +12.3 percentage points |
| 2018 WC backtest | 54.7% (64 matches) |
| 2022 WC backtest | 56.1% (164 matches) |

**Top feature by importance:** Elo difference (36.2%) — the gap in team strength between two sides explains more than a third of all match outcomes.

---

## Limitations

- Knockout bracket randomised rather than following FIFA's fixed pathway structure
- Fair play tiebreaker (yellow/red cards) not simulated — no historical card data available
- Real-time injury data not incorporated — squad adjustments applied manually
- Player ratings frozen at last available Transfermarkt snapshot
- Draw prediction is weak (2% recall) — consistent with professional football prediction systems

---

## Why I Built This

I'm a data analyst and a football fan. Mostly a Ronaldo fan. The data says Portugal has a 3.5% chance of winning. I built the whole thing anyway.

---

*Built with Python, PostgreSQL, XGBoost, Monte Carlo simulation, and misplaced optimism about Portugal.*