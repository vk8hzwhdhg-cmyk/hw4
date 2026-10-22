"""
Build a cleaned copy of the Campus Customs database.

The original data/campus_customs.db is never modified. This script copies it to
data/campus_customs_clean.db, applies the fixes flagged in output/harness.md,
and writes a change log to output/cleaning_report.json.

Run from the Homework 4 folder:
    python scripts/clean_db.py           (refuses if app accounts exist)
    python scripts/clean_db.py --force   (rebuild anyway; deletes app accounts)
"""
import hashlib
import json
import re
import shutil
import sys
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "campus_customs.db"
DST = ROOT / "data" / "campus_customs_clean.db"
REPORT = ROOT / "output" / "cleaning_report.json"

# ---- Issue 1: placeholder rows, rewritten from the product photos ----------
STUB_FIXES = {
    "benjamin-franklin-t-shirt": {
        "garment_type": "short-sleeve t-shirt",
        "description": "Heather gray short-sleeve crewneck T-shirt with a large "
        "Benjamin Franklin College shield (blue and red quarters with white "
        "lightning bolts and fleurs-de-lis) centered on the chest above "
        "black \"BENJAMIN FRANKLIN COLLEGE\" lettering.",
        "colors": ["heather gray", "red", "blue", "white", "black"],
        "search_tags": ["Yale", "Benjamin Franklin College", "Franklin",
                        "residential college", "college crest", "shield",
                        "gray T-shirt", "short sleeve", "Campus Customs"],
    },
    "berkeley-sweater-fleece-jacket": {
        "garment_type": "full-zip fleece jacket",
        "description": "Light heather gray full-zip sweater fleece jacket with a "
        "stand collar, dark gray zipper and pocket trim, zippered hand pockets, "
        "and a small red Berkeley College shield with \"BERKELEY\" on the left "
        "chest.",
        "colors": ["heather gray", "charcoal gray", "red"],
        "search_tags": ["Yale", "Berkeley College", "Berkeley",
                        "residential college", "sweater fleece", "full zip",
                        "fleece jacket", "gray jacket", "college crest",
                        "Campus Customs"],
    },
    "timothy-dwight-college-crewneck": {
        "garment_type": "crewneck sweatshirt",
        "description": "Heather gray long-sleeve crewneck sweatshirt with ribbed "
        "collar, cuffs, and waistband, featuring a small red and white Timothy "
        "Dwight College shield above \"TIMOTHY DWIGHT\" on the left chest.",
        "colors": ["heather gray", "red", "white"],
        "search_tags": ["Yale", "Timothy Dwight College", "TD",
                        "residential college", "college crest", "crewneck",
                        "sweatshirt", "gray sweatshirt", "left chest logo",
                        "Campus Customs"],
    },
}

# ---- Issues 2 & 3: mislabeled rows ----------------------------------------
# Tennis hoodie: its siblings are "pullover hoodie" at $68, but the owner decided
# to keep the database price ($45) because the reason for the difference is
# unknown. Only the garment type label is corrected; prices are never invented.
ROW_FIXES = {
    "yale-sports-hoodie-tennis": {"garment_type": "pullover hoodie"},
}

# ---- Issues 3, 6, 7: display names -----------------------------------------
NAME_OVERRIDES = {
    "school-of-architecture-crewneck": "School of Architecture 1/4 Zip",
    "squash-left-chest-tennis": "Squash Left Chest Crewneck",
    "ua-mens-tech-l-s-2-0": "UA Men's Tech Long Sleeve 2.0",
    "champion-reverse-weave-hoodie-1": "Champion Reverse Weave Hoodie",
    "champion-mens-triumph-raglan-crew": "Champion Men's Triumph Raglan Crew",
    "t-felt-y-heavyweight": "Felt Y Heavyweight T-Shirt",
    "2025-yale-vs-harvard-t-shirt": "2025 Yale vs. Harvard T-Shirt",
    "yale-sports-creqneck-field-hockey": "Yale Sports Crewneck Field Hockey",
}
NAME_RULES = [  # applied in order to every other name
    (r"\bT Shirt\b", "T-Shirt"),
    (r"\b1 4 Zip\b", "1/4 Zip"),
    (r"\bTri Blend\b", "Tri-Blend"),
    (r"\bFull Zip\b", "Full-Zip"),
    (r"\bDouble Knit\b", "Double-Knit"),
    (r"\bUa\b", "UA"),
    (r"\bHype And Vice\b", "Hype & Vice"),
    (r"\bTrack Field\b", "Track & Field"),
    (r"\b(Of|And)\b", lambda m: m.group(1).lower()),
]

