# -*- coding: utf-8 -*-
"""
Evaluation for the order agents.

Compares what an agent returns against hand-written expectations in
orders_cases.jsonl (one JSON object per line):
  {"id": 1, "text": "...", "expect": {
      "intent": "order" | ["order","other"],   # optional (str or list of accepted values)
      "items": ["لبن", ...],                    # optional, expected item names
      "forbidden": ["لبن"],                     # optional, items that must NOT appear
      "urgency": "urgent" | "normal",           # optional
      "clarify": true | false }}                # optional, is a clarifying question expected

Run from the backend folder (PYTHONPATH must be the backend folder):
    python eval\\run_eval.py                 # Order Orchestrator (needs GROQ_API_KEY)
    python eval\\run_eval.py --limit 5       # first 5 cases only
    python eval\\run_eval.py --baseline      # old rules-based parser (no LLM), items/urgency only
    python eval\\run_eval.py --delay 4       # slower, if Groq answers with 429 rate limits
"""
import argparse
import json
import os
import sys
import time
from typing import Any, Callable, Dict, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))  # backend folder
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.ai.orchestrator import _norm, run_order_orchestrator  # noqa: E402


# ----------------------------------------------------------------- scoring
def item_matches(expected: str, names: List[str]) -> bool:
    e = _norm(expected)
    for n in names:
        n = _norm(n)
        if e and n and (e in n or (len(n) >= 2 and n in e)):
            return True
    return False


def score_case(expect: Dict[str, Any], got: Dict[str, Any], baseline: bool = False) -> Dict[str, Any]:
    """Returns {check_name: True/False} only for the checks the case defines."""
    checks: Dict[str, Any] = {}
    names = got.get("items", [])

    if "intent" in expect and not baseline:
        accepted = expect["intent"] if isinstance(expect["intent"], list) else [expect["intent"]]
        checks["intent"] = got.get("intent") in accepted

    if expect.get("items"):
        hit = [item_matches(e, names) for e in expect["items"]]
        checks["item_hits"] = sum(hit)
        checks["item_expected"] = len(hit)
        extra = [n for n in names if not any(item_matches(e, [n]) for e in expect["items"])]
        checks["item_extra"] = len(extra)
        checks["item_returned"] = len(names)

    if expect.get("forbidden"):
        checks["forbidden_ok"] = not any(item_matches(f, names) for f in expect["forbidden"])

    if "urgency" in expect:
        checks["urgency"] = got.get("urgency") == expect["urgency"]

    if expect.get("clarify") is not None and not baseline:
        checks["clarify"] = bool(got.get("needs_clarification")) == bool(expect["clarify"])
    return checks


def case_failed(checks: Dict[str, Any]) -> List[str]:
    bad = [k for k in ("intent", "urgency", "clarify", "forbidden_ok") if checks.get(k) is False]
    if checks.get("item_expected") and checks.get("item_hits") != checks.get("item_expected"):
        bad.append("items_missing")
    if checks.get("item_extra"):
        bad.append("items_extra")
    return bad


