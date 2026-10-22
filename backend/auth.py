"""
Account creation and login for Campus Customs.

- Passwords are hashed with PBKDF2-SHA256 and a random salt (never stored in plain text).
  New hashes: pbkdf2_sha256$<iterations>$<salt>$<hex digest>
  Legacy rows in the course database use pbkdf2_sha256$<salt>$<hex digest> with no
  iteration count; they are checked against common settings (see _verify_legacy) and
  upgraded to the new format on their first successful login.
- Sessions are random tokens stored in a `sessions` table and sent to the browser in an
  HttpOnly cookie, so page scripts can't read them.
"""
import hashlib
import hmac
import logging
import os
import re
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from pydantic import BaseModel, field_validator

ITERATIONS = 600_000
# Confirmed with Test User: course hashes use 120,000 iterations and a text salt.
LEGACY_ITERATIONS = int(os.getenv("LEGACY_PBKDF2_ITERATIONS", "120000"))
SESSION_COOKIE = "cc_session"
SESSION_DAYS = 7
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

log = logging.getLogger("uvicorn.error")
router = APIRouter(prefix="/api/auth", tags=["auth"])
_connect = None  # set by init(); returns a read-write sqlite3 connection


def init(connect) -> None:
    """Register the DB connection factory and create the sessions table if needed."""
    global _connect
    _connect = connect
    with connect() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                expires_at TEXT NOT NULL
            )""")


# ---- password hashing -------------------------------------------------------

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), ITERATIONS).hex()
    return f"pbkdf2_sha256${ITERATIONS}${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    parts = stored.split("$")
    if len(parts) == 4:
        _, iterations, salt, digest = parts
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(iterations)).hex()
        return hmac.compare_digest(candidate, digest)
    if len(parts) == 3:  # legacy course format, no iteration count stored
        _, salt, digest = parts
        return _verify_legacy(password, salt, digest)
    return False


# Legacy hashes don't record their settings, so try the iteration counts commonly
# used by Python/Django/Werkzeug defaults (env setting first), with the salt read
# as text or as hex bytes. Only legacy accounts pay this cost, and only until their
# first successful login, when they are upgraded to the self-describing format.
LEGACY_ITERATION_CANDIDATES = list(dict.fromkeys([
    LEGACY_ITERATIONS, 100_000, 120_000, 150_000, 200_000, 210_000, 260_000,
    310_000, 390_000, 480_000, 600_000, 1_000_000, 10_000, 50_000]))


def _verify_legacy(password: str, salt: str, digest: str) -> bool:
    salts = [("text", salt.encode())]
    if re.fullmatch(r"(?:[0-9a-f]{2})+", salt):
        salts.append(("hex", bytes.fromhex(salt)))
    for iterations in LEGACY_ITERATION_CANDIDATES:
        for salt_kind, salt_bytes in salts:
            candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), salt_bytes, iterations).hex()
            if hmac.compare_digest(candidate, digest):
                # Log the matching *setting* only (never the password) so it can be pinned.
                log.info("legacy password matched: iterations=%s salt=%s", iterations, salt_kind)
                return True
    for scheme, value in (("sha256(salt+password)", salt + password),
                          ("sha256(password+salt)", password + salt)):
        if hmac.compare_digest(hashlib.sha256(value.encode()).hexdigest(), digest):
            log.info("legacy password matched: scheme=%s", scheme)
            return True
    return False


# Used when the email doesn't exist, so a login attempt takes the same time either way.
_DUMMY_HASH = hash_password(secrets.token_hex(8))


# ---- request / response models ---------------------------------------------

class RegisterRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    confirm_password: str

    @field_validator("first_name", "last_name")
    @classmethod
    def name_ok(cls, v: str) -> str:
        v = v.strip()
        if not v or len(v) > 50:
            raise ValueError("Please enter a name (up to 50 characters).")
        return v

    @field_validator("email")
    @classmethod
    def email_ok(cls, v: str) -> str:
        v = v.strip().lower()
        if not EMAIL_RE.match(v) or len(v) > 254:
            raise ValueError("Please enter a valid email address.")
        return v

    @field_validator("password")
    @classmethod
    def password_ok(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        if len(v) > 128:
            raise ValueError("Password must be 128 characters or fewer.")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str


class User(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str


def _user_out(row: sqlite3.Row) -> User:
    first, last = row["first_name"], row["last_name"]
    if not first:  # fall back to the legacy `name` column
        first, _, last = (row["name"] or "").partition(" ")
    return User(id=row["id"], first_name=first, last_name=last or "", email=row["email"])


# ---- sessions ---------------------------------------------------------------

def _start_session(con: sqlite3.Connection, response: Response, user_id: int) -> None:
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)
    con.execute("INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
                (token, user_id, expires.strftime("%Y-%m-%d %H:%M:%S")))
    response.set_cookie(SESSION_COOKIE, token, max_age=SESSION_DAYS * 86400,
                        httponly=True, samesite="lax", secure=False, path="/")


def current_user(cc_session: Optional[str] = Cookie(default=None)) -> Optional[User]:
    """FastAPI dependency: the logged-in user, or None."""
    if not cc_session:
        return None
    with _connect() as con:
        row = con.execute(
            """SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id
               WHERE s.token = ? AND s.expires_at > datetime('now')""",
            (cc_session,)).fetchone()
    return _user_out(row) if row else None


def require_user(user: Optional[User] = Depends(current_user)) -> User:
    if user is None:
        raise HTTPException(401, "Please log in.")
    return user


# ---- endpoints --------------------------------------------------------------

@router.post("/register", response_model=User, status_code=201)
def register(body: RegisterRequest, response: Response):
    if body.password != body.confirm_password:
        raise HTTPException(422, "Passwords do not match.")
    with _connect() as con:
        if con.execute("SELECT 1 FROM users WHERE email = ?", (body.email,)).fetchone():
            raise HTTPException(409, "An account with this email already exists. Try logging in.")
        cur = con.execute(
            "INSERT INTO users (name, email, password_hash, first_name, last_name) "
            "VALUES (?, ?, ?, ?, ?)",
            (f"{body.first_name} {body.last_name}", body.email,
             hash_password(body.password), body.first_name, body.last_name))
        _start_session(con, response, cur.lastrowid)
        row = con.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
    return _user_out(row)


# ---- login lockout ------------------------------------------------------------
# After MAX_FAILED_LOGINS wrong passwords for one email within LOCKOUT_WINDOW,
# that email is blocked for the rest of the window. Kept in memory: it resets
# when the server restarts, which is fine for one server (use Redis or the DB
# for several).
MAX_FAILED_LOGINS = 5
LOCKOUT_WINDOW = timedelta(minutes=15)
_failed_logins: dict[str, list[datetime]] = {}


def _recent_failures(email: str) -> list[datetime]:
    cutoff = datetime.now(timezone.utc) - LOCKOUT_WINDOW
    recent = [t for t in _failed_logins.get(email, []) if t > cutoff]
    _failed_logins[email] = recent
    return recent


@router.post("/login", response_model=User)
def login(body: LoginRequest, response: Response):
    email = body.email.strip().lower()
    recent = _recent_failures(email)
    if len(recent) >= MAX_FAILED_LOGINS:
        wait = recent[0] + LOCKOUT_WINDOW - datetime.now(timezone.utc)
        minutes = max(1, -(-int(wait.total_seconds()) // 60))
        log.warning("login locked for an account after %s failed attempts", len(recent))
        raise HTTPException(429, f"Too many login attempts. Please wait {minutes} minute"
                                 f"{'s' if minutes != 1 else ''} and try again.")
    with _connect() as con:
        row = con.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        ok = verify_password(body.password, row["password_hash"] if row else _DUMMY_HASH)
        if not row or not ok:
            recent.append(datetime.now(timezone.utc))
            raise HTTPException(401, "Incorrect email or password.")
        _failed_logins.pop(email, None)
        if row["password_hash"].count("$") == 2:  # upgrade legacy hash
            con.execute("UPDATE users SET password_hash = ? WHERE id = ?",
                        (hash_password(body.password), row["id"]))
        con.execute("DELETE FROM sessions WHERE expires_at <= datetime('now')")
        _start_session(con, response, row["id"])
    return _user_out(row)


@router.post("/logout", status_code=204)
def logout(response: Response, cc_session: Optional[str] = Cookie(default=None)):
    if cc_session:
        with _connect() as con:
            con.execute("DELETE FROM sessions WHERE token = ?", (cc_session,))
    response.delete_cookie(SESSION_COOKIE, path="/")


@router.get("/me", response_model=Optional[User])
def me(user: Optional[User] = Depends(current_user)):
    return user
