"""
Structured types for the Campus Customs API and the Bulldog shop agent.

- Product types: returned by the catalogue API.
- Chat types: sent to and returned from /api/chat.
- AgentReply: the structured output the agent produces each turn.
- ShopDeps: per-request data handed to the agent's tools.
"""
from dataclasses import dataclass, field
from typing import Literal, Optional

from pydantic import BaseModel, Field

StockStatus = Literal["in stock", "low stock", "sold out"]


# ---- products --------------------------------------------------------------

class SizeStock(BaseModel):
    size: str
    quantity: int
    status: StockStatus


class ProductSummary(BaseModel):
    product_id: str
    name: str
    category: str
    garment_type: str
    description: str
    colors: list[str]
    price: float
    image_url: str
    total_stock: int


class ProductDetail(ProductSummary):
    search_tags: list[str]
    sizes: list[SizeStock]


class ProductCard(BaseModel):
    """A product card shown on the page and in the chat.

    Built by the server from the database. The agent only chooses which
    product_ids to show; it never supplies prices, names or images.
    """
    product_id: str
    name: str
    category: str
    price: float
    image_url: str
    short_description: str
    colors: list[str]
    in_stock: bool


# ---- agent tool results ----------------------------------------------------------
# Every price and quantity below is read from the database at call time.

class ProductMatch(BaseModel):
    """One search hit: enough to recommend an item, not to promise a size."""
    product_id: str
    name: str
    category: str
    price: float
    colors: list[str]
    in_stock: bool = Field(description="True if at least one size has stock.")


class ProductInfo(BaseModel):
    """Full facts for one product: description, price and stock for every size."""
    product_id: str
    name: str
    category: str
    description: str
    colors: list[str]
    price: float
    total_quantity: int
    sizes: list[SizeStock]


class SearchResults(BaseModel):
    """search_products result: the best matches plus how many exist in total."""
    total_matches: int
    showing: int
    products: list[ProductMatch]


class PriceInfo(BaseModel):
    product_id: str
    name: str
    price: float
    currency: Literal["USD"] = "USD"


class StockCheck(BaseModel):
    """Stock for one product, for one size if asked, otherwise all sizes."""
    product_id: str
    name: str
    requested_size: Optional[str] = None
    sizes: list[SizeStock]
    total_quantity: int
    available_sizes: list[str]
    sold_out_sizes: list[str]
    fully_sold_out: bool


class NotFound(BaseModel):
    """Returned instead of guessing when a product or size can't be found."""
    error: str
    did_you_mean: list[ProductMatch] = Field(default_factory=list)
    valid_sizes: list[str] = Field(default_factory=list)


class PageInfo(BaseModel):
    """get_current_page result: what the shopper is looking at."""
    path: str
    page_type: str
    category: Optional[str] = None
    search: Optional[str] = None
    product: Optional[ProductInfo] = Field(default=None, description="Set on a product page.")


class AccountInfo(BaseModel):
    """get_my_account result: the logged-in shopper's own profile, minimized.

    The full email and last name never leave our server; the model sees a
    masked email (ad•••@yale.edu) and the last initial.
    """
    logged_in: bool
    first_name: Optional[str] = None
    last_initial: Optional[str] = None
    email_masked: Optional[str] = None


# ---- chat --------------------------------------------------------------------

class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)
    # Products shown with an assistant turn, so "the first one" still makes sense later.
    product_ids: list[str] = Field(default_factory=list, max_length=12)


class PageContext(BaseModel):
    """Where the shopper is on the website when they send a message (sent by the browser)."""
    path: str = Field(default="/", max_length=200)
    product_id: Optional[str] = Field(default=None, max_length=120)
    category: Optional[str] = Field(default=None, max_length=60)
    search: Optional[str] = Field(default=None, max_length=100)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    # Used for guests only; logged-in shoppers' history is loaded from the database.
    history: list[ChatTurn] = Field(default_factory=list, max_length=40)
    page: Optional[PageContext] = None