def summarize(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    def rate(key):
        vals = [r["checks"][key] for r in rows if key in r["checks"]]
        return (sum(vals) / len(vals), len(vals)) if vals else (None, 0)

    hits = sum(r["checks"].get("item_hits", 0) for r in rows)
    expected = sum(r["checks"].get("item_expected", 0) for r in rows)
    extra = sum(r["checks"].get("item_extra", 0) for r in rows)
    returned = sum(r["checks"].get("item_returned", 0) for r in rows)
    ok_rows = [r for r in rows if r["got"].get("success")]
    return {
        "cases": len(rows),
        "failed_calls": len(rows) - len(ok_rows),
        "intent": rate("intent"),
        "urgency": rate("urgency"),
        "clarify": rate("clarify"),
        "forbidden_ok": rate("forbidden_ok"),
        "item_recall": (hits / expected if expected else None, expected),
        "item_precision": ((returned - extra) / returned if returned else None, returned),
        "avg_latency_ms": (sum(r["got"].get("latency_ms", 0) for r in ok_rows) / len(ok_rows)) if ok_rows else None,
        "avg_tool_calls": (sum(r["got"].get("tool_calls", 0) for r in ok_rows) / len(ok_rows)) if ok_rows else None,
    }


def evaluate(run_fn: Callable[[str], Dict[str, Any]], cases: List[Dict[str, Any]],
             delay: float = 2.0, baseline: bool = False) -> List[Dict[str, Any]]:
    rows = []
    for i, case in enumerate(cases):
        got = run_fn(case["text"])
        checks = score_case(case["expect"], got, baseline) if got.get("success") else {}
        rows.append({"id": case["id"], "text": case["text"], "expect": case["expect"],
                     "got": got, "checks": checks})
        if delay and i < len(cases) - 1:
            time.sleep(delay)
    return rows


# ---------------------------------------------------------------- adapters
def orchestrator_runner(text: str) -> Dict[str, Any]:
    res = run_order_orchestrator(text, save=False)
    if not res.get("success"):
        return {"success": False, "error": res.get("error"), "details": res.get("details")}
    return {"success": True, "intent": res.get("intent"),
            "items": [i.get("name", "") for i in res.get("items", [])],
            "urgency": res.get("urgency"), "needs_clarification": res.get("needs_clarification"),
            "latency_ms": res.get("latency_ms", 0), "tool_calls": res.get("tool_calls", 0)}


def baseline_runner(text: str) -> Dict[str, Any]:
    from app.ai.groq_agent import fallback_egyptian_parser
    start = time.time()
    try:
        res = fallback_egyptian_parser(text)
    except Exception as exc:
        return {"success": False, "error": str(exc)}
    data = res.get("structured_data") if isinstance(res.get("structured_data"), dict) else res
    items = data.get("items") or res.get("items") or []
    return {"success": True,
            "items": [i.get("name", "") if isinstance(i, dict) else str(i) for i in items],
            "urgency": data.get("urgency") or res.get("urgency"),
            "latency_ms": int((time.time() - start) * 1000), "tool_calls": 0}


# --------------------------------------------------------------------- main
def fmt(pair) -> str:
    value, n = pair
    return "n/a" if value is None else f"{value * 100:5.1f}%  (n={n})"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default=os.path.join(HERE, "orders_cases.jsonl"))
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--delay", type=float, default=2.0)
    ap.add_argument("--baseline", action="store_true")
    args = ap.parse_args()

    with open(args.cases, encoding="utf-8") as f:
        cases = [json.loads(line) for line in f if line.strip()]
    if args.limit:
        cases = cases[:args.limit]

    mode = "baseline_rules" if args.baseline else "orchestrator"
    rows = evaluate(baseline_runner if args.baseline else orchestrator_runner,
                    cases, 0 if args.baseline else args.delay, args.baseline)
    s = summarize(rows)

    print(f"\n=== {mode}: {s['cases']} cases, {s['failed_calls']} failed calls ===")
    if not args.baseline:
        print(f"intent accuracy   : {fmt(s['intent'])}")
        print(f"clarify accuracy  : {fmt(s['clarify'])}")
    print(f"urgency accuracy  : {fmt(s['urgency'])}")
    print(f"item recall       : {fmt(s['item_recall'])}")
    print(f"item precision    : {fmt(s['item_precision'])}")
    print(f"forbidden ok      : {fmt(s['forbidden_ok'])}")
    if s["avg_latency_ms"] is not None:
        print(f"avg latency       : {s['avg_latency_ms']:.0f} ms, avg tool calls {s['avg_tool_calls']:.1f}")

    if args.baseline and not any(r["got"].get("items") for r in rows):
        print("\nWARNING: the baseline returned no items in any case; its output format was probably "
              "not recognized by this script. Ignore the baseline numbers.")

    print("\n--- cases that need a look ---")
    for r in rows:
        if not r["got"].get("success"):
            print(f"#{r['id']} CALL FAILED: {r['got'].get('error')} {r['got'].get('details') or ''}")
            continue
        bad = case_failed(r["checks"])
        if bad:
            print(f"#{r['id']} {r['text']}\n    problems: {', '.join(bad)} | "
                  f"got intent={r['got'].get('intent')} urgency={r['got'].get('urgency')} "
                  f"items={r['got'].get('items')} clarify={bool(r['got'].get('needs_clarification'))}")

    out = os.path.join(HERE, f"results_{mode}.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print(f"\nfull details saved to {out}")


if __name__ == "__main__":
    main()
