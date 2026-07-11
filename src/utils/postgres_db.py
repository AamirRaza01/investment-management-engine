import os
from sqlalchemy import create_engine, Column, String, Integer, Float
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = None
SessionLocal = None
Base = declarative_base()

class UserPosition(Base):
    __tablename__ = "user_positions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    ticker = Column(String, index=True, nullable=False)
    shares = Column(Float, nullable=False)
    cost_basis = Column(Float, nullable=False)

if DATABASE_URL:
    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"[DB ENGINE WARNING] Unable to bind target database server: {e}")
        engine = None
        SessionLocal = None