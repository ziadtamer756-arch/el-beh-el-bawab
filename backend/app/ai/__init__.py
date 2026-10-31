# -*- coding: utf-8 -*-
"""
AI Engine & Agents Hub for «El-Beh El-Bawab» (البيه البواب).
Contains:
- groq_agent: Real-time inference using Groq API + OpenAI SDK (openai/gpt-oss-20b or llama-3.3-70b-versatile).
- ai_agents_engine: Catalog & execution engine for all 15 building AI agents.
- prompts: Egyptian dialect system prompts & personas.
"""

from app.ai.groq_agent import run_groq_order_parser_agent, get_client
from app.ai.ai_agents_engine import AI_AGENTS_CATALOG, run_ai_agent
from app.ai.prompts import BAWAB_SYSTEM_PROMPT

__all__ = [
    "run_groq_order_parser_agent",
    "get_client",
    "AI_AGENTS_CATALOG",
    "run_ai_agent",
    "BAWAB_SYSTEM_PROMPT",
]
