# ============================================================
# FIFA World Cup 2026 Analytics Platform
# 03_train_model.py
# Phase 3 — XGBoost Match Outcome Predictor
# ============================================================
# What this script does:
#   Step 10: Load match_features, split train/test by date
#   Step 11: Train XGBoost classifier
#   Step 12: Evaluate model — accuracy, confusion matrix,
#            feature importance, backtesting on 2018 + 2022
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pickle
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
from sklearn.metrics import (
    accuracy_score, confusion_matrix,
    classification_report, log_loss
)
from xgboost import XGBClassifier
import xgboost as xgb

load_dotenv()
engine = create_engine(os.getenv("CONNECTION_STRING"))

# ============================================================
# STEP 10 — LOAD DATA & TRAIN/TEST SPLIT
# ============================================================
# We split by DATE not randomly.
# Random splitting would leak future data into training —
# the model would "see" 2022 matches while training on 2018,
# which makes accuracy look falsely high.
#
# Split:
#   Train → 1990 to 2017 (learn historical patterns)
#   Test  → 2018 to 2024 (evaluate on unseen data)
#
# Backtesting:
#   Train → pre-2018, predict 2018 WC
#   Train → pre-2022, predict 2022 WC
# ============================================================

print("Step 10: Loading match_features and splitting...")

df = pd.read_sql("""
    SELECT * FROM match_features
    ORDER BY date ASC
""", engine)

df['date'] = pd.to_datetime(df['date'])
df['year'] = df['date'].dt.year

# Features used for training
FEATURES = [
    'home_elo', 'away_elo', 'elo_diff',
    'home_form', 'away_form',
    'home_avg_scored', 'away_avg_scored',
    'home_avg_conceded', 'away_avg_conceded',
    'h2h_home_winpct',
    'squad_value_diff',
    'wc_exp_diff',
    'tournament_weight',
    'is_neutral'
]

TARGET = 'result'

# Map result to XGBoost classes (must be 0, 1, 2)
# -1 (away win) → 0
#  0 (draw)     → 1
#  1 (home win) → 2
df['target'] = df[TARGET].map({-1: 0, 0: 1, 1: 2})

# Train/test split by date
train = df[df['year'] <= 2017]
test  = df[df['year'] >= 2018]

X_train = train[FEATURES]
y_train = train['target']
X_test  = test[FEATURES]
y_test  = test['target']

print(f"  Train: {len(train):,} matches (1990–2017)")
print(f"  Test:  {len(test):,} matches (2018–2024)")
print(f"  Features: {len(FEATURES)}")


# ============================================================
# STEP 11 — TRAIN XGBOOST MODEL
# ============================================================
# XGBoost is a gradient boosting model that builds many
# decision trees sequentially, each one correcting errors
# from the previous. It works extremely well on tabular data.
#
# Key parameters:
#   n_estimators   → how many trees to build
#   max_depth      → how deep each tree can go
#   learning_rate  → how much each tree contributes
#   subsample      → fraction of data per tree (prevents overfitting)
# ============================================================

print("\nStep 11: Training XGBoost model...")

model = XGBClassifier(
    n_estimators=300,
    max_depth=4,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    use_label_encoder=False,
    eval_metric='mlogloss',
    random_state=42,
    n_jobs=-1
)

model.fit(
    X_train, y_train,
    eval_set=[(X_test, y_test)],
    verbose=False
)

print("  ✓ Model trained")

# Save model
os.makedirs('ml', exist_ok=True)
with open('ml/xgboost_model.pkl', 'wb') as f:
    pickle.dump(model, f)
print("  ✓ Model saved to ml/xgboost_model.pkl")


# ============================================================
# STEP 12 — MODEL EVALUATION
# ============================================================
# Accuracy alone is misleading for football prediction.
# We evaluate using:
#   - Accuracy vs naive baseline (always predict home win)
#   - Log loss (measures confidence in probabilities)
#   - Confusion matrix (where does it go wrong?)
#   - Feature importance (what actually drives predictions?)
#   - Backtesting on 2018 and 2022 World Cups specifically
# ============================================================

print("\nStep 12: Evaluating model...")

y_pred = model.predict(X_test)
y_prob = model.predict_proba(X_test)

# Overall accuracy
accuracy = accuracy_score(y_test, y_pred)
baseline = (y_test == 2).mean()  # always predict home win
logloss  = log_loss(y_test, y_prob)

print(f"\n  Model accuracy:    {accuracy:.3f} ({accuracy*100:.1f}%)")
print(f"  Naive baseline:    {baseline:.3f} ({baseline*100:.1f}%)")
print(f"  Improvement:       +{(accuracy-baseline)*100:.1f}pp over baseline")
print(f"  Log loss:          {logloss:.4f}")

# Classification report
print("\n  Classification Report:")
print(classification_report(
    y_test, y_pred,
    target_names=['Away Win', 'Draw', 'Home Win']
))

# Confusion matrix
cm = confusion_matrix(y_test, y_pred)
print("  Confusion Matrix:")
print("                 Pred Away  Pred Draw  Pred Home")
labels = ['Away Win', 'Draw    ', 'Home Win']
for i, row in enumerate(cm):
    print(f"  Actual {labels[i]}:  {row[0]:6d}     {row[1]:6d}     {row[2]:6d}")


