# -*- coding: utf-8 -*-
"""Offline tests for the Order Orchestrator. No API key or network needed:
the LLM is replaced by a scripted fake client."""
import json
from types import SimpleNamespace

import pytest

from app.ai import orchestrator as orch


def tool_call(call_id, name, args):
    return SimpleNamespace(id=call_id, function=SimpleNamespace(
        name=name, arguments=json.dumps(args, ensure_ascii=False)))


def llm_msg(content="", tool_calls=None):
    return SimpleNamespace(content=content, tool_calls=tool_calls)


class FakeClient:
    def __init__(self, script):
        self.script = list(script)
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return SimpleNamespace(choices=[SimpleNamespace(message=item)])


@pytest.fixture(autouse=True)
def price_table(monkeypatch):
    monkeypatch.setattr(orch, "_prices", lambda: {"لبن": 30.0, "عيش": 5.0, "أنبوبة": 200.0})


def test_unknown_item_is_never_priced():
    res = orch.lookup_prices([{"name": "لبن جهينة", "quantity": 2},
                              {"name": "حاجة غريبة", "quantity": 1}])
    assert res["known_total_egp"] == 60.0
    assert res["unknown_items"] == ["حاجة غريبة"]
    assert res["is_complete"] is False
    assert res["lines"][1]["unit_price_egp"] is None


def test_arabic_digit_quantity_and_heavy_tip():
    res = orch.lookup_prices([{"name": "أنبوبة", "quantity": "٢"}])
    assert res["known_total_egp"] == 400.0
    assert res["suggested_tip_egp"] == 35.0


def test_priority_rules():
    assert orch.classify_priority("عايز بنادول بسرعة")["urgency"] == "urgent"
    assert orch.classify_priority("عايز لبن")["urgency"] == "normal"


def test_full_tool_calling_flow(monkeypatch):
    final = {"intent": "order", "reply": "تحت أمرك يا باشا",
             "items": [{"name": "لبن", "quantity": 2}], "needs_clarification": None}
    client = FakeClient([
        llm_msg(tool_calls=[
            tool_call("1", "lookup_prices", {"items": [{"name": "لبن", "quantity": 2}]}),
            tool_call("2", "classify_priority", {"text": "هاتلي ٢ لبن"})]),
        llm_msg(content=json.dumps(final, ensure_ascii=False)),
    ])
    monkeypatch.setattr(orch, "get_client", lambda: client)
    res = orch.run_order_orchestrator("هاتلي ٢ لبن", save=False)
    assert res["success"] is True
    assert res["pricing"]["known_total_egp"] == 60.0
    assert res["tool_calls"] == 2
    assert res["requires_confirmation"] is True
    assert not any(t.get("forced") for t in res["trace"])


def test_prices_are_forced_when_model_skips_the_tool(monkeypatch):
    final = {"intent": "order", "reply": "حاضر",
             "items": [{"name": "عيش", "quantity": 10}], "needs_clarification": None}
    monkeypatch.setattr(orch, "get_client",
                        lambda: FakeClient([llm_msg(content=json.dumps(final, ensure_ascii=False))]))
    res = orch.run_order_orchestrator("هاتلي عيش", save=False)
    assert res["pricing"]["known_total_egp"] == 50.0
    assert any(t.get("forced") for t in res["trace"])


def test_emergency_is_not_an_order(monkeypatch):
    final = {"intent": "emergency", "reply": "اضغط زر الطوارئ فوراً",
             "items": [], "needs_clarification": None}
    monkeypatch.setattr(orch, "get_client",
                        lambda: FakeClient([llm_msg(content=json.dumps(final, ensure_ascii=False))]))
    res = orch.run_order_orchestrator("في ريحة غاز", save=False)
    assert res["intent"] == "emergency"
    assert res["requires_confirmation"] is False
    assert res["pricing"] is None


def test_no_api_key_is_reported_honestly(monkeypatch):
    monkeypatch.setattr(orch, "get_client", lambda: None)
    res = orch.run_order_orchestrator("هاتلي لبن", save=False)
    assert res["success"] is False
    assert "GROQ_API_KEY" in res["error"]


def test_falls_back_to_next_model_then_fails_cleanly(monkeypatch):
    boom = [RuntimeError("model gone")] * len(orch._candidate_models())
    monkeypatch.setattr(orch, "get_client", lambda: FakeClient(boom))
    res = orch.run_order_orchestrator("هاتلي لبن", save=False)
    assert res["success"] is False
    assert len(res["details"]) == len(orch._candidate_models())


def test_run_is_saved_to_agent_runs(monkeypatch):
    import sqlite3
    from contextlib import contextmanager
    conn = sqlite3.connect(":memory:")

    @contextmanager
    def fake_db():
        yield conn

    final = {"intent": "order", "reply": "حاضر", "items": [{"name": "لبن", "quantity": 1}],
             "needs_clarification": None}
    monkeypatch.setattr(orch, "get_db", fake_db)
    monkeypatch.setattr(orch, "get_client",
                        lambda: FakeClient([llm_msg(content=json.dumps(final, ensure_ascii=False))]))
    res = orch.run_order_orchestrator("هاتلي لبن", save=True)
    assert res["run_saved"] is True
    row = conn.execute("SELECT agent, success, tool_calls FROM agent_runs").fetchone()
    assert row == ("order_orchestrator", 1, 2)
