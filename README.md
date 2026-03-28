# 📊 StockIQ — Stock Data Intelligence Dashboard
Internship Assignment | Jarnox

## Features
- Real-time NSE stock data via yfinance (8 companies)
- REST API with FastAPI + SQLite
- Auto-generated Swagger docs at /docs
- Metrics: Daily Return, 7D Moving Average, Volatility Score, Correlation
- Dashboard: Price chart, Gainers/Losers, Stock Comparison

## Setup
pip install -r requirements.txt
python fetch_data.py       # fetch & store 1 year of data
uvicorn main:app --reload --port 8000

## API Endpoints
GET /companies
GET /data/{symbol}?days=30
GET /summary/{symbol}
GET /compare?symbol1=TCS&symbol2=INFY
GET /gainers-losers

## Frontend
cd frontend && python -m http.server 5500
Open: http://localhost:5500