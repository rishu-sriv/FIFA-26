-- ============================================================
-- FIFA World Cup 2026 Analytics Platform
-- 02_analytics.sql
-- Phase 2 Part A — SQL Analytics Layer
-- ============================================================
-- All queries run against the Supabase PostgreSQL database
-- Results feed into Power BI dashboards and README findings
-- ============================================================


-- ============================================================
-- STEP 1: HISTORICAL DOMINANCE
-- ============================================================
-- 1A: Top 10 nations by all-time win % (FIFA affiliated only)
-- 1B: Average goals per decade (1870s to 2020s)
-- 1C: Home ground vs neutral venue win rates
-- ============================================================

-- KEY FINDINGS:
-- Brazil leads all FIFA nations at 63.4% win rate (1,060 matches)
-- Goals per match dropped from 5.6 (1880s) to 2.7 (modern era)
-- Home advantage is real: 50.7% win rate vs 44.2% at neutral venues

SELECT '1A - Top 10 by win %' AS query,
    team, total_matches, wins, draws, losses, win_pct, points_pct
FROM (
    SELECT
        team,
        COUNT(*) AS total_matches,
        SUM(CASE WHEN result = 'win'  THEN 1 ELSE 0 END) AS wins,
        SUM(CASE WHEN result = 'draw' THEN 1 ELSE 0 END) AS draws,
        SUM(CASE WHEN result = 'loss' THEN 1 ELSE 0 END) AS losses,
        ROUND(SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS win_pct,
        ROUND((SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) * 3 +
               SUM(CASE WHEN result = 'draw' THEN 1 ELSE 0 END)) * 100.0 /
              (COUNT(*) * 3), 1) AS points_pct
    FROM (
        SELECT home_team AS team,
            CASE WHEN home_score > away_score THEN 'win'
                 WHEN home_score = away_score THEN 'draw'
                 ELSE 'loss' END AS result
        FROM matches WHERE home_score IS NOT NULL
        UNION ALL
        SELECT away_team AS team,
            CASE WHEN away_score > home_score THEN 'win'
                 WHEN away_score = home_score THEN 'draw'
                 ELSE 'loss' END AS result
        FROM matches WHERE away_score IS NOT NULL
    ) all_results
    WHERE team IN (
        SELECT DISTINCT home_team FROM matches
        WHERE tournament ILIKE '%World Cup%'
        UNION
        SELECT DISTINCT away_team FROM matches
        WHERE tournament ILIKE '%World Cup%'
    )
    GROUP BY team
    HAVING COUNT(*) >= 200
    ORDER BY win_pct DESC
    LIMIT 10
) q1a

UNION ALL

SELECT '1B - Goals per decade' AS query,
    CONCAT(FLOOR(EXTRACT(YEAR FROM date) / 10) * 10, 's') AS team,
    COUNT(*) AS total_matches,
    NULL::BIGINT AS wins,
    NULL::BIGINT AS draws,
    NULL::BIGINT AS losses,
    ROUND(AVG(home_score + away_score), 2) AS win_pct,
    NULL::NUMERIC AS points_pct
FROM matches
WHERE home_score IS NOT NULL
GROUP BY FLOOR(EXTRACT(YEAR FROM date) / 10) * 10

UNION ALL

