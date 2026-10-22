"""
Customer data protection for the chat.

redact() removes sensitive details from a shopper's message before it is sent
to the AI model provider or saved in chat_messages. mask_email() hides most of
an email address. Both are pure functions, so they're easy to test.
"""
import re

# Card numbers: 13–19 digits, optionally grouped with spaces or dashes; must pass the Luhn check.
_CARD = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")
_SSN = re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)")
_PHONE = re.compile(r"(?<![\w])(?:\+?1[ .-]?)?\(?\d{3}\)?[ .-]?\d{3}[ .-]?\d{4}(?![\w])")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_PASSWORD = re.compile(r"(?i)\b(pass(?:word|code)?|pwd)\b(\s*(?:is|=|:)\s*)\S+")


def _luhn_ok(digits: str) -> bool:
    total, double = 0, False
    for ch in reversed(digits):
        d = int(ch)
        if double:
            d = d * 2 - 9 if d > 4 else d * 2
        total += d
        double = not double
    return total % 10 == 0


def redact(text: str) -> tuple[str, list[str]]:
    """Return (safe_text, kinds_removed). Order matters: cards before phones."""
    found: list[str] = []

    def card(m: re.Match) -> str:
        digits = re.sub(r"\D", "", m.group())
        if 13 <= len(digits) <= 19 and _luhn_ok(digits):
            found.append("card number")
            return "[card number removed]"
        return m.group()

    def sub(pattern: re.Pattern, label: str, s: str, repl=None) -> str:
        def r(m: re.Match) -> str:
            found.append(label)
            return repl(m) if repl else f"[{label} removed]"
        return pattern.sub(r, s)

    text = _CARD.sub(card, text)
    text = sub(_SSN, "SSN", text)
    text = sub(_PASSWORD, "password", text, lambda m: f"{m.group(1)}{m.group(2)}[removed]")
    text = sub(_EMAIL, "email address", text)
    text = sub(_PHONE, "phone number", text)
    return text, list(dict.fromkeys(found))


def mask_email(email: str) -> str:
    """ada.lovelace@yale.edu -> ad•••@yale.edu"""
    local, _, domain = email.partition("@")
    return f"{local[:2]}•••@{domain}" if domain else "•••"
