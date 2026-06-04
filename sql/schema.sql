
-- ============================================================
-- S&OP DATABASE SCHEMA
-- ============================================================
CREATE TABLE demand_actuals (
    record_id      SERIAL PRIMARY KEY,
    date           DATE NOT NULL,
    sku_id         VARCHAR(10) NOT NULL,
    category       VARCHAR(50),
    demand         INTEGER,
    lead_time      INTEGER,
    unit_cost      DECIMAL(10,2),
    holding_cost   DECIMAL(10,2),
    order_cost     DECIMAL(10,2)
);

CREATE TABLE inventory_parameters (
    sku_id                      VARCHAR(10) PRIMARY KEY,
    avg_daily_demand            DECIMAL(10,2),
    safety_stock_units          INTEGER,
    reorder_point_optimised     INTEGER,
    reorder_point_current       INTEGER,
    eoq_units                   INTEGER,
    inventory_turnover          DECIMAL(5,2),
    stockout_prob_current_pct   DECIMAL(5,2),
    stockout_prob_optimised_pct DECIMAL(5,2)
);

CREATE TABLE demand_forecast (
    forecast_id    SERIAL PRIMARY KEY,
    date           DATE NOT NULL,
    sku_id         VARCHAR(10) NOT NULL,
    forecast_demand DECIMAL(10,2),
    model_used     VARCHAR(50)
);

-- ============================================================
-- KEY ANALYTICAL QUERIES
-- ============================================================

-- Q1: Top 10 SKUs by stockout risk reduction after optimisation
SELECT sku_id,
       stockout_prob_current_pct,
       stockout_prob_optimised_pct,
       ROUND((stockout_prob_current_pct - stockout_prob_optimised_pct) /
             NULLIF(stockout_prob_current_pct,0) * 100, 2) AS reduction_pct
FROM inventory_parameters
ORDER BY reduction_pct DESC
LIMIT 10;

-- Q2: Weekly demand trend by category (last 12 weeks)
SELECT DATE_TRUNC('week', date)  AS week_start,
       category,
       SUM(demand)               AS total_demand,
       AVG(demand)               AS avg_daily_demand,
       STDDEV(demand)            AS demand_volatility
FROM demand_actuals
WHERE date >= CURRENT_DATE - INTERVAL '12 weeks'
GROUP BY 1, 2
ORDER BY 1, 2;
