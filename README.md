# Campus Customs: Yale Bulldog Blue storefront + Bulldog AI shop assistant

A Yale merch store (React + Vite + TypeScript) with **Bulldog**, a chat assistant built as a **Pydantic AI agent** behind a **FastAPI** backend. Shoppers can:
- browse and filter products, open product pages, create an account and log in, use a cart with discount codes
- chat with Bulldog, who answers price and stock questions **from the local database** and shows matching products as cards on the page

> MGT 409 Homework 4. Full system guide (models, tools, specs, safety): [`output/harness.md`](output/harness.md).

## 1. Requirements

- **Python 3.11+** (developed on 3.12)
- **Node.js 20.19+ or 22.12+** (developed on Node 24)
- A **Portkey API key** with access to the `gpt-5.6-sol` model (Sol 5.6)

## 2. Place the data pack (not in git)

Copy the data pack into `data/` at the repo root:

```
data/
├── campus_customs.db     # catalogue, inventory by size, users
└── products/             # images referenced by the catalogue
```

On the backend's first start, it builds `data/campus_customs_clean.db` (a cleaned copy: fixed names, product categories, no price or stock changes) by running `scripts/clean_db.py` automatically. The original `campus_customs.db` is never modified.

## 3. Set the API key

```bash
cp .env.example .env
```

Then edit `.env`:

```
PORTKEY_API_KEY=your_portkey_api_key_here
PORTKEY_MODEL=gpt-5.6-sol
```

`.env` is git-ignored. The key is only read by the backend and never sent to the browser.

## 4. Run the back end (FastAPI, port 8000)

Use Python 3.11 or newer. If `python3 --version` shows something older (macOS's built-in Python is 3.9), use `python3.12` instead.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r ../requirements.txt
uvicorn main:app --reload --port 8000
```

Check it at http://localhost:8000/api/health, which returns `{"ok": true, "database": "campus_customs_clean.db"}`.

## 5. Run the front end (Vite, port 5173)

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**. The Vite dev server forwards `/api` and `/media` to the backend on port 8000, so both must be running.

**Try:**
- Click the bulldog (bottom right) and ask "What hoodies do you have?" or "How many Champion Reverse Weave Hoodies in medium?"
- Create an account, then say "Boola Boola" in the chat.

**Optional hero banner** (not in git): save the Yale Bulldog Blue banner as `frontend/public/hero/yale-bulldog-blue-banner.webp`. Without it, the home page shows a navy banner.

## 6. Checks

```bash
backend/.venv/bin/python scripts/check_agent_tools.py   # every tool answer vs data/campus_customs.db (2,249 checks)
cd frontend && npm run build                             # type-check + production build
```

## Project layout

```
hw4/
├── AI_prompts.md            # prompts used for each problem
├── requirements.txt         # backend Python packages
├── .env.example             # copy to .env and add the Portkey key
├── .gitignore
├── README.md
├── frontend/                # Vite React TypeScript app
├── backend/
│   ├── main.py              # FastAPI app; run with: uvicorn main:app --reload --port 8000
│   ├── agent.py             # agent: loads prompt + model, registers tools, runs a chat turn
│   ├── models.py            # agent: Pydantic / Pydantic AI structured types
│   ├── tools.py             # agent: the 10 tools Bulldog can call (DB lookups)
│   ├── prompts/
│   │   └── prompt.md        # agent: system prompt (voice, honesty, safety)
│   ├── auth.py              # supporting: accounts, password hashing, sessions
│   ├── memory.py            # supporting: saved chat history (30 days, logged-in only)
│   ├── store.py             # supporting: cart pricing, restock alerts, discount codes, rate limit
│   ├── privacy.py           # supporting: removes card/phone/email/password text
│   ├── audit.py             # supporting: append-only audit trail writer
│   └── size_guide.json      # supporting: sample size guide data
├── scripts/
│   ├── clean_db.py          # builds data/campus_customs_clean.db (run automatically on first start)
│   └── check_agent_tools.py # checks tool answers against the original database
└── output/
    ├── harness.md           # how the system works + build log
    ├── design.md            # design changes and why they help sales
    ├── usability.md         # usability improvements and tests
    ├── app_check.html       # live-site test report
    ├── app_check_images/    # screenshots linked from app_check.html
    ├── audit_trail.json     # append-only log of agent activity
    └── cleaning_report.json # every change made by clean_db.py
```

The **agent itself is four files**: `backend/prompts/prompt.md`, `agent.py`, `tools.py` and `models.py`. The other backend files are services that `main.py` and the tools use.

**Not in git:** `data/` (database and product images), `.env`, the hero banner, `node_modules/`, `.venv/`.
