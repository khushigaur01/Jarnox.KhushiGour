from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager          # ← ADDED
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db, engine
from models import StockPrice, Base
from fetch_data import COMPANIES, fetch_and_store   # ← fetch_and_store added
from datetime import date, timedelta
from typing import Optional
import numpy as np

Base.metadata.create_all(bind=engine)

# ── Startup: fetch data when server launches ──────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Server starting — fetching stock data...")
    try:
        fetch_and_store()
    except Exception as e:
        print(f"⚠ Data fetch warning: {e}")
    yield

app = FastAPI(title="Stock Intelligence API", version="1.0", lifespan=lifespan)  # ← lifespan added

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Helper ──────────────────────────────────────────────
def row_to_dict(row: StockPrice):
    return {
        "symbol": row.symbol,
        "date": str(row.date),
        "open": round(row.open, 2),
        "high": round(row.high, 2),
        "low": round(row.low, 2),
        "close": round(row.close, 2),
        "volume": row.volume,
        "daily_return": round(row.daily_return * 100, 4) if row.daily_return else None,
        "ma_7": round(row.ma_7, 2) if row.ma_7 else None,
        "volatility": round(row.volatility, 4) if row.volatility else None,
    }

# ── Endpoints ────────────────────────────────────────────

@app.get("/companies")
def get_companies():
    """Returns all available companies."""
    return {"companies": list(COMPANIES.keys())}


@app.get("/data/{symbol}")
def get_stock_data(symbol: str, days: int = 30, db: Session = Depends(get_db)):
    """Returns last N days of stock data for a symbol."""
    symbol = symbol.upper()
    since = date.today() - timedelta(days=days)
    rows = (
        db.query(StockPrice)
        .filter(StockPrice.symbol == symbol, StockPrice.date >= since)
        .order_by(StockPrice.date)
        .all()
    )
    if not rows:
        raise HTTPException(status_code=404, detail=f"No data found for {symbol}")
    return {"symbol": symbol, "data": [row_to_dict(r) for r in rows]}


@app.get("/summary/{symbol}")
def get_summary(symbol: str, db: Session = Depends(get_db)):
    """Returns 52-week high, low, average close, and volatility score."""
    symbol = symbol.upper()
    since = date.today() - timedelta(days=365)
    rows = db.query(StockPrice).filter(
        StockPrice.symbol == symbol, StockPrice.date >= since
    ).all()

    if not rows:
        raise HTTPException(status_code=404, detail=f"No data for {symbol}")

    closes = [r.close for r in rows]
    returns = [r.daily_return for r in rows if r.daily_return is not None]

    return {
        "symbol": symbol,
        "52_week_high": round(max(r.high for r in rows), 2),
        "52_week_low": round(min(r.low for r in rows), 2),
        "avg_close": round(sum(closes) / len(closes), 2),
        "avg_daily_return_pct": round((sum(returns) / len(returns)) * 100, 4) if returns else None,
        "volatility_score": round(float(np.std(closes)), 4),
        "data_points": len(rows),
    }


@app.get("/compare")
def compare_stocks(symbol1: str, symbol2: str, days: int = 30, db: Session = Depends(get_db)):
    """Compare two stocks' closing price performance."""
    result = {}
    for sym in [symbol1.upper(), symbol2.upper()]:
        since = date.today() - timedelta(days=days)
        rows = (
            db.query(StockPrice)
            .filter(StockPrice.symbol == sym, StockPrice.date >= since)
            .order_by(StockPrice.date)
            .all()
        )
        if not rows:
            raise HTTPException(status_code=404, detail=f"No data for {sym}")

        closes = [r.close for r in rows]
        pct_change = ((closes[-1] - closes[0]) / closes[0]) * 100 if len(closes) > 1 else 0

        result[sym] = {
            "dates": [str(r.date) for r in rows],
            "closes": [round(r.close, 2) for r in rows],
            "pct_change": round(pct_change, 2),
            "start_price": round(closes[0], 2),
            "end_price": round(closes[-1], 2),
        }

    s1 = symbol1.upper()
    s2 = symbol2.upper()
    min_len = min(len(result[s1]["closes"]), len(result[s2]["closes"]))
    c1 = result[s1]["closes"][-min_len:]
    c2 = result[s2]["closes"][-min_len:]
    correlation = float(np.corrcoef(c1, c2)[0, 1]) if min_len > 1 else None
    result["correlation"] = round(correlation, 4) if correlation else None

    return result


@app.get("/gainers-losers")
def top_gainers_losers(db: Session = Depends(get_db)):
    """Returns top gainers and losers based on latest daily return."""
    result = []
    for symbol in COMPANIES:
        row = (
            db.query(StockPrice)
            .filter(StockPrice.symbol == symbol)
            .order_by(StockPrice.date.desc())
            .first()
        )
        if row and row.daily_return is not None:
            result.append({
                "symbol": symbol,
                "daily_return_pct": round(row.daily_return * 100, 2),
                "close": round(row.close, 2)
            })

    result.sort(key=lambda x: x["daily_return_pct"], reverse=True)
    return {
        "gainers": result[:3],
        "losers": result[-3:][::-1],
    }
```

---

## Now Do These 3 Things:

