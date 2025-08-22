import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from sqlalchemy.ext.asyncio import create_async_engine, AsyncConnection
from sqlalchemy import text

APP = FastAPI()

PG_HOST = os.getenv("PG_HOST", "pg")
PG_USER = os.getenv("PG_USER", "app")
PG_PASS = os.getenv("PG_PASS", "apppass")
PG_DB = os.getenv("PG_DB", "demopg")

# SQLAlchemy async engine using asyncpg
engine = create_async_engine(
    f"postgresql+asyncpg://{PG_USER}:{PG_PASS}@{PG_HOST}:5432/{PG_DB}",
    pool_pre_ping=True,
)

@APP.get("/health")
async def health():
    try:
        async with engine.connect() as conn:  # type: AsyncConnection
            await conn.execute(text("SELECT 1"))
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@APP.get("/safe")
async def safe(name: str = "", col: str = "name"):
    allowed = {"id", "name", "email", "role"}
    if col not in allowed:
        return JSONResponse({"error": "invalid column"}, status_code=400)
    sql = text(f'SELECT "{col}" AS val FROM users WHERE name = :name')
    try:
        async with engine.connect() as conn:
            result = await conn.execute(sql, {"name": name})
            rows = [dict(r._mapping) for r in result]
        return {"query": str(sql), "rows": rows}
    except Exception as e:
        return JSONResponse({"query": str(sql), "error": str(e)}, status_code=500)

@APP.get("/vuln")
async def vuln(name: str = "", col: str = "name"):
    # VULN: naive identifier interpolation with double quotes
    sanitized = col.replace('"', '""')
    sql = text(f'SELECT "{sanitized}" AS val FROM users WHERE name = :name')
    try:
        async with engine.connect() as conn:
            result = await conn.execute(sql, {"name": name})
            rows = [dict(r._mapping) for r in result]
        return {"query": str(sql), "rows": rows}
    except Exception as e:
        return JSONResponse({"query": str(sql), "error": str(e)}, status_code=500)

if __name__ == "__main__":
    uvicorn.run(APP, host="0.0.0.0", port=5000)


