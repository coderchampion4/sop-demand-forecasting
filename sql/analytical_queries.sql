
-- Q3: Inventory turnover ranking by category
SELECT p.category,
       COUNT(DISTINCT p.sku_id)        AS sku_count,
       ROUND(AVG(p.inventory_turnover),2) AS avg_turnover,
       ROUND(AVG(p.safety_stock_units),0) AS avg_safety_stock,
       ROUND(AVG(p.stockout_prob_optimised_pct),2) AS avg_stockout_risk_pct
FROM inventory_parameters p
JOIN demand_actuals d USING (sku_id)
GROUP BY p.category
ORDER BY avg_turnover DESC;

-- Q4: Forecast vs actual accuracy (last 30 days)
WITH actuals AS (
    SELECT date, sku_id, SUM(demand) AS actual_demand
    FROM demand_actuals
    WHERE date >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY 1, 2
)
SELECT f.sku_id,
       ROUND(AVG(ABS(a.actual_demand - f.forecast_demand) /
             NULLIF(a.actual_demand,0)) * 100, 2) AS mape_pct,
       ROUND(AVG(ABS(a.actual_demand - f.forecast_demand)),2) AS mae
FROM demand_forecast f
JOIN actuals a USING (date, sku_id)
GROUP BY f.sku_id
ORDER BY mape_pct ASC;

-- Q5: S&OP Planning view – combined KPI snapshot
SELECT d.category,
       SUM(d.demand)                     AS total_demand_ytd,
       ROUND(AVG(p.safety_stock_units),0) AS avg_safety_stock,
       ROUND(AVG(p.inventory_turnover),2)  AS avg_inv_turnover,
       ROUND(AVG(p.stockout_prob_optimised_pct),2) AS avg_stockout_risk_pct,
       COUNT(CASE WHEN p.stockout_prob_optimised_pct > 5 THEN 1 END) AS high_risk_skus
FROM demand_actuals d
JOIN inventory_parameters p USING (sku_id)
GROUP BY d.category
ORDER BY avg_stockout_risk_pct DESC;
