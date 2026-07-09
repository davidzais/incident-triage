import sys
from typing import Any, Generator

from sqlalchemy.ext.asyncio.session import AsyncSession
from db.tables import Base
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from functools import cache
from dotenv import load_dotenv
import os

import asyncio


load_dotenv()



if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def init_db():
    
    engine = get_engine()
    async with engine.begin() as conn:
        #Base.metadata.drop_all()   # dev only — wipes the table
        #await conn.run_sync(Base.metadata.drop_all)
        # metadata.create_all does not have a native async implementation
        await conn.run_sync(Base.metadata.create_all)

async def get_session() -> Generator[AsyncSession, Any, None]:
    async with get_session_maker()() as s:
        yield s

@cache     
def get_session_maker():   
    return async_sessionmaker(get_engine(), expire_on_commit=False)

@cache
def get_engine():
    return create_async_engine(os.environ["DATABASE_URL"])

if __name__ == "__main__":
    asyncio.run(init_db())
   