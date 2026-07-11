# src/utils/db_connector.py

import os
from typing import Dict, Any
from src.utils.user_loader import load_user_portfolio
from src.utils.postgres_db import SessionLocal, UserPosition, DATABASE_URL

class ProductionDatabaseConnection:
    """Orchestrates live SQL rows transactional handling with failover local query stubs."""
    def __init__(self):
        # Failover dynamic checker sets if true postgres connection url variables strings exist
        self.use_real_db = True if (DATABASE_URL and SessionLocal is not None) else False
        
        if self.use_real_db:
            print("[DB SYSTEM ACTIVATED] Successfully routing calculations via real PostgreSQL queries.")
        else:
            print("[TESTING FALLBACK STATE] DATABASE_URL missing or skipped. Running local simulation engines safely.")

    def fetch_user_assets(self, user_id: str) -> Dict[str, Any]:
        # --- PATH A: Real Active PostgreSQL Pipeline Production Layer ---
        if self.use_real_db and SessionLocal:
            db = SessionLocal()
            try:
                records = db.query(UserPosition).filter(UserPosition.user_id == user_id).all()
                positions = []
                for item in records:
                    positions.append({
                        "ticker": item.ticker,
                        "shares": item.shares,
                        "cost_basis": item.cost_basis
                    })
                return {"user_id": user_id, "positions": positions}
            except Exception as e:
                print(f"[POSTGRES FETCH FAILED] Falling back to filesystem files stubs check: {e}")
            finally:
                db.close()
                
        # --- PATH B: Temporary Testing Sandbox Local Storage Loader Failover ---
        try:
            fallback_portfolio = load_user_portfolio(user_id)
            if fallback_portfolio:
                return fallback_portfolio
        except Exception:
            pass
            
        return {"user_id": user_id, "positions": []}

db_engine = ProductionDatabaseConnection()