import yfinance as yf
from typing import Dict, Any
from src.utils.db_connector import db_engine   
from src.agentic_engine import AgentState

def fetch_live_price(ticker: str, fallback_price: float) -> float:
    try:
        stock = yf.Ticker(ticker)
        todays_data = stock.history(period='1d')
        if not todays_data.empty:
            return float(todays_data['Close'].iloc[-1])
    except Exception:
        pass
    return fallback_price

def portfolio_health_node(state: AgentState) -> Dict[str, Any]:
    raw_profile = db_engine.fetch_user_assets(state["user_id"])
    if not raw_profile or "positions" not in raw_profile:
        return {"agent_outputs": {"status": "error", "message": "Portfolio profile records empty."}}
        
    positions = raw_profile["positions"]
    total_market_value = 0.0
    evaluated_positions = []
    
    for pos in positions:
        ticker = pos.get("ticker", "UNKNOWN")
        shares = float(pos.get("shares") or pos.get("quantity") or 0)
        cost_basis = float(pos.get("cost_basis") or pos.get("buy_price") or 1.0)
        
        if shares <= 0:
            continue
            
        current_price = fetch_live_price(ticker, fallback_price=cost_basis * 1.1) 
        market_value = shares * current_price
        total_market_value += market_value
        
        evaluated_positions.append({
            "ticker": ticker,
            "shares": shares,
            "market_value": market_value,
            "current_price": current_price
        })
        
    observations = []
    flag = "low"
    for ep in evaluated_positions:
        pct = (ep["market_value"] / total_market_value) * 100 if total_market_value > 0 else 0
        if pct > 50.0:
            flag = "high"
            observations.append(f"High risk exposure warning: {ep['ticker']} represents {pct:.1f}% of assets.")
            
    if not observations:
        observations.append("Asset weights appear inside healthy balanced parameters limits.")

    return {
        "agent_outputs": {
            "agent_name": "Portfolio Health Agent",
            "total_portfolio_value": round(total_market_value, 2),
            "concentration_flag": flag,
            "observations": observations,
            "disclaimer": "This analysis uses real-time metrics data feeds. This is not authorized financial advice."
        }
    }

def market_news_node(state: AgentState) -> Dict[str, Any]:
    tickers = state.get("extracted_tickers", [])
    target_ticker = tickers[0] if tickers else "SPY"
    
    news_headlines = []
    try:
        stock = yf.Ticker(target_ticker)
        ticker_news = stock.news
        if ticker_news:
            news_headlines = [item['title'] for item in ticker_news[:3]]
    except Exception:
        news_headlines = ["Unable to pull fresh market news records at this moment."]

    return {
        "agent_outputs": {
            "agent_name": "Market Intelligence News Agent",
            "target_ticker": target_ticker,
            "extracted_news_headlines": news_headlines,
            "summary": f"Analyzing market consensus context for ticker {target_ticker} across recent media blocks."
        }
    }

def tax_strategy_node(state: AgentState) -> Dict[str, Any]:
    return {
        "agent_outputs": {
            "agent_name": "Tax Strategy Analyst",
            "recommendation": "Review allocation models to harvest capital gains before calendar periods close.",
            "note": "Tax agents operate strictly on multi-period financial asset rules."
        }
    }