# ---- Issue 4: shopper-facing categories ------------------------------------
CATEGORY = {
    "Hoodies": ["hoodie", "pullover hoodie", "hooded sweatshirt",
                "hooded pullover sweatshirt", "full-zip hooded sweatshirt"],
    "Crewnecks": ["crewneck", "crewneck sweatshirt",
                  "raglan crewneck sweatshirt", "mockneck sweatshirt"],
    "Quarter-Zips": ["quarter-zip pullover", "quarter-zip pullover sweatshirt"],
    "T-Shirts": ["short-sleeve t-shirt", "short-sleeve crew-neck t-shirt",
                 "heavyweight short-sleeve t-shirt", "t-shirt"],
    "Long Sleeves": ["long-sleeve performance shirt",
                     "men's long-sleeve performance shirt"],
    "Jackets & Fleece": ["bomber jacket", "fleece jacket",
                         "full-zip fleece jacket", "jacket"],
}
TYPE_TO_CATEGORY = {t: cat for cat, types in CATEGORY.items() for t in types}

# ---- Issue 5: color synonyms and families ----------------------------------
COLOR_RENAME = {"navy blue": "navy"}
COLOR_FAMILY = {
    "navy": "navy",
    "heather gray": "gray", "gray": "gray", "light gray": "gray",
    "charcoal gray": "gray", "dark heather gray": "gray",
    "dark heather charcoal": "gray", "heather charcoal gray": "gray",
    "white": "white", "cream": "white", "ivory": "white",
    "blue": "blue", "royal blue": "blue", "light blue": "blue",
    "red": "red", "green": "green", "black": "black",
    "yellow": "yellow", "gold": "yellow",
    "dusty coral": "pink",
    "multicolor": "multicolor",
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean_name(pid, name):
    if pid in NAME_OVERRIDES:
        return NAME_OVERRIDES[pid]
    for pattern, repl in NAME_RULES:
        name = re.sub(pattern, repl, name)
    return name


def main():
    # The app writes accounts, sessions and chat history into the clean DB, so
    # rebuilding it would erase them. Require --force once those differ from the source.
    if DST.exists() and "--force" not in sys.argv:
        count = lambda p, t: sqlite3.connect(p).execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        if any(count(DST, t) != count(SRC, t) for t in ("users", "chat_messages")):
            sys.exit(f"{DST.name} has accounts or chat history created in the app; rerun with "
                     "--force to rebuild it from the original (this deletes them).")
    src_hash_before = sha256(SRC)
    shutil.copyfile(SRC, DST)
    con = sqlite3.connect(DST)
    con.row_factory = sqlite3.Row
    changes = []

    def log(table, key, field, old, new, issue):
        if old != new:
            changes.append({"table": table, "key": key, "field": field,
                            "old": old, "new": new, "issue": issue})

    con.execute("ALTER TABLE catalogue ADD COLUMN category TEXT")
    con.execute("ALTER TABLE catalogue ADD COLUMN color_families TEXT")

    for row in con.execute("SELECT * FROM catalogue").fetchall():
        pid = row["product_id"]
        new = dict(row)

        for field, value in STUB_FIXES.get(pid, {}).items():
            new[field] = json.dumps(value) if isinstance(value, list) else value
            log("catalogue", pid, field, row[field], new[field],
                "1 placeholder row")
        for field, value in ROW_FIXES.get(pid, {}).items():
            new[field] = value
            log("catalogue", pid, field, row[field], value, "2 mislabeled type")

        typed = new["garment_type"]
        new["garment_type"] = typed.lower()
        log("catalogue", pid, "garment_type", typed, new["garment_type"],
            "4 garment_type casing")

        new["name"] = clean_name(pid, row["name"])
        log("catalogue", pid, "name", row["name"], new["name"], "3/6/7 display name")

        colors = [COLOR_RENAME.get(c, c) for c in json.loads(new["colors"])]
        colors = list(dict.fromkeys(colors))
        if json.dumps(colors) != new["colors"]:
            log("catalogue", pid, "colors", new["colors"], json.dumps(colors),
                "5 color synonyms")
        new["colors"] = json.dumps(colors)
        families = list(dict.fromkeys(COLOR_FAMILY[c] for c in colors))

        con.execute(
            """UPDATE catalogue SET name=?, garment_type=?, description=?,
               colors=?, search_tags=?, price=?, category=?, color_families=?
               WHERE product_id=?""",
            (new["name"], new["garment_type"], new["description"],
             new["colors"], new["search_tags"], new["price"],
             TYPE_TO_CATEGORY[new["garment_type"]], json.dumps(families), pid))

    # ---- Sample chats: the 22 course messages are kept for learning and are
    # exempt from the 30-day chat retention (see backend/memory.py).
    con.execute("ALTER TABLE chat_messages ADD COLUMN is_sample INTEGER NOT NULL DEFAULT 0")
    con.execute("UPDATE chat_messages SET is_sample = 1")

    # ---- Issue 12: empty product lists -> NULL -----------------------------
    for (mid,) in con.execute(
            "SELECT id FROM chat_messages WHERE products_json = '[]'").fetchall():
        log("chat_messages", mid, "products_json", "[]", None, "12 empty list")
    con.execute("UPDATE chat_messages SET products_json = NULL "
                "WHERE products_json = '[]'")

    # ---- Issue 8: stock status view; Issue 13: indexes ---------------------
    con.executescript("""
        CREATE VIEW product_stock AS
        SELECT i.product_id, c.name, i.size, i.quantity,
               CASE WHEN i.quantity = 0 THEN 'sold out'
                    WHEN i.quantity <= 3 THEN 'low stock'
                    ELSE 'in stock' END AS stock_status
        FROM inventory i JOIN catalogue c USING (product_id);
        CREATE INDEX idx_inventory_product ON inventory(product_id);
        CREATE INDEX idx_chat_user ON chat_messages(user_id);
        CREATE INDEX idx_catalogue_category ON catalogue(category);
        -- Login sessions (also created by backend/auth.py on startup).
        CREATE TABLE sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            expires_at TEXT NOT NULL
        );
    """)
    con.commit()

    unmapped = con.execute(
        "SELECT product_id FROM catalogue WHERE category IS NULL").fetchall()
    assert not unmapped, unmapped
    assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    con.execute("VACUUM")
    con.close()

    assert sha256(SRC) == src_hash_before, "original database was modified!"

    summary = {}
    for c in changes:
        summary[c["issue"]] = summary.get(c["issue"], 0) + 1
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text(json.dumps({
        "source": "data/campus_customs.db",
        "source_sha256_unchanged": src_hash_before,
        "output": "data/campus_customs_clean.db",
        "schema_additions": [
            "catalogue.category", "catalogue.color_families",
            "view product_stock", "idx_inventory_product", "idx_chat_user",
            "idx_catalogue_category", "table sessions", "chat_messages.is_sample"],
        "not_changed": [
            "product_id and image_file_path (renaming would break image links)",
            "users table (name already matches first + last; Test User kept "
            "for development)",
            "inventory quantities"],
        "owner_decisions": [
            "yale-sports-hoodie-tennis keeps its database price ($45); only its "
            "garment_type label was corrected"],
        "change_counts": summary,
        "changes": changes,
    }, indent=2))
    print(f"Wrote {DST.name} with {len(changes)} field changes")
    for issue, n in sorted(summary.items()):
        print(f"  {issue}: {n}")


if __name__ == "__main__":
    main()
