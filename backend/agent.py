"""
Bulldog shop agent: loads the system prompt, connects to the model through
Portkey, registers the tools, and runs one chat turn.

Settings come from Homework 4/.env:
    PORTKEY_API_KEY   secret, never sent to the browser
    PORTKEY_MODEL     e.g. gpt-5.6-sol (Sol 5.6)
"""
import logging
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import (ModelMessage, ModelRequest, ModelResponse, TextPart, ToolCallPart,
                                  UserPromptPart)
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.usage import UsageLimits
from pydantic_ai.exceptions import UsageLimitExceeded

import audit
import memory
from models import AgentReply, ChatRequest, ChatResponse, ChatTurn, ShopDeps, Shopper
from privacy import redact
import store
from tools import AGENT_TOOLS, product_cards, resolve_page

BACKEND = Path(__file__).resolve().parent
load_dotenv(BACKEND.parent / ".env")

PROMPT_PATH = BACKEND / "prompts" / "prompt.md"
PORTKEY_URL = "https://api.portkey.ai/v1"
MAX_HISTORY_TURNS = 12
# Loop limits for one chat turn (Pydantic AI's default would allow 50 model requests).
# Real turns use 2 requests and up to ~6 tool calls (see output/audit_trail.json).
LOOP_LIMITS = UsageLimits(request_limit=8, tool_calls_limit=12, total_tokens_limit=80_000)
log = logging.getLogger("uvicorn.error")


def load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def get_agent() -> Agent[ShopDeps, AgentReply]:
    """Build the agent once, on the first chat request."""
    key = os.getenv("PORTKEY_API_KEY")
    model_name = os.getenv("PORTKEY_MODEL", "gpt-5.6-sol")
    if not key:
        raise RuntimeError("PORTKEY_API_KEY is missing from Homework 4/.env")
    client = AsyncOpenAI(api_key=key, base_url=PORTKEY_URL,
                         default_headers={"x-portkey-api-key": key},
                         max_retries=1, timeout=60)
    model = OpenAIChatModel(model_name, provider=OpenAIProvider(openai_client=client))
    agent = Agent(model, deps_type=ShopDeps, output_type=AgentReply,
                  instructions=load_prompt(), tools=AGENT_TOOLS, retries=2)

    @agent.instructions
    def shopper_context(ctx: RunContext[ShopDeps]) -> str:
        """Who is chatting. Comes from the login session, not from the message."""
        # Data minimization: only the first name goes to the model provider.
        s = ctx.deps.shopper
        if s is None:
            return "## Who is chatting\nA guest (not logged in). Their chat is not saved."
        return ("## Who is chatting\n"
                f"Logged-in customer, first name {s.first_name}. Greet them by first name. "
                "For their own account details use get_my_account (it returns a masked email). "
                "Their chat history is saved, so earlier messages may be from a previous visit.")

    @agent.instructions
    def page_context(ctx: RunContext[ShopDeps]) -> str:
        """Where the shopper is on the website, checked against the database."""
        p = ctx.deps.page
        if p is None:
            return "## Current page\nUnknown."
        lines = [f"## Current page\nPath {p.path} ({p.page_type} page)."]
        if p.product_id:
            lines.append(f"They are viewing the product **{p.product_name}** (product_id "
                         f"`{p.product_id}`). If they say \"this\", \"it\" or \"this one\" without "
                         "naming a product, they mean this item.")
        if p.category:
            lines.append(f"They are browsing the {p.category} category.")
        if p.search:
            lines.append(f"Their current search on the Products page is: {p.search!r}.")
        return " ".join(lines)

    log.info("Bulldog agent loaded: model=%s prompt=%s", model_name, PROMPT_PATH.name)
    return agent


