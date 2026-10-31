# -*- coding: utf-8 -*-
"""
AI Package for «El-Beh El-Bawab» (البيه البواب).
This folder exposes the AI Agents, Groq API verification, and prompts.
"""
import sys
import os

# Add backend directory to sys.path if not present
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

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
