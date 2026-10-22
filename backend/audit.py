"""
Append-only audit trail of the Bulldog agent loop: output/audit_trail.json.

The file is one JSON array that only ever grows. New entries are added at the
end by moving the closing "]"; earlier entries are never rewritten or removed,
and nothing wipes the file between runs. A file lock keeps concurrent chats
from interleaving writes.

Each chat turn adds, sharing one run_id:
  run_start  - who (user id or "guest"), page path, message length, what was redacted,
               and a short preview of the already-redacted message
  tool_call  - tool name, short args, short result (sensitive values masked)
  retry      - when the model's output or a tool call had to be retried
  run_end    - stop_reason, the model's finish_reason, tool/request counts,
               tokens, products shown, duration

Never logged: emails, passwords, session tokens, the API key, raw messages,
or full discount codes.
"""
import fcntl
import json
import logging
import os
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from pydantic_ai.messages import ModelResponse, RetryPromptPart, ToolCallPart, ToolReturnPart

ROOT = Path(__file__).resolve().parent.parent
AUDIT_PATH = Path(os.getenv("AUDIT_TRAIL", ROOT / "output" / "audit_trail.json"))
SHORT = 160
log = logging.getLogger("uvicorn.error")


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def short(value: Any, limit: int = SHORT) -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=str)
    text = re.sub(r"\s+", " ", text)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _mask(text: str) -> str:
    """Mask anything sensitive that could appear in a tool result."""
    text = re.sub(r"(?i)\bboola(\d{2})(\d{2})\b", r"Boola••\2", text)  # discount codes
    text = re.sub(r"[\w.+-]+@[\w-]+(\.[\w-]+)+", "[email]", text)       # full emails
    return text


def _result_text(part: ToolReturnPart) -> str:
    content = part.content
    if hasattr(content, "model_dump"):
        content = content.model_dump()
    text = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False, default=str)
    return short(_mask(text))


class Run:
    """Collects one chat turn's audit entries and appends them in one write."""

    def __init__(self, actor: str, page_path: Optional[str], message: str, redacted: list[str]):
        self.id = uuid.uuid4().hex[:12]
        self.t0 = time.monotonic()
        self.entries: list[dict] = [{
            "time": now(), "run_id": self.id, "event": "run_start", "actor": actor,
            "page": page_path, "message_chars": len(message), "redacted": redacted,
            "message_preview": short(_mask(message), 80),
        }]

    def add_agent_messages(self, messages) -> dict:
        """Record tool calls, their results and retries; return counts for run_end."""
        calls: dict[str, dict] = {}
        finish_reason, n_calls = None, 0
        for m in messages:
            if isinstance(m, ModelResponse) and m.finish_reason:
                finish_reason = m.finish_reason
            for p in getattr(m, "parts", []):
                if isinstance(p, ToolCallPart) and p.tool_name != "final_result":
                    n_calls += 1
                    entry = {"time": now(), "run_id": self.id, "event": "tool_call", "tool": p.tool_name,
                             "args": short(p.args_as_json_str()), "result": None}
                    calls[p.tool_call_id] = entry
                    self.entries.append(entry)
                elif isinstance(p, ToolReturnPart) and p.tool_call_id in calls:
                    calls[p.tool_call_id]["result"] = _result_text(p)
                elif isinstance(p, RetryPromptPart):
                    self.entries.append({"time": now(), "run_id": self.id, "event": "retry",
                                         "tool": p.tool_name, "detail": short(str(p.content), 120)})
        return {"finish_reason": finish_reason, "tool_calls": n_calls}

    def end(self, stop_reason: str, **extra) -> None:
        self.entries.append({"time": now(), "run_id": self.id, "event": "run_end", "stop_reason": stop_reason,
                             "duration_ms": round((time.monotonic() - self.t0) * 1000), **extra})
        append(self.entries)


def append(entries: list[dict]) -> None:
    """Append entries to the JSON array without rewriting earlier entries."""
    if not entries:
        return
    body = ",\n".join(json.dumps(e, ensure_ascii=False) for e in entries).encode()
    try:
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(AUDIT_PATH, "a+b") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            f.seek(0, os.SEEK_END)
            size = f.tell()
            if size == 0:
                f.write(b"[\n" + body + b"\n]\n")
                return
            f.seek(max(0, size - 256))
            tail = f.read()
            close = tail.rfind(b"]")
            if close == -1:  # never destroy an unreadable file; write alongside it instead
                raise ValueError("audit_trail.json has no closing ]")
            f.truncate(size - len(tail) + close)
            f.write(b",\n" + body + b"\n]\n")
    except Exception:
        log.exception("audit trail write failed; entries kept in audit_trail.recovery.jsonl")
        with open(AUDIT_PATH.with_suffix(".recovery.jsonl"), "a", encoding="utf-8") as r:
            for e in entries:
                r.write(json.dumps(e, ensure_ascii=False) + "\n")
