# -*- coding: utf-8 -*-
"""
Order Orchestrator - a real tool-calling agent for El-Beh El-Bawab.

The LLM (Groq, OpenAI-compatible API) reads a resident's message written in
Egyptian Arabic and decides which tools to call. Everything that is a FACT
(prices, priority) comes from deterministic tools, never from the model's head.

Flow:
  message -> LLM -> [lookup_prices, classify_priority] -> LLM -> draft order JSON
The result is a DRAFT: it needs the resident's confirmation (requires_confirmation).
Every run (tool calls included) is stored in the `agent_runs` table.

Quick manual test (from the backend folder, with GROQ_API_KEY set):
    python -m app.ai.orchestrator "هاتلي ٢ لبن وعيش سخن وبنادول بسرعة"
"""
import json
import logging
import os
import re
import sys
import time
from typing import Any, Dict, List, Optional

from app.ai import ai_agents_engine as _engine
from app.ai.groq_agent import get_client
from app.core.database import get_db

logger = logging.getLogger(__name__)

try:  # model name comes from the same config the existing Groq agent uses
    from app.core.config import GROQ_MODEL as _CFG_MODEL
except Exception:  # pragma: no cover
    _CFG_MODEL = None

AGENT_NAME = "order_orchestrator"

# ---------------------------------------------------------------- text helpers
_AR_MAP = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ة": "ه", "ؤ": "و", "ئ": "ي"})
_DIACRITICS = re.compile(r"[\u064B-\u0652\u0640]")
_AR_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")


def _norm(text: Any) -> str:
    return _DIACRITICS.sub("", str(text)).translate(_AR_MAP).strip().lower()


def _qty(value: Any) -> float:
    if isinstance(value, (int, float)) and value > 0:
        return float(min(value, 100))
    m = re.search(r"\d+(?:\.\d+)?", str(value or "").translate(_AR_DIGITS))
    if m:
        return float(min(max(float(m.group()), 0.1), 100))
    return 1.0


# ----------------------------------------------------------------------- tools
_HEAVY_WORDS = [_norm(w) for w in ["أنبوبة", "كرتونة", "شنط", "مياه", "أرز"]]

_URGENT_WORDS = {
    "medicine": ["دواء", "ادوية", "بنادول", "انسولين", "علاج", "صيدلية", "روشتة"],
    "kids_elderly": ["طفل", "رضيع", "لبن اطفال", "حفاضات", "كبير في السن", "عجوز", "مريض"],
    "utilities": ["غاز", "تسريب", "مياه قاطعة", "كهرباء قاطعة", "الاسانسير واقف"],
    "explicit": ["بسرعة", "حالا", "مستعجل", "ضروري", "طوارئ", "دلوقتي"],
}


def _prices() -> Dict[str, float]:
    return getattr(_engine, "EGYPTIAN_ITEM_PRICES", {}) or {}


def _match_price(name: str):
    """Best (longest) catalog key that matches the item name. (None, None) if unknown."""
    n = _norm(name)
    best_key, best_price = None, None
    for key, price in _prices().items():
        k = _norm(key)
        if not k or not isinstance(price, (int, float)):
            continue
        if k in n or (len(n) >= 3 and n in k):
            if best_key is None or len(k) > len(_norm(best_key)):
                best_key, best_price = key, float(price)
    return best_key, best_price


def lookup_prices(items: List[Any]) -> Dict[str, Any]:
    """Prices come ONLY from the internal catalog. Unknown items stay unknown (None)."""
    lines, unknown, known_total, heavy = [], [], 0.0, False
    for it in items or []:
        if isinstance(it, str):
            it = {"name": it}
        if not isinstance(it, dict):
            continue
        name = str(it.get("name", "")).strip()
        if not name:
            continue
        qty = _qty(it.get("quantity"))
        key, price = _match_price(name)
        if any(w in _norm(name) for w in _HEAVY_WORDS):
            heavy = True
        if price is None:
            unknown.append(name)
            lines.append({"name": name, "quantity": qty, "matched_as": None,
                          "unit_price_egp": None, "line_total_egp": None})
        else:
            total = round(price * qty, 2)
            known_total += total
            lines.append({"name": name, "quantity": qty, "matched_as": key,
                          "unit_price_egp": price, "line_total_egp": total})
    return {
        "lines": lines,
        "known_total_egp": round(known_total, 2),
        "unknown_items": unknown,
        "is_complete": bool(lines) and not unknown,
        "suggested_tip_egp": (35.0 if heavy else 20.0) if lines else 0.0,
        "price_basis": "internal estimate table, not live market prices",
    }


