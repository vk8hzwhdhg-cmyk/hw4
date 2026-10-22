"""
Check that the agent's lookup tools return exactly what is in the ORIGINAL
data/campus_customs.db: price and quantity for every product and size.

Run from the Homework 4 folder (no API key needed; no model is called):
    backend/.venv/bin/python scripts/check_agent_tools.py
"""
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from models import NotFound, ShopDeps  # noqa: E402
import tools  # noqa: E402


def ctx():
    return SimpleNamespace(deps=ShopDeps())


original = sqlite3.connect(f"file:{ROOT / 'data' / 'campus_customs.db'}?mode=ro", uri=True)
prices = dict(original.execute("SELECT product_id, price FROM catalogue"))
stock = {(p, s): q for p, s, q in original.execute("SELECT product_id, size, quantity FROM inventory")}

failures, checks = [], 0


def expect(cond, msg):
    global checks
    checks += 1
    if not cond:
        failures.append(msg)


for pid, price in prices.items():
    info = tools.get_product_details(ctx(), pid)
    expect(info.price == price, f"{pid}: details price {info.price} != {price}")
    expect(bool(info.description.strip()), f"{pid}: empty description")
    expect(tools.get_price(ctx(), pid).price == price, f"{pid}: get_price mismatch")
    all_sizes = tools.check_stock(ctx(), pid)
    expect(all_sizes.total_quantity == sum(q for (p, _), q in stock.items() if p == pid),
           f"{pid}: total quantity mismatch")
    for s in all_sizes.sizes:
        q = stock[(pid, s.size)]
        expect(s.quantity == q, f"{pid} {s.size}: {s.quantity} != {q}")
        expect((s.status == "sold out") == (q == 0), f"{pid} {s.size}: sold-out flag wrong")
        one = tools.check_stock(ctx(), pid, s.size)
        expect(one.sizes[0].quantity == q and one.requested_size == s.size, f"{pid} {s.size}: single-size check")

# Name lookup, size wording, and refusals to guess
expect(tools.get_price(ctx(), "Yale Sports Hoodie Tennis").price == prices["yale-sports-hoodie-tennis"],
       "lookup by exact name")
expect(tools.check_stock(ctx(), "baseball-left-chest-crewneck", "extra small").sizes[0].quantity
       == stock[("baseball-left-chest-crewneck", "XS")], "size alias 'extra small'")
expect(tools.check_stock(ctx(), "baseball-left-chest-crewneck", "2XL").requested_size == "XXL", "size alias '2XL'")
expect(isinstance(tools.check_stock(ctx(), "baseball-left-chest-crewneck", "XXXL"), NotFound), "unknown size")
expect(isinstance(tools.get_price(ctx(), "harvard mug"), NotFound), "unknown product")

print(f"{checks} checks, {len(failures)} failures "
      f"({len(prices)} products, {len(stock)} size rows vs data/campus_customs.db)")
for f in failures[:20]:
    print("  FAIL", f)
sys.exit(1 if failures else 0)
