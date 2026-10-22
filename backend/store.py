"""
Shop features around the catalogue: cart pricing, restock alerts, account
summary, size guide and chat rate limiting.

- Cart: the browser keeps the cart; quote_cart() re-reads every price and stock
  level from the database, so totals are always honest.
- Restock alerts: saved in `restock_requests`. No email is sent automatically
  in this project; the shop can export the list when stock arrives.
- Chat rate limit: 20 messages per minute per visitor (in memory).
- Boola Boola codes: saying "Boola Boola" in the chat gives a logged-in shopper
  one discount code (Boola + 4 random digits) per 365 days, valid for 7 days,
  applied in the cart. Codes are created only here, never by the AI.
"""
import json
import re
import secrets
import time
from datetime import datetime, timedelta, timezone
from collections import defaultdict, deque
from pathlib import Path
from typing import Optional

from models import AppliedDiscount, CartItemIn, CartLine, CartQuote, DiscountInfo, RestockAlert
from tools import SIZE_ORDER, db_rw, normalize_size, product_detail

SIZE_GUIDE = json.loads((Path(__file__).parent / "size_guide.json").read_text())
MAX_QTY_PER_LINE = 10


def ensure_schema() -> None:
    with db_rw() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS restock_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT NOT NULL REFERENCES catalogue(product_id),
                size TEXT NOT NULL,
                email TEXT NOT NULL,
                user_id INTEGER REFERENCES users(id),
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                notified_at TEXT,
                UNIQUE (product_id, size, email)
            )""")
        con.execute("""
            CREATE TABLE IF NOT EXISTS discount_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                user_id INTEGER NOT NULL REFERENCES users(id),
                percent_off INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                expires_at TEXT NOT NULL,
                redeemed_at TEXT
            )""")


# ---- cart ------------------------------------------------------------------------

def quote_cart(items: list[CartItemIn], discount_code: Optional[str] = None,
               user_id: Optional[int] = None) -> CartQuote:
    lines, subtotal, count = [], 0.0, 0
    for item in items:
        detail = product_detail(item.product_id)
        size = normalize_size(item.size) or item.size
        if detail is None:
            lines.append(CartLine(product_id=item.product_id, size=item.size, quantity=0,
                                  requested=item.quantity, status="unavailable",
                                  message="This product is no longer available."))
            continue
        stock = next((s.quantity for s in detail.sizes if s.size == size), 0)
        qty = min(item.quantity, stock, MAX_QTY_PER_LINE)
        if stock == 0:
            status, msg = "sold_out", f"Sold out in {size}."
        elif qty < item.quantity:
            status, msg = "limited", f"Only {qty} available in {size}."
        else:
            status, msg = "ok", None
        line_total = round(detail.price * qty, 2)
        subtotal += line_total
        count += qty
        lines.append(CartLine(product_id=detail.product_id, name=detail.name, size=size,
                              price=detail.price, image_url=detail.image_url, quantity=qty,
                              requested=item.quantity, available=stock, line_total=line_total,
                              status=status, message=msg))
    subtotal = round(subtotal, 2)
    discount, error = None, None
    if discount_code and discount_code.strip():
        discount, error = _apply_code(discount_code, user_id, subtotal)
    total = round(subtotal - (discount.amount if discount else 0), 2)
    return CartQuote(lines=lines, item_count=count, subtotal=subtotal, discount=discount,
                     discount_error=error, total=total)


# ---- Boola Boola discount codes ------------------------------------------------------

DISCOUNT_PERCENT = 10
CODE_VALID_DAYS = 7
CODE_EVERY_DAYS = 365
_BOOLA = re.compile(r"\bboola[\W_]*boola\b", re.IGNORECASE)


def mentions_boola(text: str) -> bool:
    return bool(_BOOLA.search(text))


def without_boola(text: str) -> str:
    return _BOOLA.sub(" ", text).strip(" \t\n!.,?;:-")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _fmt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _parse(ts: str) -> datetime:
    return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)


def _pretty_dt(dt: datetime) -> str:
    return f"{dt:%b} {dt.day}, {dt.year}"


def _pretty(ts: str) -> str:
    return _pretty_dt(_parse(ts))


def _info(row) -> DiscountInfo:
    status = ("redeemed" if row["redeemed_at"] else
              "expired" if _parse(row["expires_at"]) <= _now() else "active")
    return DiscountInfo(code=row["code"], percent_off=row["percent_off"], issued_at=row["created_at"],
                        expires_at=row["expires_at"], status=status)


def latest_code(user_id: int) -> Optional[DiscountInfo]:
    """The shopper's code from the last 365 days, if any."""
    with db_rw() as con:
        row = con.execute("SELECT * FROM discount_codes WHERE user_id = ? AND created_at > ? "
                          "ORDER BY id DESC LIMIT 1",
                          (user_id, _fmt(_now() - timedelta(days=CODE_EVERY_DAYS)))).fetchone()
    return _info(row) if row else None


