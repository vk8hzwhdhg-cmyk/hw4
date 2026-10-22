"""
Catalogue access for the website API and tools for the Bulldog agent.

All prices and stock come from the cleaned database, opened read-only.
"""
import json
import os
import re
import sqlite3
from pathlib import Path
from typing import Optional, Union

from pydantic_ai import RunContext

from privacy import mask_email

from models import (AccountInfo, CurrentPage, NotFound, PageContext, PageInfo, PriceInfo, ProductCard,
                    ProductDetail, ProductInfo, ProductMatch, ProductSummary, SearchResults, ShopDeps,
                    StockCheck)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DB_PATH = Path(os.getenv("CAMPUS_DB", DATA / "campus_customs_clean.db"))
SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]

PRODUCT_SQL = """
    SELECT c.*, COALESCE(SUM(i.quantity), 0) AS total_stock
    FROM catalogue c LEFT JOIN inventory i USING (product_id)
"""


# ---- database helpers ------------------------------------------------------

def db() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise RuntimeError(f"{DB_PATH} not found; run scripts/clean_db.py first")
    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def db_rw() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def stock_status(qty: int) -> str:
    return "sold out" if qty == 0 else "low stock" if qty <= 3 else "in stock"


def _summary(row: sqlite3.Row) -> ProductSummary:
    return ProductSummary(
        product_id=row["product_id"], name=row["name"], category=row["category"],
        garment_type=row["garment_type"], description=row["description"],
        colors=json.loads(row["colors"]), price=row["price"],
        image_url=f"/media/{row['image_file_path']}", total_stock=row["total_stock"])


def _words(text: str) -> list[str]:
    """Search words, with simple plural handling ("hoodies" -> "hoodie")."""
    out = []
    for w in re.findall(r"[a-z0-9&'-]+", text.lower()):
        if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        out.append(w)
    return out


# ---- collections ----------------------------------------------------------------
# Shopper-facing collections like the "Browse" menus on yalebulldogblue.com.
# Assigned from whole words in the product name (not descriptions, which mention
# things like "football helmets" on non-sports items). A product can be in no
# collection (general Yale gear); none is in more than one.
COLLECTIONS: dict[str, list[str]] = {
    "Sports": ["baseball", "basketball", "football", "hockey", "soccer", "tennis", "track",
               "diving", "swimming", "golf", "volleyball", "lacrosse", "fencing", "squash",
               "sailing", "crew left chest", "yale vs. harvard"],
    "Schools": ["school of", "law school", "divinity school", "forest school"],
    "Colleges": ["benjamin franklin", "berkeley", "branford", "davenport", "ezra stiles",
                 "grace hopper", "jonathan edwards", "morse", "pauli murray", "pierson",
                 "saybrook", "silliman", "timothy dwight", "trumbull"],
    "Relatives": ["mom", "dad", "grandma", "grandpa", "aunt", "uncle", "brother", "sister",
                  "cousin"],
}
_COLLECTION_RE = {name: re.compile(r"\b(" + "|".join(map(re.escape, words)) + r")\b")
                  for name, words in COLLECTIONS.items()}


def collection_of(name: str) -> Optional[str]:
    low = name.lower()
    return next((c for c, rx in _COLLECTION_RE.items() if rx.search(low)), None)


def list_collections() -> list[dict]:
    with db() as con:
        names = [r["name"] for r in con.execute("SELECT name FROM catalogue")]
    counts = {c: 0 for c in COLLECTIONS}
    for n in names:
        if (c := collection_of(n)):
            counts[c] += 1
    return [{"collection": c, "count": n} for c, n in counts.items()]


# ---- catalogue queries (used by the API and the agent) ----------------------

def list_categories() -> list[dict]:
    with db() as con:
        rows = con.execute("SELECT category, COUNT(*) AS count FROM catalogue "
                           "GROUP BY category ORDER BY count DESC").fetchall()
    return [dict(r) for r in rows]


