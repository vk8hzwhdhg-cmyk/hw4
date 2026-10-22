"""
Campus Customs API: products, images, accounts and the Bulldog chat agent.

Run from the backend/ folder:
    source .venv/bin/activate
    uvicorn main:app --reload --port 8000
"""
import logging
import subprocess
import sys
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic_ai.exceptions import ModelHTTPError, UsageLimitExceeded

import audit
import auth
import memory
import store
import tools
from agent import run_chat
from privacy import redact
from models import (AccountSummary, CartQuote, CartQuoteRequest, ChatHistory, ChatRequest, ChatResponse,
                    ProductDetail, ProductSummary, RestockAlert, RestockRequest, Shopper)

log = logging.getLogger("uvicorn.error")

@asynccontextmanager
async def lifespan(_: FastAPI):
    # Chat retention: delete any shopper's history whose 30-day clock has run out.
    memory.ensure_schema()
    store.ensure_schema()
    removed = memory.purge_expired()
    log.info("chat retention: removed %s message(s) from histories older than %s days",
             removed, memory.RETENTION_DAYS)
    yield


app = FastAPI(title="Campus Customs API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173",
                   "http://localhost:5174", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError):
    # Return only friendly messages. The default response echoes the submitted
    # input back, which would include passwords.
    messages = [e["msg"].removeprefix("Value error, ") for e in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": " ".join(dict.fromkeys(messages))})


# The data pack (data/campus_customs.db + data/products/) is not in the GitHub repo.
# On first run, build the cleaned database from it automatically; if the pack is
# missing, stop with clear instructions instead of a confusing error.
_ORIGINAL_DB = tools.DATA / "campus_customs.db"
_missing = [str(p.relative_to(tools.ROOT)) for p in (_ORIGINAL_DB, tools.DATA / "products") if not p.exists()]
if _missing and not tools.DB_PATH.exists():
    raise SystemExit(
        f"Campus Customs data pack not found: {', '.join(_missing)}.\n"
        "Place campus_customs.db and the products/ image folder in data/ (see README.md).")
if not tools.DB_PATH.exists():
    log.info("first run: building %s from the data pack", tools.DB_PATH.name)
    subprocess.run([sys.executable, str(tools.ROOT / "scripts" / "clean_db.py")], check=True)

# Product photos: /media/products/<file>.jpg (matches image_file_path in the DB).
# Mount only the products folder so the .db files are never downloadable.
app.mount("/media/products", StaticFiles(directory=tools.DATA / "products"), name="media")

auth.init(tools.db_rw)
app.include_router(auth.router)


@app.get("/api/health")
def health():
    return {"ok": True, "database": tools.DB_PATH.name}


@app.get("/api/categories")
def categories() -> list[dict]:
    return tools.list_categories()


@app.get("/api/collections")
def collections() -> list[dict]:
    return tools.list_collections()


@app.get("/api/products", response_model=list[ProductSummary])
def list_products(category: Optional[str] = None, q: Optional[str] = None,
                  collection: Optional[str] = None):
    return tools.find_products(q=q, category=category, collection=collection)


@app.get("/api/products/{product_id}", response_model=ProductDetail)
def get_product(product_id: str):
    detail = tools.product_detail(product_id)
    if detail is None:
        raise HTTPException(404, "Product not found")
    return detail


@app.get("/api/chat/history", response_model=ChatHistory)
def chat_history(user: auth.User = Depends(auth.require_user)):
    """The logged-in shopper's saved chat (401 for guests)."""
    return ChatHistory(messages=memory.load_history(user.id))


@app.delete("/api/chat/history", status_code=204)
def clear_chat_history(user: auth.User = Depends(auth.require_user)):
    memory.clear_history(user.id)


@app.get("/api/size-guide")
def size_guide():
    return store.SIZE_GUIDE


@app.post("/api/cart/quote", response_model=CartQuote)
def cart_quote(req: CartQuoteRequest, user: Optional[auth.User] = Depends(auth.current_user)):
    """Price a cart from the database. The browser only sends ids, sizes, quantities and a code."""
    return store.quote_cart(req.items, req.discount_code, user.id if user else None)


@app.post("/api/restock-alerts", response_model=RestockAlert, status_code=201)
def create_restock_alert(req: RestockRequest, user: Optional[auth.User] = Depends(auth.current_user)):
    # Logged in: always use the account email (ignore any email in the body).
    email = user.email if user else (req.email or "").strip().lower()
    if not auth.EMAIL_RE.match(email):
        raise HTTPException(422, "Please enter a valid email address.")
    alert, message = store.create_restock_alert(req.product_id, req.size, email, user.id if user else None)
    if alert is None:
        raise HTTPException(409 if "in stock" in message else 404, message)
    return alert


@app.get("/api/restock-alerts", response_model=list[RestockAlert])
def list_restock_alerts(user: auth.User = Depends(auth.require_user)):
    return store.my_restock_alerts(user.id, user.email)


@app.delete("/api/restock-alerts/{alert_id}", status_code=204)
def delete_restock_alert(alert_id: int, user: auth.User = Depends(auth.require_user)):
    if not store.delete_restock_alert(alert_id, user.id, user.email):
        raise HTTPException(404, "Alert not found.")


@app.get("/api/account", response_model=AccountSummary)
def account(user: auth.User = Depends(auth.require_user)):
    with tools.db_rw() as con:
        created = con.execute("SELECT created_at FROM users WHERE id = ?", (user.id,)).fetchone()[0]
    return AccountSummary(first_name=user.first_name, last_name=user.last_name, email=user.email,
                          member_since=created, saved_messages=memory.count_messages(user.id),
                          restock_alerts=store.my_restock_alerts(user.id, user.email),
                          discount=store.latest_code(user.id))


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request, user: Optional[auth.User] = Depends(auth.current_user)):
    # Rate limit: 20 messages a minute per visitor (account if logged in, else IP address).
    visitor = f"user:{user.id}" if user else f"ip:{request.client.host if request.client else 'unknown'}"
    wait = store.chat_rate_limited(visitor)
    if wait:
        log.warning("chat rate limit hit for a visitor")
        audit.Run(f"user:{user.id}" if user else "guest", req.page.path if req.page else None,
                  redact(req.message)[0], []).end("rate_limited", model_called=False, retry_after_s=wait)
        raise HTTPException(429, f"You're sending messages too quickly. Please wait {wait} seconds and try again.")
    # Identity comes only from the session cookie, never from the request body.
    shopper = Shopper(user.id, user.first_name, user.last_name, user.email) if user else None
    try:
        return await run_chat(req, shopper=shopper)
    except UsageLimitExceeded:
        # The agent loop hit its limit (too many lookups or tokens for one turn).
        log.warning("chat stopped by agent loop limit")
        return ChatResponse(reply="That one needed more lookups than I can do at once. "
                                  "Could you ask about one item or one size at a time?")
    except ModelHTTPError as e:
        if "content_filter" in str(e.body):
            # The model provider's safety filter blocked the message.
            log.warning("chat message blocked by provider content filter")
            safe, redacted = redact(req.message)
            return ChatResponse(reply="I can only help with Campus Customs products and the shop. "
                                      "What Yale gear can I help you find?",
                                redacted=redacted, safe_message=safe if redacted else None)
        log.exception("chat failed")
        return ChatResponse(reply="Sorry, Bulldog is having trouble right now. "
                                  "Please try again in a moment.")
    except Exception:
        log.exception("chat failed")
        return ChatResponse(reply="Sorry, Bulldog is having trouble right now. "
                                  "Please try again in a moment.")