class ChatResponse(BaseModel):
    """API contract for POST /api/chat."""
    reply: str
    results_title: Optional[str] = None
    products: list[ProductCard] = Field(default_factory=list)
    # Kinds of sensitive info removed from the shopper's message, e.g. ["card number"],
    # and the cleaned message, so the website can replace what's shown on screen.
    redacted: list[str] = Field(default_factory=list)
    safe_message: Optional[str] = None


class AgentReply(BaseModel):
    """The agent's structured answer for one turn."""
    reply: str = Field(description="Message to the shopper, in markdown.")
    product_ids: list[str] = Field(
        default_factory=list, max_length=12,
        description="IDs of the matching products to show as cards on the page, most relevant "
                    "first, taken from tool results this turn. Empty if no products apply.")
    results_title: Optional[str] = Field(
        default=None, max_length=60,
        description="Short heading for the cards, e.g. 'Hoodies' or 'Navy crewnecks under $60'.")


class HistoryMessage(BaseModel):
    """One saved chat message, as returned by GET /api/chat/history."""
    role: Literal["user", "assistant"]
    content: str
    results_title: Optional[str] = None
    products: list[ProductCard] = Field(default_factory=list)  # re-read from the DB on load
    created_at: str


class ChatHistory(BaseModel):
    messages: list[HistoryMessage]


# ---- cart, restock alerts, account ------------------------------------------------------

class CartItemIn(BaseModel):
    product_id: str = Field(max_length=120)
    size: str = Field(max_length=20)
    quantity: int = Field(ge=1, le=99)


class CartQuoteRequest(BaseModel):
    items: list[CartItemIn] = Field(default_factory=list, max_length=50)
    discount_code: Optional[str] = Field(default=None, max_length=30)


class CartLine(BaseModel):
    """One cart line priced from the database (never from the browser)."""
    product_id: str
    name: Optional[str] = None
    size: str
    price: Optional[float] = None
    image_url: Optional[str] = None
    quantity: int                 # what can actually be bought (capped by stock and 10/line)
    requested: int
    available: int = 0
    line_total: float = 0
    status: Literal["ok", "limited", "sold_out", "unavailable"]
    message: Optional[str] = None


class AppliedDiscount(BaseModel):
    code: str
    percent_off: int
    amount: float
    expires_at: str


class CartQuote(BaseModel):
    lines: list[CartLine]
    item_count: int
    subtotal: float
    discount: Optional[AppliedDiscount] = None
    discount_error: Optional[str] = None
    total: float = 0
    currency: Literal["USD"] = "USD"


class DiscountInfo(BaseModel):
    """A shopper's Boola Boola code (one per account per year, valid 7 days)."""
    code: str
    percent_off: int
    issued_at: str
    expires_at: str
    status: Literal["active", "expired", "redeemed"]


class RestockRequest(BaseModel):
    product_id: str = Field(max_length=120)
    size: str = Field(max_length=20)
    email: Optional[str] = Field(default=None, max_length=254)  # guests only; logged in uses account email


class RestockAlert(BaseModel):
    id: int
    product_id: str
    product_name: str
    size: str
    created_at: str


class AccountSummary(BaseModel):
    first_name: str
    last_name: str
    email: str
    member_since: str
    saved_messages: int
    restock_alerts: list[RestockAlert]
    discount: Optional[DiscountInfo] = None


# ---- agent dependencies -------------------------------------------------------------

@dataclass
class Shopper:
    """The logged-in customer, taken from the session (never from the request body)."""
    user_id: int
    first_name: str
    last_name: str
    email: str


@dataclass
class CurrentPage:
    """Page context after the server has checked it against the database."""
    path: str
    page_type: Literal["home", "products", "product", "about", "account", "other"]
    product_id: Optional[str] = None      # only set if the product exists
    product_name: Optional[str] = None    # looked up from the DB, not taken from the browser
    category: Optional[str] = None        # only set if it's a real category
    search: Optional[str] = None


@dataclass
class ShopDeps:
    shopper: Optional[Shopper] = None
    page: Optional[CurrentPage] = None
    # Product IDs returned by tools this turn; only these can become cards.
    seen_product_ids: set[str] = field(default_factory=set)
