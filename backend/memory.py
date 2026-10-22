"""
Chat memory for logged-in shoppers, stored in the existing `chat_messages` table.

    chat_messages(id, user_id → users.id, role 'user'|'assistant', content,
                  products_json, created_at, is_sample)

products_json (assistant rows only) stores which products were shown, not
their prices: {"product_ids": [...], "results_title": "..."}. Older course rows
stored full product snapshots as a list; both formats are read. Product cards
are always rebuilt from the database on load, so prices and stock are current.

Retention: each shopper's saved history lives for up to RETENTION_DAYS (30)
days. The 30-day clock starts with the first message saved after their last
Clear (or their first chat ever). When the clock runs out, the whole history
is deleted, and the next message starts a new 30-day clock. Clearing deletes
everything immediately, which also restarts the clock.

purge_expired() enforces this at startup, before each save, and before each
load, so expired history is never shown or sent to the agent.

Cap: at most MAX_SAVED_MESSAGES (200) real messages per shopper; when a new
exchange pushes past it, the oldest are deleted.

Sample rows (is_sample = 1) are the 22 course example messages kept for
learning. They are exempt from expiry and don't start a shopper's clock, but
a shopper's own Clear still deletes them.

Every function takes the user_id from the login session; callers never pass
one from the request, so a shopper can only read or delete their own history.
"""
import json
from typing import Optional

from models import ChatTurn, HistoryMessage
from tools import db_rw, product_cards

HISTORY_LIMIT = 50  # messages returned to the website on load
RETENTION_DAYS = 30
MAX_SAVED_MESSAGES = 200  # per shopper; the oldest are removed beyond this
_CUTOFF = f"datetime('now', '-{RETENTION_DAYS} days')"

# Shoppers whose 30-day clock (oldest non-sample message) has run out.
_EXPIRED_USERS = f"""
    SELECT user_id FROM chat_messages WHERE is_sample = 0
    GROUP BY user_id HAVING MIN(created_at) < {_CUTOFF}
"""


def _parse_products(products_json: Optional[str]) -> tuple[list[str], Optional[str]]:
    if not products_json:
        return [], None
    try:
        data = json.loads(products_json)
    except json.JSONDecodeError:
        return [], None
    if isinstance(data, dict):  # current format
        return [str(i) for i in data.get("product_ids", [])], data.get("results_title")
    if isinstance(data, list):  # older course rows: list of product snapshots
        return [str(p["product_id"]) for p in data if isinstance(p, dict) and "product_id" in p], None
    return [], None


def _rows(user_id: int, limit: int):
    purge_expired(user_id)
    with db_rw() as con:
        rows = con.execute(
            "SELECT role, content, products_json, created_at FROM chat_messages "
            "WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, limit)).fetchall()
    return list(reversed(rows))


def load_history(user_id: int, limit: int = HISTORY_LIMIT) -> list[HistoryMessage]:
    """Saved messages for the website, oldest first, with live product cards."""
    out = []
    for r in _rows(user_id, limit):
        ids, title = _parse_products(r["products_json"])
        cards = product_cards(ids)
        out.append(HistoryMessage(role=r["role"], content=r["content"], products=cards,
                                  results_title=(title or "Bulldog's picks") if cards else None,
                                  created_at=r["created_at"]))
    return out


def load_turns(user_id: int, limit: int) -> list[ChatTurn]:
    """Recent saved messages for the agent's message history."""
    return [ChatTurn(role=r["role"], content=r["content"][:4000],
                     product_ids=_parse_products(r["products_json"])[0][:12])
            for r in _rows(user_id, limit)]


def save_exchange(user_id: int, user_message: str, reply: str,
                  product_ids: list[str], results_title: Optional[str]) -> None:
    """Save one shopper message and Bulldog's reply."""
    products_json = (json.dumps({"product_ids": product_ids, "results_title": results_title})
                     if product_ids else None)
    purge_expired(user_id)  # an expired history is wiped first, so this message starts a new clock
    with db_rw() as con:
        con.execute("INSERT INTO chat_messages (user_id, role, content) VALUES (?, 'user', ?)",
                    (user_id, user_message))
        con.execute("INSERT INTO chat_messages (user_id, role, content, products_json) "
                    "VALUES (?, 'assistant', ?, ?)", (user_id, reply, products_json))
        # Cap: keep only the newest MAX_SAVED_MESSAGES real messages for this shopper.
        con.execute("""DELETE FROM chat_messages WHERE user_id = ? AND is_sample = 0 AND id NOT IN (
                           SELECT id FROM chat_messages WHERE user_id = ? AND is_sample = 0
                           ORDER BY id DESC LIMIT ?)""", (user_id, user_id, MAX_SAVED_MESSAGES))


def count_messages(user_id: int) -> int:
    purge_expired(user_id)
    with db_rw() as con:
        return con.execute("SELECT COUNT(*) FROM chat_messages WHERE user_id = ?", (user_id,)).fetchone()[0]


def clear_history(user_id: int) -> int:
    """The shopper's Clear button: delete everything now (sample rows included)."""
    with db_rw() as con:
        return con.execute("DELETE FROM chat_messages WHERE user_id = ?", (user_id,)).rowcount


def purge_expired(user_id: Optional[int] = None) -> int:
    """Delete the whole saved history of shoppers whose 30-day clock has run out.

    With user_id, only that shopper is checked; without it, everyone is.
    """
    sql = f"DELETE FROM chat_messages WHERE is_sample = 0 AND user_id IN ({_EXPIRED_USERS})"
    args: tuple = ()
    if user_id is not None:
        sql += " AND user_id = ?"
        args = (user_id,)
    with db_rw() as con:
        return con.execute(sql, args).rowcount


def ensure_schema() -> None:
    """Add the is_sample column to older copies of the database."""
    with db_rw() as con:
        cols = {r["name"] for r in con.execute("PRAGMA table_info(chat_messages)")}
        if "is_sample" not in cols:
            con.execute("ALTER TABLE chat_messages ADD COLUMN is_sample INTEGER NOT NULL DEFAULT 0")