# ── Feature Importance ──────────────────────────────────────
print("\n  Feature Importance:")
importance = pd.Series(
    model.feature_importances_,
    index=FEATURES
).sort_values(ascending=False)

for feat, score in importance.items():
    bar = '█' * int(score * 200)
    print(f"  {feat:<25} {score:.4f}  {bar}")

# Save feature importance chart
fig, ax = plt.subplots(figsize=(10, 6))
importance.plot(kind='barh', ax=ax, color='steelblue')
ax.set_title('XGBoost Feature Importance — FIFA Match Predictor', fontsize=14)
ax.set_xlabel('Importance Score')
ax.invert_yaxis()
plt.tight_layout()
plt.savefig('ml/feature_importance.png', dpi=150)
plt.close()
print("\n  ✓ Feature importance chart saved to ml/feature_importance.png")


# ── Backtesting: 2018 World Cup ─────────────────────────────
print("\n  Backtesting on 2018 World Cup...")

train_2018 = df[df['year'] < 2018]
test_2018  = df[
    (df['year'] == 2018) &
    (df['tournament'].str.contains('World Cup', case=False, na=False))
]

model_2018 = XGBClassifier(
    n_estimators=300, max_depth=4, learning_rate=0.05,
    subsample=0.8, colsample_bytree=0.8,
    use_label_encoder=False, eval_metric='mlogloss',
    random_state=42, n_jobs=-1
)
model_2018.fit(train_2018[FEATURES], train_2018['target'], verbose=False)

if len(test_2018) > 0:
    pred_2018 = model_2018.predict(test_2018[FEATURES])
    acc_2018  = accuracy_score(test_2018['target'], pred_2018)
    print(f"  2018 WC accuracy: {acc_2018:.3f} ({len(test_2018)} matches)")
else:
    print("  No 2018 WC matches found in dataset")


# ── Backtesting: 2022 World Cup ─────────────────────────────
print("\n  Backtesting on 2022 World Cup...")

train_2022 = df[df['year'] < 2022]
test_2022  = df[
    (df['year'] == 2022) &
    (df['tournament'].str.contains('World Cup', case=False, na=False))
]

model_2022 = XGBClassifier(
    n_estimators=300, max_depth=4, learning_rate=0.05,
    subsample=0.8, colsample_bytree=0.8,
    use_label_encoder=False, eval_metric='mlogloss',
    random_state=42, n_jobs=-1
)
model_2022.fit(train_2022[FEATURES], train_2022['target'], verbose=False)

if len(test_2022) > 0:
    pred_2022 = model_2022.predict(test_2022[FEATURES])
    acc_2022  = accuracy_score(test_2022['target'], pred_2022)
    print(f"  2022 WC accuracy: {acc_2022:.3f} ({len(test_2022)} matches)")

    # Show predicted vs actual for 2022 WC
    test_2022 = test_2022.copy()
    test_2022['predicted'] = pred_2022
    result_map = {0: 'Away Win', 1: 'Draw', 2: 'Home Win'}
    test_2022['pred_label']   = test_2022['predicted'].map(result_map)
    test_2022['actual_label'] = test_2022['target'].map(result_map)
    test_2022['correct']      = test_2022['predicted'] == test_2022['target']

    print(f"\n  2022 WC — Sample predictions:")
    print(f"  {'Home':<25} {'Away':<25} {'Predicted':<12} {'Actual':<12} {'Correct'}")
    print(f"  {'-'*90}")
    for _, r in test_2022.head(15).iterrows():
        tick = '✅' if r['correct'] else '❌'
        print(f"  {r['home_team']:<25} {r['away_team']:<25} {r['pred_label']:<12} {r['actual_label']:<12} {tick}")
else:
    print("  No 2022 WC matches found in dataset")


# ── Predict a sample match ───────────────────────────────────
print("\n  Sample prediction — Brazil vs France (neutral):")

sample = pd.DataFrame([{
    'home_elo':          1436.6,
    'away_elo':          1537.0,
    'elo_diff':          -100.4,
    'home_form':         0.62,
    'away_form':         0.65,
    'home_avg_scored':   2.1,
    'away_avg_scored':   2.3,
    'home_avg_conceded': 0.9,
    'away_avg_conceded': 0.8,
    'h2h_home_winpct':   0.41,
    'squad_value_diff':  -7.5,
    'wc_exp_diff':       6,
    'tournament_weight': 3,
    'is_neutral':        1
}])

probs = model.predict_proba(sample)[0]
print(f"  Brazil Win:  {probs[2]*100:.1f}%")
print(f"  Draw:        {probs[1]*100:.1f}%")
print(f"  France Win:  {probs[0]*100:.1f}%")

print("\n✅ Phase 3 Step 12 complete.")
print("   Run 04_monte_carlo.py next to simulate the 2026 tournament.")

model.get_booster().save_model('ml/xgboost_model.json')
print("✓ Model saved as xgboost_model.json")