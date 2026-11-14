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
from typing import Dict, Any, List, Optional, Tuple
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


_AR_DIGIT_TO_WESTERN = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
_QTY_WORD_TO_N = {
    "واحد": 1, "واحدة": 1,
    "اتنين": 2, "اثنين": 2,
    "تلات": 3, "تلاتة": 3, "تلاته": 3, "ثلاثة": 3,
    "أربعة": 4, "اربعة": 4,
    "خمسة": 5, "ستة": 6, "سبعة": 7, "ثمانية": 8, "تسعة": 9, "عشرة": 10,
}
_QTY_WORDS_ALT = "|".join(sorted(_QTY_WORD_TO_N, key=len, reverse=True))
_QTY_BEFORE_RE = re.compile(
    rf"(?:(?P<digit>[0-9]+|[٠-٩]+)|(?P<word>{_QTY_WORDS_ALT}))"
    rf"(?:\s*(?:كيلو|لتر|علبة))?\s*$"
)
_NEGATION_BEFORE_RE = re.compile(r"مش\s*عايز(?:ش)?\s*$")
_ORDER_VERB_RE = re.compile(r"هات(?:لي|ي)?|جيب(?:لي)?|عايز|محتاج|نسيت")
_GREETING_RE = re.compile(r"صباح الخير|مساء الخير|السلام عليكم|ازيك|إزيك|عامل إيه|أهلا")
_EMERGENCY_RE = re.compile(
    r"حريق|ريحة\s*غاز|أسانسير|اسانسير|مصعد|محبوس|وقع|مش\s*بيتحرك"
)
_LEAK_RE = re.compile(r"تسريب")
_VAGUE_NEED_RE = re.compile(r"هات(?:لي|ي)?\s+حاجة|عايز\s+حاجة|جيب(?:لي)?\s+حاجة")
_URGENT_MARKERS = ("بسرعة", "ضروري", "طوارئ", "حالاً", "حالا", "مستعجل", "دلوقتي", "فوراً", "فورا")


def _qty_before_item(text: str, item_start: int) -> Tuple[int, Optional[str]]:
    """Return an explicit quantity, or None when the user did not specify one."""
    window = text[max(0, item_start - 28):item_start]
    match = _QTY_BEFORE_RE.search(window)
    if not match:
        return 0, None

    if match.group("digit"):
        n = int(match.group("digit").translate(_AR_DIGIT_TO_WESTERN))
    else:
        n = _QTY_WORD_TO_N[match.group("word")]

    if n <= 0:
        return 0, None

    return n, str(n)


def _fallback_non_order(
    intent: str,
    urgency: str,
    reply: str,
    title: str,
    needs_clarification: bool,
) -> Dict[str, Any]:
    action = "وضّح الطلب لو حابب أبعت لعم عبد السميع." if needs_clarification else "لا يوجد طلب شراء جاهز للتأكيد."
    return {
        "success": True,
        "agent_id": "agent_01_order_parser",
        "agent_name_ar": "وكيل تحليل الطلبات باللهجة المصرية",
        "reply": reply,
        "confidence": 0.6,
        "summary_ar": title,
        "structured_data": {
            "intent": intent,
            "title": title,
            "category": "other",
            "urgency": urgency,
            "items": [],
            "estimated_total_cost_egp": 0.0,
            "suggested_tip_egp": 0.0,
            "needs_clarification": needs_clarification,
            "action_recommendation": action,
        },
        "action_recommendation": action,
    }