def classify_priority(text: str) -> Dict[str, Any]:
    n = _norm(text)
    reasons = [group for group, words in _URGENT_WORDS.items()
               if any(_norm(w) in n for w in words)]
    return {"urgency": "urgent" if reasons else "normal", "reasons": reasons}


TOOL_IMPL = {"lookup_prices": lookup_prices, "classify_priority": classify_priority}

TOOLS = [
    {"type": "function", "function": {
        "name": "lookup_prices",
        "description": "Look up estimated prices for the order items from the internal price table. "
                       "Call it once with ALL items. Unknown items come back with null price.",
        "parameters": {"type": "object", "properties": {
            "items": {"type": "array", "items": {"type": "object", "properties": {
                "name": {"type": "string", "description": "short Arabic item name, e.g. لبن"},
                "quantity": {"type": "number"}}, "required": ["name"]}}},
            "required": ["items"]}}},
    {"type": "function", "function": {
        "name": "classify_priority",
        "description": "Classify urgency (urgent/normal) of the ORIGINAL resident message.",
        "parameters": {"type": "object", "properties": {"text": {"type": "string"}},
                       "required": ["text"]}}},
]

SYSTEM_PROMPT = """You are the order assistant of "El Beh El Bawab", an Egyptian building-services app.
Residents write short messages in Egyptian Arabic dialect. Turn each message into a clean DRAFT order.

Rules:
1. Extract the items: short natural Arabic name (e.g. "لبن", not a sentence) and a numeric quantity.
2. Call lookup_prices ONCE with all items. NEVER invent or estimate a price yourself.
3. Call classify_priority with the original message text.
4. If the message is ambiguous or items are missing, do not guess: put ONE short question in
   needs_clarification (Egyptian Arabic).
5. Do NOT write prices or totals in "reply"; the app shows prices from the tool results.
6. intent is one of: "order", "emergency" (gas leak, stuck elevator, fire, injury), "other".
   For "emergency" do not build an order; reply briefly and tell them to use the SOS button.

When done, answer with ONE JSON object only, no extra text:
{"intent": "order", "reply": "short friendly Egyptian Arabic reply, no prices",
 "items": [{"name": "لبن", "quantity": 2}], "needs_clarification": null}"""


# ------------------------------------------------------------------- internals
def _candidate_models() -> List[str]:
    first = os.getenv("GROQ_MODEL") or _CFG_MODEL or "openai/gpt-oss-20b"
    out: List[str] = []
    for m in [first, "openai/gpt-oss-120b", "llama-3.3-70b-versatile"]:
        if m and m not in out:
            out.append(m)
    return out


def _parse_json(text: str) -> Dict[str, Any]:
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("model did not return JSON")
    return json.loads(text[start:end + 1])


def _run_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    fn = TOOL_IMPL.get(name)
    if fn is None:
        return {"error": f"unknown tool {name}"}
    try:
        return fn(**args)
    except Exception as exc:  # a bad tool call must not crash the agent
        return {"error": f"tool {name} failed: {exc}"}


def _tool_loop(client, model: str, messages: List[Dict[str, Any]], trace: List[Dict[str, Any]],
               max_steps: int) -> Dict[str, Any]:
    for _ in range(max_steps):
        resp = client.chat.completions.create(
            model=model, messages=messages, tools=TOOLS, tool_choice="auto",
            temperature=0.1, max_tokens=1200)
        msg = resp.choices[0].message
        calls = getattr(msg, "tool_calls", None)
        if calls:
            messages.append({
                "role": "assistant", "content": msg.content or "",
                "tool_calls": [{"id": c.id, "type": "function",
                                "function": {"name": c.function.name,
                                             "arguments": c.function.arguments}} for c in calls]})
            for c in calls:
                try:
                    args = json.loads(c.function.arguments or "{}")
                except Exception:
                    args = {}
                out = _run_tool(c.function.name, args)
                trace.append({"tool": c.function.name, "args": args, "result": out})
                messages.append({"role": "tool", "tool_call_id": c.id,
                                 "content": json.dumps(out, ensure_ascii=False)})
            continue
        return _parse_json(msg.content or "")
    raise RuntimeError("max_steps reached without a final answer")


