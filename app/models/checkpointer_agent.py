import os
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import ConnectionPool, AsyncConnectionPool

from dotenv import load_dotenv

load_dotenv()

DB_URI = os.getenv("SQLALCHEMY_DATABASE_URL")

connection_kwargs = {
    "autocommit": True,
    "prepare_threshold": 0,
}

# async postgres database checkpointer persistance connecion

async_pool = AsyncConnectionPool(DB_URI, kwargs=connection_kwargs)

async_checkpointer = AsyncPostgresSaver(async_pool)

# sync postgres database checkpointer persistance connecion

pool = ConnectionPool(
    conninfo=DB_URI,
    max_size=20,
    kwargs=connection_kwargs,
)
checkpointer = PostgresSaver(pool)

checkpointer.setup()