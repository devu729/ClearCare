"""
ClearCare Backend — FastAPI Application
Agents: Policy Parser, Decision Tracer, Dual Explainer,
        Hallucination Guard, MCP (Email + Calendar), Eval Suite, Audit Log
AI: Google Gemini (free) + sentence-transformers (local)
"""

import logging
import time
import asyncio
import os
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from config import get_settings
from routers.policy_router import router as policy_router
from routers.trace_router  import router as trace_router
from routers.mcp_router    import router as mcp_router
from routers.audit_router  import router as audit_router
from routers.eval_router   import router as eval_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger   = logging.getLogger(__name__)
settings = get_settings()


# ── Keep-alive pinger ─────────────────────────────────────────────────────────
# Render free tier sleeps after 15 min of no traffic.
# This pings /health every 10 min so the server stays awake.
# Set RENDER_EXTERNAL_URL in Render environment variables.
# (Render provides this automatically — just add it to your env vars)

async def keep_alive():
    """Ping self every 10 minutes — prevents Render cold starts."""
    await asyncio.sleep(60)  # Wait 1 min after startup
    while True:
        try:
            url = os.getenv("RENDER_EXTERNAL_URL", "")
            if url:
                async with httpx.AsyncClient(timeout=10) as client:
                    resp = await client.get(f"{url}/health")
                    logger.info(f"Keep-alive ping → {resp.status_code}")
            else:
                logger.debug("RENDER_EXTERNAL_URL not set — skipping (local dev is fine)")
        except Exception as e:
            logger.warning(f"Keep-alive ping failed (non-critical): {e}")
        await asyncio.sleep(600)  # 10 minutes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs on startup and shutdown."""
    asyncio.create_task(keep_alive())
    logger.info("ClearCare started ✓ keep-alive pinger active")
    yield
    logger.info("ClearCare shutting down")


# ── FastAPI App ───────────────────────────────────────────────────────────────
app = FastAPI(
    title       = "ClearCare API",
    version     = "1.0.0",
    description = "Healthcare Decision Intelligence — Complete Backend",
    lifespan    = lifespan,                                              # ← keep-alive
    docs_url    = "/docs"  if settings.environment == "development" else None,
    redoc_url   = "/redoc" if settings.environment == "development" else None,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins     = settings.origins_list,
    allow_credentials = True,
    allow_methods     = ["GET", "POST", "DELETE"],
    allow_headers     = ["Authorization", "Content-Type"],
)

# ── Security headers on every response ───────────────────────────────────────
@app.middleware("http")
async def security_headers(request: Request, call_next):
    start    = time.time()
    response = await call_next(request)
    response.headers["X-Content-Type-Options"]    = "nosniff"
    response.headers["X-Frame-Options"]           = "DENY"
    response.headers["X-XSS-Protection"]          = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Cache-Control"]             = "no-store"
    response.headers["X-Process-Time"]            = str(round(time.time() - start, 4))
    if "server" in response.headers:
        del response.headers["server"]
    return response

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(policy_router)
app.include_router(trace_router)
app.include_router(mcp_router)
app.include_router(audit_router)
app.include_router(eval_router)

# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {
        "status":  "ok",
        "version": "1.0.0",
        "ai":      "gemini-2.5-flash-lite + sentence-transformers",
        "agents":  ["policy_parser", "decision_tracer", "dual_explainer", "mcp_email", "mcp_calendar"],
    }

# ── Global error handler ──────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again."},
    )