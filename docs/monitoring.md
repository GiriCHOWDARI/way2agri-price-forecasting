# Model monitoring and update plan

1. **Data quality:** required columns, valid dates, positive prices, duplicate months, missing
   months, schema changes and freshness.
2. **Service health:** uptime, latency, error rates, request counts and dependency failures.
3. **Forecast quality:** once actual outcomes arrive, calculate MAE, RMSE, MAPE (where appropriate),
   and mean error/bias by horizon and market/commodity.
4. **Drift:** track changes in price distribution, level, variance, and forecast residuals. A
   distribution shift is a signal to investigate, not proof of model failure by itself.
5. **Retraining:** run a scheduled candidate evaluation; compare against naive and drift baselines
   with rolling-origin validation. Promote only if acceptance criteria are met.
6. **Governance:** log model version, training-data cutoff, forecast timestamp and input-data version.
   Keep human review for procurement actions.
7. **Business KPIs:** adjusted procurement cost, stockout rate, wastage, holding cost and emergency
   purchases; compare against a baseline or control where feasible.
