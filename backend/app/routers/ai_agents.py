from fastapi import APIRouter, HTTPException
from app.core.database import get_db
from app.schemas.models import AIAgentInvokeRequest, AIAgentChatRequest
from app.ai.ai_agents_engine import AI_AGENTS_CATALOG, run_ai_agent
from app.ai.groq_agent import run_groq_order_parser_agent

router = APIRouter(prefix="/api/ai-agents", tags=["15. 15 AI Agents Hub API (محرك وكلاء الذكاء الاصطناعي الـ ١٥)"])


@router.get("")
def list_all_15_ai_agents():
    """[API #15] استعراض قائمة وكلاء الذكاء الاصطناعي الـ ١٥ ومهام كل وكيل."""
    return {
        "total_agents": len(AI_AGENTS_CATALOG),
        "agents": AI_AGENTS_CATALOG,
    }


@router.post("/invoke")
def invoke_specific_ai_agent(payload: AIAgentInvokeRequest):
    """تشغيل أي وكيل من الـ 15 AI Agents مباشرة وإرجاع المخرجات المهيكلة والتوصية."""
    valid_ids = {a["id"] for a in AI_AGENTS_CATALOG}
    if payload.agent_id not in valid_ids:
        raise HTTPException(status_code=404, detail=f"الوكيل غير موجود. اختر من: {sorted(valid_ids)}")
    return run_ai_agent(
        agent_id=payload.agent_id,
        prompt=payload.prompt,
        building_id=payload.building_id,
        context=payload.context,
    )


@router.post("/chat")
def chat_with_bawab_ai_agent(payload: AIAgentChatRequest):
    """
    [AI Chat Endpoint] التحدث التفاعلي مع «عم عبد السميع - البيه البواب الذكي» المدعوم بـ Groq API (LLaMA 3.3).
    يحلل النص بالعامية المصرية ويستخرج تفاصيل الطلب والتكلفة والإكرامية ويرد برد ودود مهذب.
    """
    ai_result = run_groq_order_parser_agent(
        prompt=payload.message,
        building_id=payload.building_id,
        history=payload.history,
        api_key_override=payload.groq_api_key,
    )

    # تسجيل المحادثة في قاعدة البيانات
    try:
        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO ai_agent_logs (building_id, agent_id, agent_name_ar, input_query, output_summary, confidence_score)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (
                    payload.building_id,
                    "agent_01_order_parser",
                    "عم عبد السميع الذكي (Groq Agent)",
                    payload.message,
                    ai_result.get("reply", "")[:250],
                    ai_result.get("confidence", 0.98),
                ),
            )
    except Exception:
        pass

    return ai_result


@router.get("/logs/{building_id}")
def get_ai_agent_execution_logs(building_id: int = 1):
    """عرض سجل العمليات الذكية التي نفذها الـ 15 AI Agents في العمارة."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM ai_agent_logs WHERE building_id = ? ORDER BY created_at DESC LIMIT 30;",
            (building_id,),
        ).fetchall()
        return [dict(r) for r in rows]