def find_products(q: Optional[str] = None, category: Optional[str] = None,
                  color: Optional[str] = None, max_price: Optional[float] = None,
                  limit: Optional[int] = None, collection: Optional[str] = None) -> list[ProductSummary]:
    where, args = [], []
    for w in _words(q or ""):
        where.append("(lower(c.name) LIKE ? OR lower(c.description) LIKE ? "
                     "OR lower(c.search_tags) LIKE ? OR lower(c.category) LIKE ?)")
        args += [f"%{w}%"] * 4
    if category:
        where.append("lower(c.category) = lower(?)")
        args.append(category)
    if color:
        where.append("(lower(c.colors) LIKE ? OR lower(c.color_families) LIKE ?)")
        args += [f"%{color.lower()}%"] * 2
    if max_price is not None:
        where.append("c.price <= ?")
        args.append(max_price)
    sql = PRODUCT_SQL + (" WHERE " + " AND ".join(where) if where else "")
    sql += " GROUP BY c.product_id ORDER BY c.category, c.name"
    with db() as con:
        rows = con.execute(sql, args).fetchall()
    if collection:
        rows = [r for r in rows if (collection_of(r["name"]) or "").lower() == collection.lower()]
    return [_summary(r) for r in (rows[:limit] if limit else rows)]


def product_detail(product_id: str) -> Optional[ProductDetail]:
    with db() as con:
        row = con.execute(PRODUCT_SQL + " WHERE c.product_id = ? GROUP BY c.product_id",
                          (product_id,)).fetchone()
        if row is None:
            return None
        stock = con.execute("SELECT size, quantity FROM inventory WHERE product_id = ?",
                            (product_id,)).fetchall()
    sizes = sorted(stock, key=lambda r: SIZE_ORDER.index(r["size"]))
    return ProductDetail(
        **_summary(row).model_dump(), search_tags=json.loads(row["search_tags"]),
        sizes=[{"size": s["size"], "quantity": s["quantity"],
                "status": stock_status(s["quantity"])} for s in sizes])


def short_description(text: str, limit: int = 120) -> str:
    """First sentence of a description, trimmed for a card."""
    first = re.split(r"(?<=\.)\s", text.strip(), maxsplit=1)[0]
    return first if len(first) <= limit else first[: limit - 1].rstrip() + "…"


def product_cards(product_ids: list[str]) -> list[ProductCard]:
    """Cards for the page and chat, in the given order, built from the database."""
    if not product_ids:
        return []
    with db() as con:
        rows = con.execute(
            PRODUCT_SQL + f" WHERE c.product_id IN ({','.join('?' * len(product_ids))})"
            " GROUP BY c.product_id", product_ids).fetchall()
    by_id = {r["product_id"]: r for r in rows}
    return [ProductCard(product_id=pid, name=r["name"], category=r["category"], price=r["price"],
                        image_url=f"/media/{r['image_file_path']}",
                        short_description=short_description(r["description"]),
                        colors=json.loads(r["colors"]), in_stock=r["total_stock"] > 0)
            for pid in product_ids if (r := by_id.get(pid))]


# ---- agent tools --------------------------------------------------------------
# Each tool reads the database when called, so answers reflect current stock.

SEARCH_LIMIT = 12

SIZE_ALIASES = {
    "xs": "XS", "x-small": "XS", "xsmall": "XS", "extra small": "XS", "extra-small": "XS",
    "s": "S", "small": "S", "sm": "S",
    "m": "M", "medium": "M", "med": "M",
    "l": "L", "large": "L", "lg": "L",
    "xl": "XL", "x-large": "XL", "xlarge": "XL", "extra large": "XL", "extra-large": "XL",
    "xxl": "XXL", "2xl": "XXL", "xx-large": "XXL", "xxlarge": "XXL", "2x": "XXL",
    "double extra large": "XXL", "extra extra large": "XXL",
}


def normalize_size(size: str) -> Optional[str]:
    return SIZE_ALIASES.get(re.sub(r"\s+", " ", size.strip().lower()))


def _match(p: ProductSummary) -> ProductMatch:
    return ProductMatch(product_id=p.product_id, name=p.name, category=p.category,
                        price=p.price, colors=p.colors, in_stock=p.total_stock > 0)


def _resolve(ctx: RunContext[ShopDeps], product: str) -> Union[ProductDetail, NotFound]:
    """Find a product by id or exact name; otherwise suggest close matches."""
    key = product.strip()
    detail = product_detail(key) or product_detail(re.sub(r"[^a-z0-9]+", "-", key.lower()).strip("-"))
    if detail is None:
        with db() as con:
            row = con.execute("SELECT product_id FROM catalogue WHERE lower(name) = lower(?)",
                              (key,)).fetchone()
        detail = product_detail(row["product_id"]) if row else None
    if detail is None:
        suggestions = [_match(p) for p in find_products(q=key, limit=3)]
        ctx.deps.seen_product_ids.update(m.product_id for m in suggestions)
        return NotFound(error=f"No product matches {product!r}. Do not guess; use a suggestion "
                              "or search_products.", did_you_mean=suggestions)
    ctx.deps.seen_product_ids.add(detail.product_id)
    return detail


