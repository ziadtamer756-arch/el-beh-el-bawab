"""
Groq AI Agent Engine for «El-Beh El-Bawab» (البيه البواب).
Uses OpenAI SDK pointed to Groq's high-speed inference endpoint:
- Base URL: https://api.groq.com/openai/v1
- Model: llama-3.3-70b-versatile (or llama-3.1-8b-instant)
- Native Egyptian Dialect & Real-Time Concierge Agent.
"""
import os
import json
import time
import re
from typing import Dict, Any, List, Optional
from openai import OpenAI
from app.core.config import GROQ_API_KEY, GROQ_MODEL

GROQ_BASE_URL = "https://api.groq.com/openai/v1"

SYSTEM_PROMPT = """أنت «عم عبد السميع - البيه البواب الذكي»، المساعد الشخصي وبواب عمارة النيل بالدقي في مصر.
تتحدث باللهجة المصرية الودودة المحترمة والأصيلة («يا باشا»، «عنيا يا فندم»، «من عنيا الاتنين»، «حاضر فوراً»، «يا بيه»).

قواعد الذاكرة وتراكم الطلبات (CRITICAL ORDER ACCUMULATION & MEMORY):
1. لديك ذاكرة ذكية وتراكمية كاملة لكل المحادثة الجارية. إذا كان الساكن قد طلب أصنافاً في رسائل سابقة في المحادثة، ثم أضاف طلباً جديداً (مثل: «وهاتلي كمان...»، «وضيف عليهم...»، «معلش نسيت كذا»، أو ذكر صنفاً جديداً)، يجب عليك الاحتفاظ بكافة الأصناف السابقة وتجميع الصنف الجديد معها في مصفوفة items، وحساب إجمالي التكلفة التراكمية المجمعة لكل الأصناف معاً!
2. لا تمسح أو تتجاهل أبداً الأصناف السابقة إلا إذا طلب الساكن صراحةً الحذف أو الاستبدال (مثل: «شيل العيش» أو «بدل كذا بكذا»).
3. إذا ذكر الساكن سعراً معيناً لصنف (مثل: «اللبن بـ 30 جنيه» أو «عيش بـ 10»)، التزم بالسعر الذي حدده الساكن فوراً ولا تغيره!
4. في حقل reply: اذكر رداً مصرياً ودوداً يوضح ملخصاً شاملاً لما تم قيده حتى الآن (الموجود سابقاً + المضاف حديثاً)، وإجمالي الحساب، ليبعث الطمأنينة للساكن.

مهامك الأساسية:
1. فهم طلبات السكان بالعامية المصرية بدقة (سوبرماركت، عيش، صيدلية، سباكة، كهرباء، غسيل سيارات، طرود، طوارئ).
2. استخراج الأصناف والكميات والأسعار بالجنيه المصري (EGP) وتحديد نوع الطلب (category) ودرجة الأهمية (urgency).
3. اقتراح إكرامية عادلة (suggested_tip_egp) بحسب ثقل المشوار وعدد الأصناف.

يجب أن ترد دائماً بصيغة JSON حصراً بالشكل التالي:
{
  "intent": "order",
  "reply": "الرد المصري الودود من عم عبد السميع موضحاً كافة الأصناف المتراكمة وإجمالي التكلفة",
  "category": "groceries" | "pharmacy" | "errand" | "cleaning" | "car_wash" | "plumbing_electrical" | "luggage_help" | "other",
  "title": "عنوان موجز وشامل لكل طلبات الساكن الحالية",
  "urgency": "normal" | "urgent" | "scheduled",
  "items": [
    {"name": "اسم الصنف", "quantity": "الكمية", "estimated_price_egp": 25.0, "category": "groceries"}
  ],
  "estimated_total_cost_egp": 120.0,
  "suggested_tip_egp": 20.0,
  "action_recommendation": "توصية سريعة قابلة للتنفيذ"
}
"""

def get_client(api_key: Optional[str] = None) -> Optional[OpenAI]:
    key = api_key or os.getenv("GROQ_API_KEY") or GROQ_API_KEY
    if not key:
        return None
    return OpenAI(base_url=GROQ_BASE_URL, api_key=key, timeout=12.0)