def boola_message(user_id: Optional[int]) -> str:
    """Bulldog's reply to "Boola Boola". Issues a new code when the shopper is eligible."""
    if user_id is None:
        return ("**Boola Boola!** 🐶 That's the spirit! **Log in or create an account** and say it "
                "again to unlock a one-time Bulldog discount code (one per account each year).")
    existing = latest_code(user_id)
    if existing and existing.status == "active":
        return (f"**Boola Boola!** You already have code **{existing.code}** "
                f"({existing.percent_off}% off), good until **{_pretty(existing.expires_at)}**. "
                "Enter it in your **Cart** under *Discount code*.")
    if existing:
        next_date = _parse(existing.issued_at) + timedelta(days=CODE_EVERY_DAYS)
        return (f"**Boola Boola!** You've already received your Bulldog code this year "
                f"(on {_pretty(existing.issued_at)}). You can unlock a new one after "
                f"**{_pretty_dt(next_date)}**.")
    expires = _fmt(_now() + timedelta(days=CODE_VALID_DAYS))
    with db_rw() as con:
        for _ in range(50):  # pick an unused Boola#### code
            code = f"Boola{secrets.randbelow(10000):04d}"
            if not con.execute("SELECT 1 FROM discount_codes WHERE code = ?", (code,)).fetchone():
                break
        else:
            return "**Boola Boola!** Our code machine is busy right now. Please try again later."
        con.execute("INSERT INTO discount_codes (code, user_id, percent_off, expires_at) VALUES (?, ?, ?, ?)",
                    (code, user_id, DISCOUNT_PERCENT, expires))
    return (f"**Boola Boola!** 🎉 Here's your one-time Bulldog code: **{code}**. It's "
            f"**{DISCOUNT_PERCENT}% off** your merch and expires in {CODE_VALID_DAYS} days "
            f"(**{_pretty(expires)}**). Enter it in your **Cart** under *Discount code*. "
            "One code per account each year.")


def _apply_code(raw: str, user_id: Optional[int], subtotal: float) -> tuple[Optional[AppliedDiscount], Optional[str]]:
    digits = re.sub(r"(?i)^\s*boola\s*", "", raw.strip())
    if not re.fullmatch(r"\d{4}", digits):
        return None, "Discount codes look like Boola1234."
    if user_id is None:
        return None, "Log in to use your Bulldog discount code."
    with db_rw() as con:
        row = con.execute("SELECT * FROM discount_codes WHERE lower(code) = lower(?) AND user_id = ?",
                          (f"Boola{digits}", user_id)).fetchone()
    if row is None:
        return None, "That code isn't valid for your account."
    info = _info(row)
    if info.status == "expired":
        return None, f"Code {info.code} expired on {_pretty(info.expires_at)}."
    if info.status == "redeemed":
        return None, f"Code {info.code} has already been used."
    amount = round(subtotal * info.percent_off / 100, 2)
    return AppliedDiscount(code=info.code, percent_off=info.percent_off, amount=amount,
                           expires_at=info.expires_at), None


# ---- restock alerts --------------------------------------------------------------------

def create_restock_alert(product_id: str, size: str, email: str,
                         user_id: Optional[int]) -> tuple[Optional[RestockAlert], str]:
    """Returns (alert, message). Only sold-out sizes can get an alert."""
    detail = product_detail(product_id)
    size_n = normalize_size(size)
    if detail is None:
        return None, "We couldn't find that product."
    if size_n is None:
        return None, f"We carry sizes {', '.join(SIZE_ORDER)}."
    stock = next((s.quantity for s in detail.sizes if s.size == size_n), 0)
    if stock > 0:
        return None, f"Good news: {detail.name} is in stock in {size_n}, so you can order it now."
    with db_rw() as con:
        con.execute("INSERT OR IGNORE INTO restock_requests (product_id, size, email, user_id) "
                    "VALUES (?, ?, ?, ?)", (detail.product_id, size_n, email.lower(), user_id))
        row = con.execute("SELECT * FROM restock_requests WHERE product_id = ? AND size = ? AND email = ?",
                          (detail.product_id, size_n, email.lower())).fetchone()
    return _alert(row, detail.name), f"We'll email you when {detail.name} is back in {size_n}."


def _alert(row, name: Optional[str] = None) -> RestockAlert:
    if name is None:
        d = product_detail(row["product_id"])
        name = d.name if d else row["product_id"]
    return RestockAlert(id=row["id"], product_id=row["product_id"], product_name=name,
                        size=row["size"], created_at=row["created_at"])


def my_restock_alerts(user_id: int, email: str) -> list[RestockAlert]:
    with db_rw() as con:
        rows = con.execute("SELECT * FROM restock_requests WHERE (user_id = ? OR email = ?) "
                           "AND notified_at IS NULL ORDER BY id DESC", (user_id, email.lower())).fetchall()
    return [_alert(r) for r in rows]


def delete_restock_alert(alert_id: int, user_id: int, email: str) -> bool:
    with db_rw() as con:
        return con.execute("DELETE FROM restock_requests WHERE id = ? AND (user_id = ? OR email = ?)",
                           (alert_id, user_id, email.lower())).rowcount > 0


# ---- size guide ---------------------------------------------------------------------------

def size_chart_for(category: str) -> Optional[dict]:
    return next((c for c in SIZE_GUIDE["charts"].values() if category in c["applies_to"]), None)


# ---- chat rate limit ---------------------------------------------------------------------

CHAT_LIMIT_PER_MINUTE = 20
_chat_hits: dict[str, deque] = defaultdict(deque)


def chat_rate_limited(visitor: str) -> Optional[int]:
    """Record a chat message for this visitor; return seconds to wait if over the limit."""
    now = time.monotonic()
    hits = _chat_hits[visitor]
    while hits and now - hits[0] >= 60:
        hits.popleft()
    if len(hits) >= CHAT_LIMIT_PER_MINUTE:
        return int(60 - (now - hits[0])) + 1
    hits.append(now)
    return None
