# API examples

## Health
`GET http://127.0.0.1:8000/health`

## Recent history
`GET http://127.0.0.1:8000/history?limit=12`

## Forecast
`GET http://127.0.0.1:8000/forecast?horizon=12`

## Model information
`GET http://127.0.0.1:8000/model-info`

The forecast is a naive baseline that repeats the last observed value. No currency symbol is
shown because the dataset does not identify the unit.
