import yfinance as yf
import pandas as pd
import time                          # ← ADDED
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import StockPrice, Base

COMPANIES = {
    "RELIANCE": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "INFY": "INFY.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "WIPRO": "WIPRO.NS",
    "ICICIBANK": "ICICIBANK.NS",
    "SBIN": "SBIN.NS",
    "BHARTIARTL": "BHARTIARTL.NS",
}

def fetch_and_store():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    end = datetime.today()
    start = end - timedelta(days=365)

    for symbol, ticker in COMPANIES.items():
        print(f"Fetching {symbol}...")
        try:
            df = yf.download(ticker, start=start, end=end, progress=False)
            time.sleep(3)            # ← ADDED: wait 3 sec between each stock

            if df.empty:
                print(f"  No data for {symbol}, skipping.")
                continue

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            df.reset_index(inplace=True)
            df.rename(columns={
                "Date": "date", "Open": "open", "High": "high",
                "Low": "low", "Close": "close", "Volume": "volume"
            }, inplace=True)

            df.dropna(subset=["open", "high", "low", "close"], inplace=True)

            df["daily_return"] = (df["close"] - df["open"]) / df["open"]
            df["ma_7"] = df["close"].rolling(window=7).mean()
            df["volatility"] = df["close"].rolling(window=7).std()

            db.query(StockPrice).filter(StockPrice.symbol == symbol).delete()

            for _, row in df.iterrows():
                record = StockPrice(
                    symbol=symbol,
                    date=row["date"].date() if hasattr(row["date"], "date") else row["date"],
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row["volume"]) if pd.notna(row["volume"]) else 0.0,
                    daily_return=float(row["daily_return"]) if pd.notna(row["daily_return"]) else 0.0,
                    ma_7=float(row["ma_7"]) if pd.notna(row["ma_7"]) else None,
                    volatility=float(row["volatility"]) if pd.notna(row["volatility"]) else None,
                )
                db.add(record)

            db.commit()
            print(f"  ✅ {symbol} saved.")

        except Exception as e:
            print(f"  ❌ Error for {symbol}: {e}")
            db.rollback()

    db.close()
    print("✅ All done!")

if __name__ == "__main__":
    fetch_and_store()