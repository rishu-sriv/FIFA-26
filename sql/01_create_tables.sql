-- ============================================================
-- FIFA World Cup 2026 Analytics Platform
-- 01_create_tables.sql
-- Schema as deployed on Supabase
-- ============================================================


-- 1. Former names
-- Maps historical country names to current names
-- Used for data standardisation across all tables
CREATE TABLE former_names (
    id          SERIAL PRIMARY KEY,
    current     TEXT NOT NULL,
    former      TEXT NOT NULL,
    start_date  DATE,
    end_date    DATE
);


-- 2. Matches
-- Every international match played since 1872 (49,477 rows)
-- Backbone of Elo calculation and form features
CREATE TABLE matches (
    id          SERIAL PRIMARY KEY,
    date        DATE NOT NULL,
    home_team   TEXT NOT NULL,
    away_team   TEXT NOT NULL,
    home_score  SMALLINT,
    away_score  SMALLINT,
    tournament  TEXT NOT NULL,
    city        TEXT,
    country     TEXT,
    neutral     BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_matches_date       ON matches(date);
CREATE INDEX idx_matches_home_team  ON matches(home_team);
CREATE INDEX idx_matches_away_team  ON matches(away_team);
CREATE INDEX idx_matches_tournament ON matches(tournament);


-- 3. Goalscorers
-- Individual goal events (47,690 rows)
-- Used to calculate avg goals scored per team
CREATE TABLE goalscorers (
    id          SERIAL PRIMARY KEY,
    date        DATE NOT NULL,
    home_team   TEXT NOT NULL,
    away_team   TEXT NOT NULL,
    team        TEXT NOT NULL,
    scorer      TEXT,
    minute      NUMERIC,
    own_goal    BOOLEAN NOT NULL DEFAULT FALSE,
    penalty     BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_goalscorers_date ON goalscorers(date);
CREATE INDEX idx_goalscorers_team ON goalscorers(team);


-- 4. Shootouts
-- Penalty shootout results (678 rows)
-- Used in Monte Carlo simulation for knockout tiebreakers
CREATE TABLE shootouts (
    id            SERIAL PRIMARY KEY,
    date          DATE NOT NULL,
    home_team     TEXT NOT NULL,
    away_team     TEXT NOT NULL,
    winner        TEXT NOT NULL,
    first_shooter TEXT
);

CREATE INDEX idx_shootouts_date ON shootouts(date);


-- 5. World Cup history
-- One row per tournament (22 rows)
-- Used for wc_experience and wc_appearances features
CREATE TABLE wc_history (
    id              SERIAL PRIMARY KEY,
    year            SMALLINT NOT NULL UNIQUE,
    host            TEXT NOT NULL,
    teams           SMALLINT,
    champion        TEXT NOT NULL,
    runner_up       TEXT NOT NULL,
    top_scorer      TEXT,
    attendance      INTEGER,
    attendance_avg  INTEGER,
    matches         SMALLINT
);


-- 6. World Cup matches
-- Detailed match data for every WC game 1930-2022 (964 rows)
-- Includes xG, managers, captains, round, venue
CREATE TABLE wc_matches (
    id              SERIAL PRIMARY KEY,
    year            SMALLINT NOT NULL,
    date            DATE NOT NULL,
    round           TEXT NOT NULL,
    host            TEXT NOT NULL,
    home_team       TEXT NOT NULL,
    away_team       TEXT NOT NULL,
    home_score      SMALLINT NOT NULL,
    away_score      SMALLINT NOT NULL,
    home_xg         NUMERIC,
    away_xg         NUMERIC,
    home_penalty    SMALLINT,
    away_penalty    SMALLINT,
    home_manager    TEXT,
    away_manager    TEXT,
    home_captain    TEXT,
    away_captain    TEXT,
    venue           TEXT,
    attendance      INTEGER,
    referee         TEXT,
    notes           TEXT
);

CREATE INDEX idx_wc_matches_year      ON wc_matches(year);
CREATE INDEX idx_wc_matches_home_team ON wc_matches(home_team);
CREATE INDEX idx_wc_matches_away_team ON wc_matches(away_team);


-- 7. Schedule 2026
-- Full 2026 World Cup fixture list (72 rows)
-- Feeds directly into the Monte Carlo simulation bracket
CREATE TABLE schedule_2026 (
    id        SERIAL PRIMARY KEY,
    round     TEXT NOT NULL,
    date      DATE NOT NULL,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    kickoff   TEXT
);

CREATE INDEX idx_schedule_2026_round ON schedule_2026(round);


-- 8. Rankings historical
-- FIFA world rankings for every team since 1992 (69,992 rows)
-- Used as ranking_diff feature in match_features table
CREATE TABLE rankings_historical (
    id               SERIAL PRIMARY KEY,
    rank_date        DATE NOT NULL,
    country_full     TEXT NOT NULL,
    country_abrv     TEXT,
    rank             SMALLINT,
    total_points     NUMERIC,
    previous_points  NUMERIC,
    rank_change      SMALLINT,
    confederation    TEXT
);

CREATE INDEX idx_rankings_hist_date    ON rankings_historical(rank_date);
CREATE INDEX idx_rankings_hist_country ON rankings_historical(country_full);


-- 9. National teams
-- Current squad summary per national team (118 rows)
-- Source: Transfermarkt | total_market_value = squad strength proxy
CREATE TABLE national_teams (
    id                     SERIAL PRIMARY KEY,
    national_team_id       INTEGER UNIQUE NOT NULL,
    name                   TEXT NOT NULL,
    team_code              TEXT,
    country_id             INTEGER,
    country_name           TEXT,
    country_code           TEXT,
    confederation          TEXT,
    team_image_url         TEXT,
    squad_size             SMALLINT,
    average_age            NUMERIC,
    foreigners_number      SMALLINT,
    foreigners_percentage  NUMERIC,
    total_market_value     NUMERIC,
    coach_name             TEXT,
    fifa_ranking           SMALLINT,
    last_season            SMALLINT,
    url                    TEXT
);


-- 10. Players
-- Individual player profiles (47,716 rows)
-- Source: Transfermarkt | used to calculate squad strength per nation
CREATE TABLE players (
    id                                  SERIAL PRIMARY KEY,
    player_id                           INTEGER UNIQUE NOT NULL,
    player_code                         TEXT,
    name                                TEXT NOT NULL,
    first_name                          TEXT,
    last_name                           TEXT,
    country_of_birth                    TEXT,
    city_of_birth                       TEXT,
    country_of_citizenship              TEXT,
    date_of_birth                       DATE,
    position                            TEXT,
    sub_position                        TEXT,
    foot                                TEXT,
    height_in_cm                        SMALLINT,
    market_value_in_eur                 NUMERIC,
    highest_market_value_in_eur         NUMERIC,
    international_caps                  SMALLINT,
    international_goals                 SMALLINT,
    current_national_team_id            INTEGER,
    current_club_id                     INTEGER,
    current_club_name                   TEXT,
    current_club_domestic_competition_id TEXT,
    contract_expiration_date            DATE,
    agent_name                          TEXT,
    image_url                           TEXT,
    url                                 TEXT,
    last_season                         SMALLINT
);

CREATE INDEX idx_players_citizenship   ON players(country_of_citizenship);
CREATE INDEX idx_players_national_team ON players(current_national_team_id);


-- 11. Player valuations
-- Historical market value per player over time (507,815 rows)
-- Used to calculate squad strength at any historical point
CREATE TABLE player_valuations (
    id                                  SERIAL PRIMARY KEY,
    player_id                           INTEGER NOT NULL,
    date                                DATE NOT NULL,
    market_value_in_eur                 NUMERIC NOT NULL,
    current_club_name                   TEXT,
    current_club_id                     INTEGER,
    player_club_domestic_competition_id TEXT
);

CREATE INDEX idx_player_val_player_id ON player_valuations(player_id);
CREATE INDEX idx_player_val_date      ON player_valuations(date);