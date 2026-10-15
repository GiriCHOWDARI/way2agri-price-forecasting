# Model training and evaluation

## Available models
The API compares four candidates: Naive baseline, Drift, Holt damped trend, and Holt-Winters additive seasonality. It uses expanding-window rolling-origin validation, forecasting 12 months ahead for each validation window by default. Metrics are mean MAE, RMSE, and MAPE; the selected candidate minimizes mean MAE. This is a prototype selection rule and should be approved against a business-defined acceptance threshold.

## Run evaluation
- Dashboard: click **Run model evaluation**.
- API: `POST /train-evaluate?windows=4&horizon=12`.
- The API writes `backend/data/active_model.json`, containing the selected model, validation setup, dataset fingerprint context (observation count and last date), and candidate metrics.
- `GET /forecast?horizon=12` then uses the selected model. If fitting fails, it safely falls back to a naive forecast.

The evaluation needs enough monthly history to preserve an initial training period plus the requested validation windows. If the current dataset is stale, refresh it first. Re-evaluate after each verified data refresh; do not assume retraining automatically improves accuracy.

## Guardrails
- Candidate selection is based only on past-to-future chronological splits, never random splits.
- MAPE can be misleading when actual values are near zero; the current validator requires positive prices and reports MAE/RMSE alongside MAPE.
- No prediction intervals, independent holdout approval, authentication, or multi-user model registry are implemented yet.
- Before production, define acceptance thresholds, add a final untouched holdout, version model/data artifacts, and require manual approval for model promotion.


## Side-by-side forecast comparison

`GET /forecast?horizon=12` now returns both the selected model's `forecast` and a
`forecast_comparison` array for Naive baseline, Drift, Holt damped trend, and
Holt-Winters additive. The dashboard displays these predictions side by side for
each forecast month, so users can see why the Naive baseline is flat while trend
and seasonal models may vary.

The model selected by rolling-origin validation remains the primary forecast; the
comparison table does not automatically force a model with changing values to win.
The sample dataset ends in September 2025, so its forecast dates are historical
relative to October 2026. Upload a current, verified monthly dataset and rerun
model evaluation before using forecasts for decisions.