SELECT '1C - Home vs neutral' AS query,
    CASE WHEN neutral THEN 'Neutral venue' ELSE 'Home ground' END AS team,
    COUNT(*) AS total_matches,
    SUM(CASE WHEN home_score > away_score THEN 1 ELSE 0 END) AS wins,
    SUM(CASE WHEN home_score = away_score THEN 1 ELSE 0 END) AS draws,
    SUM(CASE WHEN home_score < away_score THEN 1 ELSE 0 END) AS losses,
    ROUND(SUM(CASE WHEN home_score > away_score THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS win_pct,
    ROUND(AVG(home_score + away_score), 2) AS points_pct
FROM matches
WHERE home_score IS NOT NULL
GROUP BY neutral;


-- ============================================================
-- STEP 2: WORLD CUP SPECIFIC ANALYSIS
-- ============================================================
-- 2A: World Cup titles per country
-- 2B: Host nation performance at their own tournament
-- 2C: World Cup appearances per country (top 10)
-- ============================================================

-- KEY FINDINGS:
-- Brazil is the only nation to qualify for every World Cup (22 tournaments)
-- Italy won 4 titles and never lost a match as host nation (83.3% win rate)
-- Host advantage is conditional: strong nations win 70-100%, weak hosts underperform
-- Germany + West Germany combined = 4 titles, equal to Italy

SELECT '2A - WC wins per country' AS query,
    team,
    total_matches,
    NULL::BIGINT AS wins,
    NULL::BIGINT AS draws,
    NULL::BIGINT AS losses,
    NULL::NUMERIC AS win_pct,
    NULL::NUMERIC AS points_pct
FROM (
    SELECT champion AS team, COUNT(*) AS total_matches
    FROM wc_history
    GROUP BY champion
) q2a

UNION ALL

SELECT '2B - Host performance' AS query,
    w.host AS team,
    COUNT(*) AS total_matches,
    SUM(CASE
        WHEN (m.home_team = w.host AND m.home_score > m.away_score)
          OR (m.away_team = w.host AND m.away_score > m.home_score)
        THEN 1 ELSE 0 END) AS wins,
    SUM(CASE WHEN m.home_score = m.away_score THEN 1 ELSE 0 END) AS draws,
    SUM(CASE
        WHEN (m.home_team = w.host AND m.home_score < m.away_score)
          OR (m.away_team = w.host AND m.away_score < m.home_score)
        THEN 1 ELSE 0 END) AS losses,
    ROUND(SUM(CASE
        WHEN (m.home_team = w.host AND m.home_score > m.away_score)
          OR (m.away_team = w.host AND m.away_score > m.home_score)
        THEN 1.0 ELSE 0 END) * 100 / COUNT(*), 1) AS win_pct,
    NULL::NUMERIC AS points_pct
FROM wc_matches m
JOIN wc_history w ON m.year = w.year
WHERE m.home_team = w.host OR m.away_team = w.host
GROUP BY w.host

UNION ALL

SELECT '2C - WC appearances' AS query,
    team,
    total_matches,
    NULL::BIGINT AS wins,
    NULL::BIGINT AS draws,
    NULL::BIGINT AS losses,
    NULL::NUMERIC AS win_pct,
    NULL::NUMERIC AS points_pct
FROM (
    SELECT team, COUNT(*) AS total_matches
    FROM (
        SELECT DISTINCT year, home_team AS team FROM wc_matches
        UNION
        SELECT DISTINCT year, away_team AS team FROM wc_matches
    ) appearances
    GROUP BY team
    ORDER BY COUNT(*) DESC
    LIMIT 10
) q2c;


-- ============================================================
-- STEP 3: HEAD-TO-HEAD RECORDS
-- ============================================================
-- 3A: All-time H2H between top 6 nations
-- 3B: Penalty shootout win counts (top 10)
-- 3C: H2H specifically at World Cups (min 2 meetings)
-- ============================================================

-- KEY FINDINGS:
-- Argentina vs Brazil is the most played top-nation rivalry (110 matches)
-- Argentina has never lost to Nigeria at a World Cup (5-0-0)
-- Netherlands leads Brazil 3-1 at World Cups despite trailing all-time
-- Argentina leads all nations with 15 penalty shootout wins
-- Germany vs Spain: perfectly balanced at 9-9-9 across 27 matches

SELECT '3A - H2H all time' AS query,
    home_team || ' vs ' || away_team AS team,
    total_matches,
    home_wins AS wins,
    draws,
    away_wins AS losses,
    home_win_pct AS win_pct,
    NULL::NUMERIC AS points_pct
FROM (
    SELECT
        LEAST(home_team, away_team) AS home_team,
        GREATEST(home_team, away_team) AS away_team,
        COUNT(*) AS total_matches,
        SUM(CASE WHEN home_score > away_score THEN 1 ELSE 0 END) AS home_wins,
        SUM(CASE WHEN home_score = away_score THEN 1 ELSE 0 END) AS draws,
        SUM(CASE WHEN home_score < away_score THEN 1 ELSE 0 END) AS away_wins,
        ROUND(SUM(CASE WHEN home_score > away_score THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS home_win_pct
    FROM (
        SELECT
            LEAST(home_team, away_team) AS home_team,
            GREATEST(home_team, away_team) AS away_team,
            CASE WHEN home_team < away_team THEN home_score ELSE away_score END AS home_score,
            CASE WHEN home_team < away_team THEN away_score ELSE home_score END AS away_score
        FROM matches
        WHERE home_score IS NOT NULL
    ) normalised
    WHERE home_team IN ('Brazil','Argentina','France','Germany','Spain','England')
      AND away_team IN ('Brazil','Argentina','France','Germany','Spain','England')
      AND home_team != away_team
    GROUP BY home_team, away_team
    HAVING COUNT(*) >= 5
) h2h

UNION ALL

SELECT '3B - Shootout win rates' AS query,
    team,
    total_matches,
    NULL::BIGINT AS wins,
    NULL::BIGINT AS draws,
    NULL::BIGINT AS losses,
    NULL::NUMERIC AS win_pct,
    NULL::NUMERIC AS points_pct
FROM (
    SELECT winner AS team, COUNT(*) AS total_matches
    FROM shootouts
    GROUP BY winner
    ORDER BY COUNT(*) DESC
    LIMIT 10
) q3b

UNION ALL

SELECT '3C - H2H at World Cups' AS query,
    home_team || ' vs ' || away_team AS team,
    total_matches,
    home_wins AS wins,
    draws,
    away_wins AS losses,
    home_win_pct AS win_pct,
    NULL::NUMERIC AS points_pct
FROM (
    SELECT
        LEAST(home_team, away_team) AS home_team,
        GREATEST(home_team, away_team) AS away_team,
        COUNT(*) AS total_matches,
        SUM(CASE
            WHEN home_team < away_team AND home_score > away_score THEN 1
            WHEN home_team > away_team AND away_score > home_score THEN 1
            ELSE 0 END) AS home_wins,
        SUM(CASE WHEN home_score = away_score THEN 1 ELSE 0 END) AS draws,
        SUM(CASE
            WHEN home_team < away_team AND home_score < away_score THEN 1
            WHEN home_team > away_team AND away_score < home_score THEN 1
            ELSE 0 END) AS away_wins,
        ROUND(SUM(CASE
            WHEN home_team < away_team AND home_score > away_score THEN 1.0
            WHEN home_team > away_team AND away_score > home_score THEN 1.0
            ELSE 0 END) * 100 / COUNT(*), 1) AS home_win_pct
    FROM wc_matches
    WHERE home_score IS NOT NULL
    GROUP BY LEAST(home_team, away_team), GREATEST(home_team, away_team)
    HAVING COUNT(*) >= 2
    ORDER BY COUNT(*) DESC
    LIMIT 15
) q3c;


-- ============================================================
-- STEP 4: SQUAD STRENGTH ANALYSIS
-- ============================================================
-- 4A: Total squad market value per national team (top 20)
-- 4B: Average international caps per squad (experience proxy)
-- 4C: Average squad value by confederation
-- ============================================================

-- KEY FINDINGS:
-- Portugal leads squad value at €864.5M; Norway at €504M driven by Haaland
-- CONMEBOL avg squad value (€288.7M) exceeds UEFA (€197.3M) despite 10 vs 51 teams
-- UEFA max (€864.5M Portugal) vs CONMEBOL max (€778.5M Brazil) — UEFA has ceiling
-- Squad experience metric dominated by small nations; WC appearances is better proxy

SELECT '4A - Squad market value' AS query,
    name AS team,
    squad_size AS total_matches,
    NULL::BIGINT AS wins,
    NULL::BIGINT AS draws,
    NULL::BIGINT AS losses,
    ROUND(total_market_value / 1000000, 1) AS win_pct,
    ROUND(total_market_value / squad_size / 1000000, 1) AS points_pct
FROM (
    SELECT name, squad_size, total_market_value
    FROM national_teams
    WHERE total_market_value IS NOT NULL
    ORDER BY total_market_value DESC
    LIMIT 20
) q4a

UNION ALL

SELECT '4B - Squad experience' AS query,
    team,
    total_matches,
    NULL::BIGINT AS wins,
    NULL::BIGINT AS draws,
    NULL::BIGINT AS losses,
    win_pct,
    points_pct
FROM (
    SELECT
        country_of_citizenship AS team,
        COUNT(*) AS total_matches,
        ROUND(AVG(international_caps), 1) AS win_pct,
        ROUND(AVG(international_goals), 1) AS points_pct
    FROM players
    WHERE international_caps IS NOT NULL
      AND country_of_citizenship IS NOT NULL
      AND international_caps > 0
    GROUP BY country_of_citizenship
    HAVING COUNT(*) >= 10
    ORDER BY AVG(international_caps) DESC
    LIMIT 15
) q4b

UNION ALL

SELECT '4C - Confederation strength' AS query,
    confederation AS team,
    COUNT(*) AS total_matches,
    NULL::BIGINT AS wins,
    NULL::BIGINT AS draws,
    NULL::BIGINT AS losses,
    ROUND(AVG(total_market_value) / 1000000, 1) AS win_pct,
    ROUND(MAX(total_market_value) / 1000000, 1) AS points_pct
FROM national_teams
WHERE total_market_value IS NOT NULL
  AND confederation IS NOT NULL
GROUP BY confederation;


-- ============================================================
-- STEP 5: RECENT FORM & CURRENT MOMENTUM
-- ============================================================
-- 5A: Win % across last 50 matches per team (top 20 FIFA nations)
-- ============================================================

-- KEY FINDINGS:
-- Argentina leads all FIFA nations at 71% win rate in last 50 matches
-- Elite nations cluster tightly: France, Portugal, Iran, Algeria all at 65%
-- Spain, England, Brazil all within 3% of each other (62-62-62)
-- Non-FIFA micronations (Jersey, Guernsey, Padania) filtered in post-processing

SELECT '5A - Recent form' AS query,
    team,
    total_matches,
    wins,
    draws,
    losses,
    win_pct,
    NULL::NUMERIC AS points_pct
FROM (
    SELECT
        team,
        COUNT(*) AS total_matches,
        SUM(CASE WHEN result = 'win'  THEN 1 ELSE 0 END) AS wins,
        SUM(CASE WHEN result = 'draw' THEN 1 ELSE 0 END) AS draws,
        SUM(CASE WHEN result = 'loss' THEN 1 ELSE 0 END) AS losses,
        ROUND(SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS win_pct
    FROM (
        SELECT team, result FROM (
            SELECT home_team AS team,
                CASE WHEN home_score > away_score THEN 'win'
                     WHEN home_score = away_score THEN 'draw'
                     ELSE 'loss' END AS result,
                ROW_NUMBER() OVER (PARTITION BY home_team ORDER BY date DESC) AS rn
            FROM matches WHERE home_score IS NOT NULL
            UNION ALL
            SELECT away_team AS team,
                CASE WHEN away_score > home_score THEN 'win'
                     WHEN away_score = home_score THEN 'draw'
                     ELSE 'loss' END AS result,
                ROW_NUMBER() OVER (PARTITION BY away_team ORDER BY date DESC) AS rn
            FROM matches WHERE away_score IS NOT NULL
        ) ranked
        WHERE rn <= 50
    ) recent
    GROUP BY team
    HAVING COUNT(*) >= 20
    ORDER BY win_pct DESC
    LIMIT 20
) q5a;