def search_products(ctx: RunContext[ShopDeps], query: str = "", category: Optional[str] = None,
                    color: Optional[str] = None, max_price: Optional[float] = None,
                    collection: Optional[str] = None) -> SearchResults:
    """Search the catalogue to find products. Use this first when the shopper describes an item.

    Args:
        query: Keywords such as "hoodie", "Saybrook", "tennis", "Yale dad". Leave empty to browse.
        category: One of Hoodies, Crewnecks, T-Shirts, Quarter-Zips, Jackets & Fleece, Long Sleeves.
        color: A color such as navy, gray, white, blue, red, black, green, yellow.
        max_price: Highest price in US dollars.
        collection: One of Sports, Schools (graduate & professional schools), Colleges
            (residential colleges) or Relatives (Yale Mom, Dad, Grandpa…).

    Returns total_matches (how many products match in all) and up to 12 of them,
    with price and whether any size is in stock. It does not give size-level
    stock; use check_stock for that.
    """
    found = find_products(query, category, color, max_price, collection=collection)
    shown = [_match(p) for p in found[:SEARCH_LIMIT]]
    ctx.deps.seen_product_ids.update(m.product_id for m in shown)
    return SearchResults(total_matches=len(found), showing=len(shown), products=shown)


def get_product_details(ctx: RunContext[ShopDeps], product: str) -> Union[ProductInfo, NotFound]:
    """Get the full description, colors, price and stock quantity for every size of one product.

    Args:
        product: The product_id from search_products, or the product's exact name.
    """
    detail = _resolve(ctx, product)
    if isinstance(detail, NotFound):
        return detail
    return ProductInfo(product_id=detail.product_id, name=detail.name, category=detail.category,
                       description=detail.description, colors=detail.colors, price=detail.price,
                       total_quantity=detail.total_stock, sizes=detail.sizes)


def get_price(ctx: RunContext[ShopDeps], product: str) -> Union[PriceInfo, NotFound]:
    """Get the current price of one product in US dollars.

    Args:
        product: The product_id from search_products, or the product's exact name.
    """
    detail = _resolve(ctx, product)
    if isinstance(detail, NotFound):
        return detail
    return PriceInfo(product_id=detail.product_id, name=detail.name, price=detail.price)


def check_stock(ctx: RunContext[ShopDeps], product: str,
                size: Optional[str] = None) -> Union[StockCheck, NotFound]:
    """Check how many are in stock for one product, for one size or for all sizes.

    Args:
        product: The product_id from search_products, or the product's exact name.
        size: Optional size as the shopper said it, e.g. "M", "medium", "XL", "2XL".
              Leave empty to get every size.
    """
    detail = _resolve(ctx, product)
    if isinstance(detail, NotFound):
        return detail
    sizes = detail.sizes
    requested = None
    if size:
        requested = normalize_size(size)
        if requested is None:
            return NotFound(error=f"{size!r} is not a size we carry.", valid_sizes=SIZE_ORDER)
        sizes = [s for s in sizes if s.size == requested]
    return StockCheck(
        product_id=detail.product_id, name=detail.name, requested_size=requested, sizes=sizes,
        total_quantity=detail.total_stock,
        available_sizes=[s.size for s in detail.sizes if s.quantity > 0],
        sold_out_sizes=[s.size for s in detail.sizes if s.quantity == 0],
        fully_sold_out=detail.total_stock == 0)


# ---- page context and shopper -------------------------------------------------------

def resolve_page(page: Optional[PageContext]) -> Optional[CurrentPage]:
    """Check what the browser says about the current page against the database.

    Only a real product_id or category is kept, and the product name comes from
    the database, so text from the browser never reaches the agent unchecked.
    """
    if page is None:
        return None
    path = page.path if page.path.startswith("/") else "/"
    if path.startswith("/products/"):
        page_type = "product"
    elif path.startswith("/products"):
        page_type = "products"
    else:
        page_type = {"/": "home", "/about": "about", "/login": "account",
                     "/create-account": "account"}.get(path, "other")
    current = CurrentPage(path=path, page_type=page_type)
    if page_type == "product" and page.product_id:
        detail = product_detail(page.product_id)
        if detail:
            current.product_id, current.product_name = detail.product_id, detail.name
    if page.category and page.category.lower() in {c["category"].lower() for c in list_categories()}:
        current.category = page.category
    if page.search:
        current.search = re.sub(r"[^\w\s&'.-]", "", page.search)[:100].strip() or None
    return current


