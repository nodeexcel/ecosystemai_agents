from fastapi import Depends
from sqlalchemy.orm import Session
from .model import SessionLocal, AsyncSessionLocal
from contextlib import asynccontextmanager

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@asynccontextmanager
async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session