def fallback_egyptian_parser(
    prompt: str,
    building_id: int = 1,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Offline Egyptian Arabic order parser. Never invents prices or actions."""
    clean = (prompt or "").strip()
    urgency = "urgent" if any(w in clean for w in _URGENT_MARKERS) else "normal"

    if re.search(r"أدوية|دواء|صيدلية|بنادول", clean):
        urgency = "urgent"

    if _EMERGENCY_RE.search(clean):
        return _fallback_non_order(
            "emergency",
            "urgent",
            "ده بلاغ طوارئ. برجاء التواصل مع الطوارئ وإبلاغ أمن العمارة فوراً.",
            "بلاغ طوارئ",
            False,
        )

    if _LEAK_RE.search(clean):
        return _fallback_non_order(
            "other",
            urgency,
            "وصلني بلاغ تسريب. محتاجين تسجيل بلاغ صيانة لتحديد مكان المشكلة والتعامل معاها.",
            "بلاغ صيانة / تسريب",
            False,
        )

    if _VAGUE_NEED_RE.search(clean):
        return _fallback_non_order(
            "other",
            urgency,
            "تحت أمرك. ممكن تحدد محتاج إيه بالضبط؟",
            "طلب غير محدد",
            True,
        )

    if re.search(r"(?:ألغي|الغي|الغى|إلغاء|الغاء)\s*(?:طلب)?", clean):
        return _fallback_non_order(
            "other",
            urgency,
            "فهمت إنك عايز تلغي الطلب. لم يتم إنشاء طلب شراء جديد.",
            "طلب إلغاء",
            False,
        )

    # (pattern, canonical name, category)
    # Prices are intentionally excluded: lookup_prices is the pricing authority.
    catalog = [
        (r"لبن\s+(?:أطفال|اطفال)", "لبن أطفال", "groceries"),
        (r"حفاضات|بامبرز", "حفاضات", "groceries"),
        (r"شيبسي|شيبس|شيبسات", "شيبسي", "groceries"),
        (r"بيبسي", "بيبسي", "groceries"),
        (r"ملح", "ملح", "groceries"),
        (r"فلفل", "فلفل", "groceries"),
        (r"كمون", "كمون", "groceries"),
        (r"حليب(?:\s+جهينة|\s+بخيره)?", "حليب", "groceries"),
        (r"لبن(?:\s+جهينة|\s+بخيره)?", "لبن جهينة  لتر", "groceries"),
        (r"(?:كرتونة|طبق)\s*بيض(?:\s+أحمر|\s+أبيض)?", "طبق بيض ( بيضة)", "groceries"),
        (r"(?:عيش|خبز)(?:\s+بلدي|\s+سخن|\s+سياحي|\s+فينو)?", "عيش سخن من الفرن", "groceries"),
        (r"(?:كيلو\s*)?سكر(?:\s+الأسرة|\s+أبيض)?", "كيلو سكر أبيض", "groceries"),
        (r"(?:شاي|باكو\s*شاي)(?:\s+العروسة|\s+ليبتون)?", "شاي العروسة (ربع كيلو)", "groceries"),
        (r"(?:زجاجة|إزازة\s*)?زيت(?:\s+ذرة|\s+عباد|\s+قلية)?", "زيت نباتي ممتاز", "groceries"),
        (r"(?:كيلو\s*)?(?:أرز|ارز)(?:\s+الضحى)?", "أرز", "groceries"),
        (r"مكرونة", "مكرونة", "groceries"),
        (r"طعمية", "طعمية", "groceries"),
        (r"فول", "فول", "groceries"),
        (r"أنبوبة(?:\s+بوتاجاز)?", "أنبوبة بوتاجاز", "groceries"),
        (r"جبنة(?:\s+رومي)?", "جبنة", "groceries"),
        (r"بنادول", "بنادول", "pharmacy"),
        (r"باراسيتامول|مسكن|أوجمنتين", "دواء يحتاج مراجعة", "pharmacy"),
        (r"دواء(?:\s+ال)?ضغط", "دواء الضغط", "pharmacy"),
        (r"(?:سباكة|حنفية|فلتر|ماسورة|حوض)", "طلب صيانة سباكة", "plumbing_electrical"),
        (r"(?:كهرباء|لمبة|مفتاح|فيشة|قاطع)", "طلب صيانة كهرباء", "plumbing_electrical"),
        (r"(?:غسيل|عربية|سيارة|باكية|جراج)", "خدمة غسيل سيارة", "car_wash"),
        (r"(?:طرد|أمازون|نون|شحنة|مندوب|استلام)", "استلام طرد", "errand"),
    ]

    extracted_items = []
    occupied = []
    matched_spans = []

    for pattern, name, category in catalog:
        for match in re.finditer(pattern, clean):
            start, end = match.span()

            if any(start < old_end and end > old_start for old_start, old_end in occupied):
                continue

            if _NEGATION_BEFORE_RE.search(clean[max(0, start - 20):start]):
                matched_spans.append((start, end))
                continue

            occupied.append((start, end))
            matched_spans.append((start, end))

            matched_text = clean[start:end]
            multiplier, quantity = _qty_before_item(clean, start)
            if matched_text.startswith("كيلو"):
                quantity = "1"

            extracted_items.append({
                "name": name,
                "quantity": quantity,
                "estimated_price_egp": None,
                "category": category,
            })

    # Remove recognized item spans, then inspect remaining complete words.
    residual = clean
    for start, end in sorted(matched_spans, reverse=True):
        residual = residual[:start] + " " + residual[end:]

    residual = re.sub(r"[،,.!؟?+*/:؛()\[\]-]", " ", residual)
    residual = re.sub(r"[0-9-]+", " ", residual)

    ignored_words = {
        "هاتلي", "هات", "جيبلي", "جيب", "عايز", "عاوزه", "عاوز",
        "محتاج", "محتاجه", "من", "و", "في", "ال", "لو", "سمحت",
        "ممكن", "عايزه", "مش", "واحد", "واحدة", "اتنين", "اثنين",
        "تلات", "تلاتة", "تلاته", "ثلاثة", "اربعة", "أربعة",
        "خمسة", "ستة", "سبعة", "ثمانية", "تسعة", "عشرة", "صفر",
        "كيلو", "لتر", "علبة", "حالاً", "حالا", "دلوقتي",
        "بسرعة", "ضروري", "مستعجل", "فوراً", "فورا",
        "يا", "باشا", "تكرمت",
    }

    unknown_words = [
        word for word in residual.split()
        if len(word) > 1 and word not in ignored_words
    ]

    order_signal_text = re.sub(
        r"مش\s*(?:عايز|عاوز|محتاج)(?:ش)?",
        " ",
        clean,
    )
    is_order_request = (
        bool(_ORDER_VERB_RE.search(order_signal_text))
        or bool(extracted_items)
    )

    if not is_order_request:
        return _fallback_non_order(
            "other",
            urgency,
            "أهلاً بيك. تحت أمرك، تحب أساعدك في إيه؟",
            "رسالة عامة",
            False,
        )

    needs_clarification = (
        bool(unknown_words)
        or not extracted_items
        or any(item["quantity"] is None for item in extracted_items)
    )

    categories = [item["category"] for item in extracted_items]
    category = "groceries" if "groceries" in categories else (
        categories[0] if categories else "other"
    )

    if needs_clarification:
        missing_quantity_items = [
            item for item in extracted_items
            if item["quantity"] is None
        ]

        if unknown_words:
            clarification = (
                "مش قادر أحدد الصنف: "
                + "، ".join(unknown_words)
                + ". ممكن توضح النوع أو تختار صنفًا من القائمة؟"
            )
        elif missing_quantity_items:
            names = " و".join(item["name"] for item in missing_quantity_items)
            clarification = (
                f"ممكن تحدد الكمية المطلوبة من {names}؟ "
                "لازم تكون الكمية أكبر من صفر."
            )
        else:
            clarification = "ممكن تحدد الأصناف المطلوبة؟"

        requested_names = (
            "، ".join(item["name"] for item in extracted_items)
            if extracted_items else "الأصناف"
        )
        reply = (
            f"فهمت إنك عايز تطلب {requested_names}. "
            f"{clarification}"
        )
        action = "استكمال تحديد الأصناف والكميات ومراجعة الأسعار قبل التأكيد."
        title = "طلب يحتاج توضيح"
    else:
        item_names = " و".join(item["name"] for item in extracted_items)
        reply = f"تمام، فهمت طلبك: {item_names}. راجع الأصناف والأسعار قبل تأكيد الطلب."
        action = "راجع الأصناف والأسعار ثم أكد الطلب."
        title = f"طلب {category}"

    return {
        "success": True,
        "agent_id": "agent_01_order_parser",
        "agent_name_ar": "وكيل تحليل الطلبات باللهجة المصرية",
        "reply": reply,
        "confidence": 0.85 if not needs_clarification else 0.65,
        "summary_ar": f"تم استخراج {len(extracted_items)} أصناف. الأسعار تحتاج مراجعة.",
        "structured_data": {
            "intent": "order",
            "title": title,
            "category": category,
            "urgency": urgency,
            "items": extracted_items,
            "estimated_total_cost_egp": None,
            "suggested_tip_egp": 0.0,
            "needs_clarification": needs_clarification,
            "action_recommendation": action,
        },
        "action_recommendation": action,
    }