def get_current_page(ctx: RunContext[ShopDeps]) -> Union[PageInfo, NotFound]:
    """What the shopper is looking at right now on the website.

    Call this when they say "this", "it" or "this one" without naming a product,
    or ask about "the item on this page". On a product page it returns that
    product's full details (description, colors, price, stock by size).
    """
    page = ctx.deps.page
    if page is None:
        return NotFound(error="The website didn't say which page the shopper is on. Ask which item they mean.")
    product = None
    if page.product_id:
        product = get_product_details(ctx, page.product_id)
    return PageInfo(path=page.path, page_type=page.page_type, category=page.category,
                    search=page.search, product=product if isinstance(product, ProductInfo) else None)


def get_my_account(ctx: RunContext[ShopDeps]) -> AccountInfo:
    """The logged-in shopper's own account: first name, last initial and a masked email.

    Use only to answer questions about their own account. The full email is
    deliberately not available to the chat; they can see it on their My Account page.
    """
    s = ctx.deps.shopper
    if s is None:
        return AccountInfo(logged_in=False)
    return AccountInfo(logged_in=True, first_name=s.first_name,
                       last_initial=(s.last_name[:1] + ".") if s.last_name else None,
                       email_masked=mask_email(s.email))


def get_categories(ctx: RunContext[ShopDeps]) -> list[dict]:
    """List the shop's product categories and how many styles each has."""
    return list_categories()


# ---- agent tools backed by the shop services (store.py) ------------------------------
# store.py imports this module, so it is imported inside each tool to avoid a cycle.

def get_size_guide(ctx: RunContext[ShopDeps], product: Optional[str] = None) -> dict:
    """Size and fit guide (garment measurements in inches, how to measure, fit notes).

    Args:
        product: Optional product_id or exact name; returns the chart for its type.
            Leave empty for the whole guide.
    """
    import store
    guide = {k: store.SIZE_GUIDE[k] for k in ("note", "fit_note", "how_to_measure", "body_chest_inches")}
    if product:
        detail = _resolve(ctx, product)
        if isinstance(detail, NotFound):
            return detail.model_dump()
        guide["product"] = detail.name
        guide["chart"] = store.size_chart_for(detail.category)
    else:
        guide["charts"] = store.SIZE_GUIDE["charts"]
    return guide


def request_restock_alert(ctx: RunContext[ShopDeps], product: str, size: str) -> dict:
    """Sign a logged-in shopper up for an email when a sold-out size is back in stock.

    Uses the email on their account (they don't need to type it). Guests can't use
    this tool; tell them to use the "Notify me" button on the product page instead.

    Args:
        product: product_id or exact name.
        size: the sold-out size, e.g. "L" or "large".
    """
    import store
    shopper = ctx.deps.shopper
    if shopper is None:
        return {"ok": False, "message": "Guest: ask them to use the Notify me button on the product page."}
    detail = _resolve(ctx, product)
    if isinstance(detail, NotFound):
        return detail.model_dump()
    alert, message = store.create_restock_alert(detail.product_id, size, shopper.email, shopper.user_id)
    return {"ok": alert is not None, "message": message,
            "email_masked": mask_email(shopper.email) if alert else None}


def get_my_discount_code(ctx: RunContext[ShopDeps]) -> dict:
    """The logged-in shopper's Bulldog discount code (if they've unlocked one this year).

    Use when they ask about their code or discounts. Never make up codes; only the
    shop creates them (when a logged-in shopper says "Boola Boola").
    """
    import store
    if ctx.deps.shopper is None:
        return {"logged_in": False}
    info = store.latest_code(ctx.deps.shopper.user_id)
    return {"logged_in": True, "code": info.model_dump() if info else None}


# All 10 tools the Bulldog agent can call (registered in agent.py).
AGENT_TOOLS = [search_products, get_product_details, get_price, check_stock, get_categories,
               get_current_page, get_my_account, get_size_guide, request_restock_alert,
               get_my_discount_code]