def run_groq_order_parser_agent(
    prompt: str,
    building_id: int = 1,
    context: Optional[Dict[str, Any]] = None,
    history: Optional[List[Dict[str, str]]] = None,
    api_key_override: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Real working AI Agent powered by Groq API + OpenAI SDK.
    Parses natural Egyptian dialect and acts as smart concierge agent.
    Falls back gracefully to intelligent Egyptian heuristic engine if no API key is provided.
    """
    start_time = time.time()
    client = get_client(api_key_override)
    raw_model = os.getenv("GROQ_MODEL") or GROQ_MODEL or "openai/gpt-oss-20b"
    # Normalize aliases like openai/oss-20b to the exact Groq API identifier openai/gpt-oss-20b
    if raw_model in ("openai/oss-20b", "oss-20b"):
        model_name = "openai/gpt-oss-20b"
    else:
        model_name = raw_model

    if client:
        # Priority list of models to try, starting with openai/gpt-oss-20b
        candidates = [model_name]
        for fallback_m in ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.8-27b", "allam-2-7b"]:
            if fallback_m not in candidates:
                candidates.append(fallback_m)

        last_error = None
        for cur_model in candidates:
            try:
                messages = [{"role": "system", "content": SYSTEM_PROMPT}]
                if history:
                    for h in history[-20:]:  # Full rich conversation memory context
                        r = h.get("role", "user")
                        c = h.get("content", "")
                        if r in ("user", "assistant") and c:
                            messages.append({"role": r, "content": c})

                user_msg = prompt
                if context:
                    user_msg += f"\n[سياق إضافي من العمارة: {json.dumps(context, ensure_ascii=False)}]"

                messages.append({"role": "user", "content": user_msg})

                completion = client.chat.completions.create(
                    model=cur_model,
                    messages=messages,
                    response_format={"type": "json_object"},
                    temperature=0.2,
                    max_tokens=1500,
                )
                raw_text = completion.choices[0].message.content or "{}"
                if "```" in raw_text:
                    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, re.DOTALL)
                    if match:
                        raw_text = match.group(1)
                parsed_json = json.loads(raw_text)
                latency_ms = int((time.time() - start_time) * 1000)

                return {
                    "success": True,
                    "agent_id": "agent_01_order_parser",
                    "agent_name_ar": f"عم عبد السميع الذكي ({cur_model})",
                    "provider": "groq",
                    "model": cur_model,
                    "latency_ms": latency_ms,
                    "reply": parsed_json.get("reply", "عيوني يا فندم، الطلب وصل وهبدأ فيه فوراً."),
                    "structured_data": parsed_json,
                    "confidence": 0.98,
                    "summary_ar": f"تم استخراج {len(parsed_json.get('items', []))} أصناف بتكلفة تقريبية {parsed_json.get('estimated_total_cost_egp', 0)} ج.م",
                    "action_recommendation": parsed_json.get("action_recommendation", "اضغط تأكيد الطلب لإرساله للبواب فوراً."),
                }
            except Exception as e:
                last_error = e
                continue

        # If all Groq models failed, fallback to local Egyptian heuristic engine
        res = fallback_egyptian_parser(prompt, building_id, context)
        res["provider"] = "local_heuristics_fallback"
        res["notice"] = f"تم الاستعانة بمحرك القواعد المحلي (ملاحظة الاتصال بـ Groq: {str(last_error)[:100]})"
        res["latency_ms"] = int((time.time() - start_time) * 1000)
        return res

    # If no Groq API Key is configured yet, use our rich Egyptian heuristic parser
    res = fallback_egyptian_parser(prompt, building_id, context)
    res["provider"] = "local_heuristics"
    res["notice"] = "يعمل بنظام القواعد الفوري. لإجراء الاتصال الحي مع LLaMA 3.3، يرجى إضافة GROQ_API_KEY في ملف .env"
    res["latency_ms"] = int((time.time() - start_time) * 1000)
    return res


def fallback_egyptian_parser(prompt: str, building_id: int = 1, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    High-fidelity offline Egyptian dialect heuristic engine.
    Ensures zero downtime and immediate sensible responses even without internet or API keys.
    """
    clean = (prompt or "").strip()
    lowered = clean.lower()

    # Egyptian grocery catalog with current market prices
    CATALOG = [
        (r"(?:لبن|حليب)(?:\s+جهينة|\s+بخيره)?", "لبن جهينة ١ لتر", 42.0, "groceries"),
        (r"(?:كرتونة|طبق)\s*بيض(?:\s+أحمر|\s+أبيض)?", "طبق بيض (٣٠ بيضة)", 165.0, "groceries"),
        (r"(?:عيش|خبز)(?:\s+بلدي|\s+سخن|\s+سياحي|\s+فينو)?", "عيش سخن من الفرن", 20.0, "groceries"),
        (r"(?:كيلو\s*)?سكر(?:\s+الأسرة|\s+أبيض)?", "كيلو سكر أبيض", 36.0, "groceries"),
        (r"(?:شاي|باكو\s*شاي)(?:\s+العروسة|\s+ليبتون)?", "شاي العروسة (ربع كيلو)", 55.0, "groceries"),
        (r"(?:زجاجة|إزازة\s*)?زيت(?:\s+ذرة|\s+عباد|\s+قلية)?", "زيت نباتي ممتاز", 68.0, "groceries"),
        (r"(?:بنادول|باراسيتامول|مسكن|أوجمنتين|دواء|صيدلية)", "أدوية ومستلزمات صيدلية", 85.0, "pharmacy"),
        (r"(?:سباكة|حنفية|تسريب|فلتر|ماسورة|حوض)", "صيانة سباكة ومستلزمات عزل", 120.0, "plumbing_electrical"),
        (r"(?:كهرباء|لمبة|مفتاح|فيشة|قاطع)", "مستلزمات صيانة كهربائية", 75.0, "plumbing_electrical"),
        (r"(?:غسيل|عربية|سيارة|باكية|جراج)", "خدمة غسيل وتلميع سيارة", 60.0, "car_wash"),
        (r"(?:طرد|أمازون|نون|شحنة|مندوب|استلام)", "استلام طرد وتأمين خزينة البوابة", 0.0, "errand"),
    ]

    extracted_items = []
    total_cost = 0.0
    category = "groceries"
    urgency = "normal"

    if any(w in lowered for w in ["بسرعة", "ضروري", "طوارئ", "حالاً", "مستعجل", "دلوقتي"]):
        urgency = "urgent"

    # Check for explicit budget like "بـ 10 جنيه" or "ب 10" or "ب15 جنيه"
    budget_match = re.search(r"ب(?:ـ|\s*)?(\d+)(?:\s*جنيه|\s*ج\.م)?", clean)
    custom_budget = float(budget_match.group(1)) if budget_match else None

    for pattern, name, price, cat in CATALOG:
        match = re.search(pattern, clean)
        if match:
            # check for quantity like "٢ لبن" or "10 عيش"
            prefix_match = re.search(r"(\d+|٢|واحد|اتنين|ثلاثة|عشرة)\s*" + pattern, clean)
            qty = "١"
            multiplier = 1
            if prefix_match:
                q_text = prefix_match.group(1)
                if q_text in ("٢", "اتنين", "2"):
                    qty = "٢"
                    multiplier = 2
                elif q_text in ("10", "١٠", "عشرة"):
                    qty = "١٠"
                    multiplier = 10
                elif q_text.isdigit():
                    multiplier = max(1, int(q_text))
                    qty = str(multiplier)

            item_cost = custom_budget if (custom_budget and "عيش" in name) else (price * (multiplier if cat != "groceries" or "طبق" not in name else 1))
            if custom_budget and "عيش" in name:
                qty = f"بقيمة {int(custom_budget)} ج.م"

            extracted_items.append({
                "name": name,
                "quantity": qty,
                "estimated_price_egp": item_cost,
                "category": cat
            })
            total_cost += item_cost
            category = cat

    if not extracted_items:
        extracted_items.append({
            "name": clean[:35] if clean else "مشوار / طلب عام",
            "quantity": "١",
            "estimated_price_egp": 50.0,
            "category": "errand"
        })
        total_cost = 50.0
        category = "errand"

    tip = 15.0
    if urgency == "urgent":
        tip += 10.0
    if total_cost > 200.0:
        tip += 15.0

    # Egyptian friendly bawab reply
    if category == "pharmacy":
        reply = "ألف سلامة يا باشا، هجري على الصيدلية حالاً وأجيب العلاج فوراً وأطلعه لحضرتك! 💊🛎️"
        title = "طلب عاجل من الصيدلية"
    elif category == "plumbing_electrical":
        reply = "يا فندم متقلقش خالص، هقفل المحبس العمومي وأطلع لحضرتك فوراً بالعدة ونعاين التسريب! 🔧🛎️"
        title = "طلب صيانة منزلية عاجلة"
    elif category == "car_wash":
        reply = "عنيا يا باشا، هغسلك العربية في الباكية وألمعها وتبقى بتلمع قبل ما تنزل الصبح! 🚗✨"
        title = "غسيل سيارة بالجراج"
    else:
        item_names_str = " و".join([i["name"] for i in extracted_items[:2]])
        reply = f"يا مرحب يا بيه، عيوني ليك! هجيبلك {item_names_str} طازة من أحسن مكان، ورشة ملح ويكونوا عند باب شقتك! 🛎️🥖"
        title = f"طلب {category}"

    return {
        "success": True,
        "agent_id": "agent_01_order_parser",
        "agent_name_ar": "وكيل تحليل الطلبات باللهجة المصرية",
        "reply": reply,
        "confidence": 0.95,
        "summary_ar": f"تم استخراج {len(extracted_items)} أصناف بتكلفة تقريبية {total_cost} ج.م",
        "structured_data": {
            "intent": "order",
            "title": title,
            "category": category,
            "urgency": urgency,
            "items": extracted_items,
            "estimated_total_cost_egp": total_cost,
            "suggested_tip_egp": tip,
            "action_recommendation": "اضغط «تأكيد الطلب» لإرساله مباشرة لعم عبد السميع وقيده في قائمة المهام.",
        },
        "action_recommendation": "اضغط «تأكيد الطلب» لإرساله مباشرة لعم عبد السميع وقيده في قائمة المهام.",
    }