def _save_run(result: Dict[str, Any], text: str, building_id: int) -> bool:
    try:
        with get_db() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    building_id INTEGER NOT NULL DEFAULT 1,
                    agent TEXT NOT NULL,
                    input_text TEXT NOT NULL,
                    provider TEXT,
                    model TEXT,
                    tool_calls INTEGER NOT NULL DEFAULT 0,
                    latency_ms INTEGER,
                    success INTEGER NOT NULL,
                    trace_json TEXT,
                    output_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );""")
            conn.execute(
                "INSERT INTO agent_runs (building_id, agent, input_text, provider, model, tool_calls,"
                " latency_ms, success, trace_json, output_json) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (building_id, AGENT_NAME, text, result.get("provider"), result.get("model"),
                 result.get("tool_calls", 0), result.get("latency_ms"),
                 1 if result.get("success") else 0,
                 json.dumps(result.get("trace", []), ensure_ascii=False),
                 json.dumps({k: v for k, v in result.items() if k != "trace"}, ensure_ascii=False)))
            commit = getattr(conn, "commit", None)
            if callable(commit):
                commit()
        return True
    except Exception as exc:
        logger.warning("agent_runs insert failed: %s", exc)
        return False


# ------------------------------------------------------------------ public API
def run_order_orchestrator(message: str, building_id: int = 1,
                           history: Optional[List[Dict[str, str]]] = None,
                           max_steps: int = 4, save: bool = True) -> Dict[str, Any]:
    started = time.time()
    text = (message or "").strip()
    if not text:
        return {"success": False, "agent": AGENT_NAME, "error": "empty message"}

    client = get_client()
    if client is None:
        return {"success": False, "agent": AGENT_NAME, "provider": None,
                "error": "GROQ_API_KEY is not configured. The orchestrator needs a real LLM "
                         "and does not fake answers without one."}

    base: List[Dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    for h in (history or [])[-10:]:
        if h.get("role") in ("user", "assistant") and h.get("content"):
            base.append({"role": h["role"], "content": h["content"]})
    base.append({"role": "user", "content": text})

    final, used_model, errors = None, None, []
    trace: List[Dict[str, Any]] = []
    for model in _candidate_models():
        trace.clear()
        try:
            final = _tool_loop(client, model, list(base), trace, max_steps)
            used_model = model
            break
        except Exception as exc:
            errors.append(f"{model}: {str(exc)[:120]}")

    if final is None:
        result = {"success": False, "agent": AGENT_NAME, "provider": "groq",
                  "error": "all models failed", "details": errors,
                  "latency_ms": int((time.time() - started) * 1000)}
        result["run_saved"] = _save_run(result, text, building_id) if save else False
        return result

    def last(tool: str):
        for t in reversed(trace):
            if t["tool"] == tool and "error" not in t["result"]:
                return t["result"]
        return None

    pricing, priority = last("lookup_prices"), last("classify_priority")
    intent = final.get("intent", "order")
    items = final.get("items") or []

    # safety net: an order must never be shown without prices from the tool
    if intent == "order" and items and pricing is None:
        pricing = lookup_prices(items)
        trace.append({"tool": "lookup_prices", "args": {"items": items},
                      "result": pricing, "forced": True})
    if priority is None:
        priority = classify_priority(text)
        trace.append({"tool": "classify_priority", "args": {"text": text},
                      "result": priority, "forced": True})

    result = {
        "success": True, "agent": AGENT_NAME, "intent": intent,
        "reply": final.get("reply", ""),
        "items": pricing["lines"] if pricing else items,
        "pricing": pricing, "urgency": priority["urgency"],
        "urgency_reasons": priority["reasons"],
        "needs_clarification": final.get("needs_clarification"),
        "requires_confirmation": intent == "order",
        "provider": "groq", "model": used_model,
        "tool_calls": len(trace), "trace": trace,
        "latency_ms": int((time.time() - started) * 1000),
    }
    result["run_saved"] = _save_run(result, text, building_id) if save else False
    return result


if __name__ == "__main__":  # pragma: no cover
    out = run_order_orchestrator(" ".join(sys.argv[1:]) or "هاتلي ٢ لبن وعيش سخن", save=False)
    print(json.dumps(out, ensure_ascii=False, indent=2))