def _history(turns: list[ChatTurn]) -> list[ModelMessage]:
    """Convert saved or browser-sent turns into Pydantic AI message history.

    Assistant turns get a note of the products that were shown with them, so
    references like "the second one" still work after a reload.
    """
    turns = turns[-MAX_HISTORY_TURNS:]
    names = {c.product_id: c.name for c in product_cards(
        list(dict.fromkeys(pid for t in turns for pid in t.product_ids)))}
    messages: list[ModelMessage] = []
    for turn in turns:
        if turn.role == "user":
            messages.append(ModelRequest(parts=[UserPromptPart(content=turn.content)]))
        else:
            shown = [f"{i}. {names[pid]} ({pid})" for i, pid in
                     enumerate((p for p in turn.product_ids if p in names), 1)]
            note = f"\n\n[Products shown: {'; '.join(shown)}]" if shown else ""
            messages.append(ModelResponse(parts=[TextPart(content=turn.content + note)]))
    # History must start with a request; drop a leading assistant turn if the window cut it.
    while messages and isinstance(messages[0], ModelResponse):
        messages.pop(0)
    return messages


async def run_chat(req: ChatRequest, shopper: Optional[Shopper] = None) -> ChatResponse:
    """One chat turn. Logged-in shoppers' history comes from (and is saved to) the database."""
    # Remove card numbers, phone numbers, emails, etc. before the AI or the database sees them.
    message, redacted = redact(req.message)

    run = audit.Run(f"user:{shopper.user_id}" if shopper else "guest",
                    req.page.path if req.page else None, message, redacted)

    # "Boola Boola" easter egg: the server (never the AI) issues the discount code.
    boola = store.boola_message(shopper.user_id if shopper else None) if store.mentions_boola(message) else None
    if boola and len(re.findall(r"[a-z]", store.without_boola(message), re.I)) < 3:
        response = ChatResponse(reply=boola, redacted=redacted, safe_message=message if redacted else None)
        if shopper:
            memory.save_exchange(shopper.user_id, message, boola, [], None)
        log.info("chat: boola boola reply (no model call)")
        run.end("boola_shortcut", model_called=False, code_issued="Here's your one-time" in boola)
        return response
    if redacted:
        log.info("chat redacted: %s", ", ".join(redacted))
    deps = ShopDeps(shopper=shopper, page=resolve_page(req.page))
    if shopper:
        turns = memory.load_turns(shopper.user_id, MAX_HISTORY_TURNS)
    else:  # guest history comes from the browser, so clean it too
        turns = [t.model_copy(update={"content": redact(t.content)[0]}) for t in req.history]
    # With a Boola Boola announcement, the AI only answers the rest of the message.
    agent_input = store.without_boola(message) if boola else message
    try:
        result = await get_agent().run(agent_input, deps=deps, message_history=_history(turns),
                                       usage_limits=LOOP_LIMITS)
    except Exception as e:
        reason = ("usage_limit" if isinstance(e, UsageLimitExceeded) else
                  "content_filter" if "content_filter" in str(getattr(e, "body", "") or e) else "model_error")
        run.end(reason, error=type(e).__name__, detail=audit.short(str(e), 120))
        raise
    out = result.output
    try:
        counts = run.add_agent_messages(result.new_messages())
    except Exception:
        log.exception("audit tool logging failed")
        counts = {"finish_reason": None, "tool_calls": None}
    calls = [f"{p.tool_name}({p.args_as_json_str()})" for m in result.new_messages()
             for p in getattr(m, "parts", []) if isinstance(p, ToolCallPart)]
    log.info("chat tools used: %s", ", ".join(calls) or "none")
    # Only show cards for products a tool actually returned this turn.
    ids = [pid for pid in dict.fromkeys(out.product_ids) if pid in deps.seen_product_ids]
    dropped = [pid for pid in dict.fromkeys(out.product_ids) if pid not in deps.seen_product_ids]
    cards = product_cards(ids)
    reply = f"{boola}\n\n{out.reply}" if boola else out.reply
    response = ChatResponse(reply=reply, products=cards, redacted=redacted,
                            safe_message=message if redacted else None,
                            results_title=(out.results_title or "Bulldog's picks") if cards else None)
    if shopper:
        memory.save_exchange(shopper.user_id, message, response.reply,
                             [c.product_id for c in cards], response.results_title)
    try:  # auditing must never break a shopper's chat
        usage = result.usage() if callable(result.usage) else result.usage
        run.end("final_result", finish_reason=counts["finish_reason"], tool_calls=counts["tool_calls"],
                model_requests=usage.requests, input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens, products_shown=len(cards),
                unverified_product_ids_dropped=dropped, reply_chars=len(response.reply),
                boola_code_message=bool(boola))
    except Exception:
        log.exception("audit run_end failed")
    return response
