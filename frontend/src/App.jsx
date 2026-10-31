import React, { useState } from "react";
import {
  Activity,
  Award,
  BarChart3,
  Building2,
  CheckCircle2,
  Code2,
  Cpu,
  Database,
  FileJson,
  Layers,
  Navigation,
  Package,
  Plus,
  RefreshCw,
  Server,
  ShieldAlert,
  Sparkles,
  TrendingUp,
  Users,
  Wallet
} from "lucide-react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from "recharts";

const WEEKLY_ANALYTICS = [
  { day: "السبت", orders: 18, tips: 340, pooled: 8 },
  { day: "الأحد", orders: 24, tips: 460, pooled: 12 },
  { day: "الإثنين", orders: 21, tips: 395, pooled: 10 },
  { day: "الثلاثاء", orders: 29, tips: 540, pooled: 16 },
  { day: "الأربعاء", orders: 26, tips: 490, pooled: 14 },
  { day: "الخميس", orders: 35, tips: 680, pooled: 21 },
  { day: "الجمعة", orders: 42, tips: 820, pooled: 28 }
];

const AI_AGENTS_15 = [
  { id: "agent_01_order_parser", num: 1, name: "وكيل تحليل الطلبات باللهجة المصرية", model: "Careem Quik NLP", latency: "42ms", accuracy: "98.4%", output: "تحويل الرسائل العامية إلى JSON مهيكل مع تسعير الأصناف وتحديد الأولوية" },
  { id: "agent_02_price_estimator", num: 2, name: "وكيل التسعير المرن (Surge Pricing)", model: "Uber Surge Engine", latency: "18ms", accuracy: "99.1%", output: "حساب معامل الذروة (0.85x - 1.5x) وإكرامية البواب حسب الوزن والطابق" },
  { id: "agent_03_errand_batcher", num: 3, name: "وكيل تجميع المشاوير وخط السير", model: "Halan Route Pooler", latency: "35ms", accuracy: "97.8%", output: "دمج طلبات الشقق المتجاورة في مشوار واحد لتوفير 45% من وقت البواب" },
  { id: "agent_04_maintenance_diagnostician", num: 4, name: "وكيل تشخيص أعطال الصيانة المنزلية", model: "Smart Home Diagnostician", latency: "55ms", accuracy: "96.5%", output: "تشخيص أعطال السباكة والكهرباء والغاز وتحديد قطع الغيار المطلوبة" },
  { id: "agent_05_invoice_auditor", num: 5, name: "وكيل مراجعة الفواتير وكشف الفروق", model: "Fintech Custody Auditor", latency: "29ms", accuracy: "99.3%", output: "مطابقة الفاتورة الفعلية مع أسعار السوق المصري لمنع أي تلاعب" },
  { id: "agent_06_urgency_dispatcher", num: 6, name: "وكيل ترتيب الأولويات والطوارئ الذكي", model: "Uber Priority Dispatch", latency: "15ms", accuracy: "99.0%", output: "تقديم طلبات الأدوية وكبار السن والطوارئ على المشاوير غير العاجلة" },
  { id: "agent_07_announcement_writer", num: 7, name: "وكيل صياغة إعلانات وتنبيهات العمارة", model: "Arabic Copywriter AI", latency: "60ms", accuracy: "98.0%", output: "صياغة تنبيهات رسمية مهذبة لصيانة الأسانسير والخزان وإرسالها للسكان" },
  { id: "agent_08_utility_splitter", num: 8, name: "وكيل تقسيم فواتير المرافق المشتركة", model: "Halan Bill Splitter", latency: "12ms", accuracy: "100%", output: "تقسيم فواتير مياه العمارة وكهرباء الأسانسير ومتابعة الشقق المسددة" },
  { id: "agent_09_security_gatekeeper", num: 9, name: "وكيل أمن البوابة وتصاريح QR/PIN", model: "Uber PIN Gatekeeper", latency: "20ms", accuracy: "99.5%", output: "إصدار أكواد دخول مؤقتة لمندوبي التوصيل والضيوف مع إشعار الساكن" },
  { id: "agent_10_car_garage_coordinator", num: 10, name: "وكيل تنسيق الجراج وغسيل السيارات", model: "Careem Car Care Scheduler", latency: "27ms", accuracy: "98.2%", output: "جدولة غسيل السيارات الصباحي حسب مواعيد خروج كل ساكن للعمل" },
  { id: "agent_11_voice_chat_assistant", num: 11, name: "وكيل الردود الذكية وتلخيص الصوتيات", model: "Captain 1-Tap Reply AI", latency: "38ms", accuracy: "97.6%", output: "توليد ٣ ردود سريعة للبواب بضغطة زر أثناء انشغاله بالمشتريات" },
  { id: "agent_12_package_tracker", num: 12, name: "وكيل أمانات البوابة واستلام الطرود", model: "Careem Box Custody", latency: "22ms", accuracy: "99.4%", output: "تسجيل الشحنات في خزينة البواب وإضافة مبالغ COD في عهدة الشقة" },
  { id: "agent_13_bawab_coach_sentiment", num: 13, name: "وكيل تحليل رضا السكان ومكافآت الكابتن", model: "Captain Tier Analytics", latency: "44ms", accuracy: "97.9%", output: "تحليل التقييمات ومنح شارة Captain Platinum ومكافآت الأداء الشهري" },
  { id: "agent_14_emergency_sos", num: 14, name: "وكيل إدارة الطوارئ والاستغاثة SOS", model: "Critical SOS Responder", latency: "10ms", accuracy: "99.9%", output: "إصدار خطة إنقاذ فورية عند احتجاز الأسانسير أو تسريب الغاز" },
  { id: "agent_15_predictive_restock", num: 15, name: "وكيل التنبؤ بالطلبات والائتمان المصغر", model: "Halan BNPL & Restock AI", latency: "48ms", accuracy: "96.8%", output: "توقع طلبات الجمعة المعتادة وإدارة حد ائتمان الشقة (١٥٠٠ ج.م عالنوتة)" }
];

const BACKEND_APIS_15 = [
  { num: "01", endpoint: "/api/auth", router: "auth.py", table: "users", status: "200 OK", desc: "المصادقة، كود العمارة، ورمز التحقق OTP" },
  { num: "02", endpoint: "/api/buildings", router: "buildings.py", table: "buildings", status: "200 OK", desc: "بيانات العمارة وحالة الأسانسير وموتور المياه" },
  { num: "03", endpoint: "/api/users", router: "users.py", table: "users", status: "200 OK", desc: "إدارة السكان والكابتن البواب وحالة التواجد" },
  { num: "04", endpoint: "/api/orders", router: "orders.py", table: "orders", status: "200 OK", desc: "إدارة الطلبات، التسعير المرن، والمشاوير المجمعة" },
  { num: "05", endpoint: "/api/maintenance", router: "maintenance.py", table: "maintenance_tickets", status: "200 OK", desc: "بلاغات السباكة والكهرباء والغاز والتشخيص الذكي" },
  { num: "06", endpoint: "/api/visitors", router: "visitors.py", table: "visitors_passes", status: "200 OK", desc: "تصاريح دخول الزوار والدليفري بكود PASS-XXX" },
  { num: "07", endpoint: "/api/parcels", router: "parcels.py", table: "parcels", status: "200 OK", desc: "خزينة الطرود وأمانات البوابة وحساب COD" },
  { num: "08", endpoint: "/api/garage", router: "garage.py", table: "vehicles", status: "200 OK", desc: "باكيات الجراج وجدول غسيل السيارات الصباحي" },
  { num: "09", endpoint: "/api/utilities", router: "utilities.py", table: "utility_bills", status: "200 OK", desc: "تقسيم فواتير المياه وكهرباء الأسانسير" },
  { num: "10", endpoint: "/api/wallet", router: "wallet.py", table: "wallet_transactions", status: "200 OK", desc: "محفظة الكابتن، تقسيط حالاً BNPL، والعهدة" },
  { num: "11", endpoint: "/api/announcements", router: "announcements.py", table: "announcements", status: "200 OK", desc: "لوحة إعلانات العمارة والتنبيهات المثبتة" },
  { num: "12", endpoint: "/api/reviews", router: "reviews.py", table: "reviews", status: "200 OK", desc: "تقييمات السكان ونظام رتب الكابتن" },
  { num: "13", endpoint: "/api/chat", router: "chat.py", table: "chat_messages", status: "200 OK", desc: "المحادثة الفورية والردود الذكية بضغطة واحدة" },
  { num: "14", endpoint: "/api/emergency", router: "emergency.py", table: "emergency_alerts", status: "101 WS", desc: "طوارئ SOS وقناة WebSocket اللحظية" },
  { num: "15", endpoint: "/api/ai-agents", router: "ai_agents.py", table: "ai_agent_logs", status: "200 OK", desc: "بوابة تشغيل الـ 15 AI Agents وسجل قراراتها" }
];

export default function App() {
  const [activeSection, setActiveSection] = useState("overview"); // "overview" | "dispatch" | "ai-matrix" | "apis-json" | "fintech"
  const [selectedAgent, setSelectedAgent] = useState(AI_AGENTS_15[0]);
  const [surgeFactor, setSurgeFactor] = useState(1.2);
  const [toast, setToast] = useState(null);

  const [dispatchQueue, setDispatchQueue] = useState([
    { id: 901, apt: "شقة 12 (الدور 4)", resident: "أستاذ أحمد زكي", service: "سوبرماركت + فرن بلدي", mode: "Halan Pool (مدموج)", cost: 225, tip: 25, pin: "4829", status: "جاري التنفيذ 🛵" },
    { id: 902, apt: "شقة 20 (الدور 7)", resident: "مدام سعاد", service: "تغيير أنبوبة بوتاجاز", mode: "Uber Priority 🔥", cost: 150, tip: 35, pin: "9104", status: "قيد الانتظار ⏳" },
    { id: 903, apt: "شقة 5 (الدور 2)", resident: "مهندس طارق علام", service: "صيدلية العزبي", mode: "Careem Quik", cost: 140, tip: 20, pin: "3312", status: "تم التسليم ✅" }
  ]);

  const notify = (msg) => {
    setToast(msg);
    setTimeout(() => setToast(null), 3000);
  };

  const liveJsonPayload = {
    building: { id: 1, name: "عمارة النيل الذهبية", code: "NILE-15", floors: 12 },
    captain_bawab: { name: "عم عبد السميع", tier: "Platinum 4.94★", active_surge: surgeFactor, wallet_egp: 640 },
    active_ai_agent: selectedAgent,
    fintech_halan_bnpl: { total_credit_limit_egp: 36000, active_custody_egp: 1420, collection_rate: "94.2%" },
    orders_in_queue: dispatchQueue.length
  };

  return (
    <div dir="rtl" className="min-h-screen bg-slate-950 text-slate-100 flex font-sans">
      
      {/* Toast Notification */}
      {toast && (
        <div className="fixed bottom-6 left-6 z-50 bg-emerald-600 text-white px-5 py-3 rounded-2xl shadow-2xl font-bold text-sm flex items-center gap-2 border border-emerald-300/40">
          <Sparkles className="w-4 h-4" />
          <span>{toast}</span>
        </div>
      )}

      {/* Right Sidebar Navigation (Desktop Enterprise Command Center) */}
      <aside className="w-72 bg-slate-900 border-l border-slate-800 p-5 flex flex-col justify-between shrink-0">
        <div className="space-y-6">
          {/* Brand Logo */}
          <div className="flex items-center gap-3 pb-4 border-b border-slate-800">
            <div className="w-12 h-12 rounded-2xl bg-amber-400 text-slate-950 flex items-center justify-center text-2xl font-black shadow-lg">
              🖥️
            </div>
            <div>
              <h1 className="text-lg font-black text-white">البيه البواب v4.0</h1>
              <p className="text-xs text-teal-400 font-bold">نسخة الكمبيوتر المستقلة (Desktop)</p>
            </div>
          </div>

          {/* Navigation Menu */}
          <nav className="space-y-1.5 text-sm">
            {[
              { id: "overview", label: "غرفة العمليات والتحليلات", icon: BarChart3 },
              { id: "dispatch", label: "رادار التوجيه والـ Surge (Uber)", icon: Navigation },
              { id: "ai-matrix", label: "مصفوفة الـ 15 AI Agents", icon: Cpu },
              { id: "apis-json", label: "الـ 15 APIs ومولد الـ JSON", icon: FileJson },
              { id: "fintech", label: "بنك العمارة وائتمان «حالاً»", icon: Wallet }
            ].map((item) => {
              const IconComp = item.icon;
              const active = activeSection === item.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setActiveSection(item.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-2xl font-extrabold transition ${
                    active
                      ? "bg-gradient-to-l from-teal-600 to-emerald-600 text-white shadow-lg"
                      : "text-slate-400 hover:bg-slate-800/70 hover:text-white"
                  }`}
                >
                  <IconComp className="w-5 h-5" />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Competitor Architecture Box */}
        <div className="bg-slate-950/90 p-4 rounded-2xl border border-slate-800 space-y-2 text-xs">
          <div className="font-black text-amber-400">🏆 معمارية المنافسين المدمجة</div>
          <div className="text-slate-400 space-y-1">
            <div>• <strong className="text-white">Uber:</strong> رادار ETA + Surge + كود PIN</div>
            <div>• <strong className="text-white">Careem:</strong> Super-App + رتب الكابتن</div>
            <div>• <strong className="text-white">Halan:</strong> تقسيط العهدة + دمج المشاوير</div>
          </div>
        </div>
      </aside>

      {/* Main Desktop Workspace */}
      <div className="flex-1 flex flex-col min-w-0">
        
        {/* Top Desktop Bar */}
        <header className="bg-slate-900/80 backdrop-blur border-b border-slate-800 px-8 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-black text-white">
              لوحة التحكم المركزية لإدارة العمارة واتحاد الملاك (Desktop Command Center)
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              عمارة النيل الذهبية (٢٤ شقة) • Python FastAPI Async + React 18 + JSON Schema Engine
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-3 py-1.5 rounded-xl text-xs font-extrabold">
              ● Python Backend: 15/15 APIs Online
            </span>
            <span className="bg-amber-400/10 text-amber-300 border border-amber-400/30 px-3 py-1.5 rounded-xl text-xs font-extrabold">
              🤖 15/15 AI Agents Ready
            </span>
          </div>
        </header>

        {/* Main Content Body */}
        <main className="p-8 space-y-6 overflow-y-auto">
          
          {/* Top KPI Row */}
          <div className="grid grid-cols-5 gap-4">
            <div className="bg-slate-900 p-5 rounded-2xl border border-slate-800">
              <div className="text-xs text-slate-400 font-bold">إجمالي المشاوير الأسبوعية</div>
              <div className="text-3xl font-black text-white mt-1">195</div>
              <div className="text-xs text-emerald-400 font-bold mt-1">+28% بفضل دمج المشاوير</div>
            </div>
            <div className="bg-slate-900 p-5 rounded-2xl border border-slate-800">
              <div className="text-xs text-slate-400 font-bold">متوسط زمن التوصيل (Uber ETA)</div>
              <div className="text-3xl font-black text-amber-400 mt-1">9.4 د</div>
              <div className="text-xs text-slate-400 mt-1">أسرع بـ 14 دقيقة عن المعتاد</div>
            </div>
            <div className="bg-slate-900 p-5 rounded-2xl border border-slate-800">
              <div className="text-xs text-slate-400 font-bold">رتبة الكابتن عبد السميع</div>
              <div className="text-2xl font-black text-teal-400 mt-1">Platinum 4.94★</div>
              <div className="text-xs text-slate-400 mt-1">Careem Captain Pro Tier</div>
            </div>
            <div className="bg-slate-900 p-5 rounded-2xl border border-slate-800">
              <div className="text-xs text-slate-400 font-bold">محفظة «حالاً عالنوتة» النشطة</div>
              <div className="text-3xl font-black text-indigo-400 mt-1">4,850 <span className="text-sm">ج.م</span></div>
              <div className="text-xs text-emerald-400 mt-1">نسبة سداد الشقق: 96%</div>
            </div>
            <div className="bg-slate-900 p-5 rounded-2xl border border-slate-800">
              <div className="text-xs text-slate-400 font-bold">قرارات الـ 15 AI Agents</div>
              <div className="text-3xl font-black text-emerald-400 mt-1">1,420</div>
              <div className="text-xs text-slate-400 mt-1">دقة تصنيف وتوجيه 98.4%</div>
            </div>
          </div>

          {/* =============================================================== */}
          {/* SECTION 1: OVERVIEW & RECHARTS ANALYTICS                        */}
          {/* =============================================================== */}
          {activeSection === "overview" && (
            <div className="grid grid-cols-12 gap-6">
              <div className="col-span-7 bg-slate-900 p-6 rounded-2xl border border-slate-800">
                <h3 className="text-base font-black text-white mb-1">📈 منحنى الطلبات والمشاوير المجمعة (Uber & Halan Pooling Analytics)</h3>
                <p className="text-xs text-slate-400 mb-4">مقارنة بين إجمالي الطلبات والطلبات المدمجة التي وفرت وقت ومجهود البواب خلال الأسبوع</p>
                <div className="relative h-72 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={WEEKLY_ANALYTICS}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="day" stroke="#94a3b8" fontSize={12} />
                      <YAxis stroke="#94a3b8" fontSize={12} />
                      <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#14b8a6", borderRadius: "12px", color: "#fff" }} />
                      <Area type="monotone" dataKey="orders" name="إجمالي الطلبات" stroke="#14b8a6" fill="#0d9488" fillOpacity={0.35} />
                      <Area type="monotone" dataKey="pooled" name="مشاوير مدمجة (Halan Pool)" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.25} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="col-span-5 bg-slate-900 p-6 rounded-2xl border border-slate-800">
                <h3 className="text-base font-black text-white mb-1">💰 نمو إكراميات ومكافآت الكابتن (ج.م)</h3>
                <p className="text-xs text-slate-400 mb-4">العائد اليومي للكابتن عبد السميع بعد تطبيق التسعير المرن (Surge)</p>
                <div className="relative h-72 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={WEEKLY_ANALYTICS}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="day" stroke="#94a3b8" fontSize={12} />
                      <YAxis stroke="#94a3b8" fontSize={12} />
                      <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#f59e0b", borderRadius: "12px", color: "#fff" }} />
                      <Bar dataKey="tips" name="إكراميات الكابتن (ج.م)" fill="#f59e0b" radius={[8, 8, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          )}

          {/* =============================================================== */}
          {/* SECTION 2: UBER DISPATCH & SURGE CONTROL                        */}
          {/* =============================================================== */}
          {activeSection === "dispatch" && (
            <div className="bg-slate-900 p-6 rounded-2xl border border-slate-800 space-y-5">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-black text-white">🗺️ مركز التوجيه اللحظي ومعامل الذروة (Uber Dispatch & Surge Control)</h3>
                  <p className="text-xs text-slate-400">تحكم في معامل أوقات الذروة وتابع جدول المشاوير النشطة وأكواد الاستلام (Drop-off PIN)</p>
                </div>
                <div className="flex items-center gap-3 bg-slate-950 px-4 py-2 rounded-xl border border-slate-800">
                  <span className="text-xs font-bold text-slate-300">معامل الذروة الحالي (Surge):</span>
                  {[1.0, 1.2, 1.5].map((val) => (
                    <button
                      key={val}
                      type="button"
                      onClick={() => {
                        setSurgeFactor(val);
                        notify(`تم ضبط معامل الذروة على ${val}x`);
                      }}
                      className={`px-3 py-1 rounded-lg text-xs font-black ${
                        surgeFactor === val ? "bg-amber-400 text-slate-950" : "bg-slate-800 text-slate-300"
                      }`}
                    >
                      {val}x
                    </button>
                  ))}
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-right text-sm border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 text-xs">
                      <th className="py-3 px-4">رقم الطلب</th>
                      <th className="py-3 px-4">الشقة والساكن</th>
                      <th className="py-3 px-4">الخدمة المطلوبة</th>
                      <th className="py-3 px-4">نظام التوجيه</th>
                      <th className="py-3 px-4">التكلفة + الإكرامية</th>
                      <th className="py-3 px-4">كود الاستلام (PIN)</th>
                      <th className="py-3 px-4">الحالة</th>
                      <th className="py-3 px-4">إجراء سريع</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/70 text-xs">
                    {dispatchQueue.map((row) => (
                      <tr key={row.id} className="hover:bg-slate-800/40">
                        <td className="py-3.5 px-4 font-mono text-amber-300">#{row.id}</td>
                        <td className="py-3.5 px-4 font-bold text-white">{row.apt} • {row.resident}</td>
                        <td className="py-3.5 px-4 text-slate-300">{row.service}</td>
                        <td className="py-3.5 px-4">
                          <span className="bg-teal-950 text-teal-300 border border-teal-700/50 px-2.5 py-1 rounded-lg font-bold">
                            {row.mode}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 font-bold text-emerald-400">{row.cost + row.tip} ج.م</td>
                        <td className="py-3.5 px-4 font-mono font-black text-amber-400">{row.pin}</td>
                        <td className="py-3.5 px-4 font-bold">{row.status}</td>
                        <td className="py-3.5 px-4">
                          <button
                            type="button"
                            onClick={() => {
                              setDispatchQueue((prev) =>
                                prev.map((item) => (item.id === row.id ? { ...item, status: "تم التسليم ✅" } : item))
                              );
                              notify(`تم تأكيد تسليم الطلب #${row.id} بكود ${row.pin}`);
                            }}
                            className="bg-teal-600 hover:bg-teal-500 text-white px-3 py-1 rounded-lg font-bold"
                          >
                            تأكيد التسليم
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* =============================================================== */}
          {/* SECTION 3: 15 AI AGENTS ENTERPRISE MATRIX                       */}
          {/* =============================================================== */}
          {activeSection === "ai-matrix" && (
            <div className="space-y-4">
              <div className="bg-gradient-to-l from-teal-950 to-slate-900 p-5 rounded-2xl border border-teal-500/40 flex items-center justify-between">
                <div>
                  <h3 className="text-base font-black text-amber-300">
                    🤖 الوكيل النشط في الفحص: #{selectedAgent.num} — {selectedAgent.name}
                  </h3>
                  <p className="text-xs text-slate-200 mt-1">{selectedAgent.output}</p>
                </div>
                <div className="text-left text-xs font-mono text-emerald-300">
                  <div>Model: {selectedAgent.model}</div>
                  <div>Latency: {selectedAgent.latency} • Accuracy: {selectedAgent.accuracy}</div>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                {AI_AGENTS_15.map((ag) => (
                  <div
                    key={ag.id}
                    onClick={() => {
                      setSelectedAgent(ag);
                      notify(`تم تحديد الوكيل #${ag.num}: ${ag.name}`);
                    }}
                    className={`cursor-pointer p-4 rounded-2xl border transition ${
                      selectedAgent.id === ag.id
                        ? "bg-teal-950/60 border-amber-400 shadow-lg"
                        : "bg-slate-900 border-slate-800 hover:border-teal-600"
                    }`}
                  >
                    <div className="flex items-center justify-between text-xs mb-2">
                      <span className="bg-amber-400 text-slate-950 font-black px-2.5 py-0.5 rounded-full">
                        AI Agent #{ag.num}
                      </span>
                      <span className="text-emerald-400 font-mono">{ag.accuracy}</span>
                    </div>
                    <h4 className="font-black text-sm text-white mb-1">{ag.name}</h4>
                    <p className="text-xs text-slate-400">{ag.output}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* =============================================================== */}
          {/* SECTION 4: 15 BACKEND APIs & LIVE JSON SCHEMA INSPECTOR         */}
          {/* =============================================================== */}
          {activeSection === "apis-json" && (
            <div className="grid grid-cols-12 gap-6">
              <div className="col-span-7 bg-slate-900 p-5 rounded-2xl border border-slate-800 space-y-3">
                <h3 className="text-base font-black text-white">🔌 وحدات الـ 15 APIs في الباك إند (Python FastAPI Routers)</h3>
                <div className="grid grid-cols-1 gap-2 max-h-[460px] overflow-y-auto pr-1">
                  {BACKEND_APIS_15.map((api) => (
                    <div key={api.num} className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between text-xs">
                      <div>
                        <span className="font-black text-amber-400 ml-2">#{api.num}</span>
                        <code className="text-teal-300 font-bold" dir="ltr">{api.endpoint}</code>
                        <span className="text-slate-300 mr-3">{api.desc}</span>
                      </div>
                      <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded font-mono">
                        {api.status}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="col-span-5 bg-slate-900 p-5 rounded-2xl border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-black text-amber-300">📄 مخرجات JSON Schema الحية</h3>
                  <span className="text-xs font-mono text-slate-400">el_beh_super_app_specs.json</span>
                </div>
                <pre dir="ltr" className="bg-slate-950 text-emerald-300 p-4 rounded-xl border border-slate-800 text-xs font-mono overflow-x-auto max-h-[430px]">
                  {JSON.stringify(liveJsonPayload, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {/* =============================================================== */}
          {/* SECTION 5: HALAN FINTECH & BUILDING TREASURY                    */}
          {/* =============================================================== */}
          {activeSection === "fintech" && (
            <div className="grid grid-cols-3 gap-5">
              <div className="bg-slate-900 p-6 rounded-2xl border border-slate-800 space-y-2">
                <div className="text-xs font-bold text-amber-400">HALAN BNPL MICRO-CREDIT</div>
                <h3 className="text-lg font-black text-white">تمويل المشتريات والصيانة عالنوتة</h3>
                <p className="text-xs text-slate-400">
                  كل شقة تتمتع بحد ائتماني ١٥٠٠ ج.م لطلبات السوبرماركت، الصيدلية، وأعطال السباكة الطارئة، وتُسدد مجمعة أول كل شهر عبر InstaPay.
                </p>
              </div>
              <div className="bg-slate-900 p-6 rounded-2xl border border-slate-800 space-y-2">
                <div className="text-xs font-bold text-emerald-400">CAREEM CAPTAIN WALLET</div>
                <h3 className="text-lg font-black text-white">محفظة الكابتن ومكافآت الأداء</h3>
                <p className="text-xs text-slate-400">
                  تحويل فوري للإكراميات ومبالغ العهدة التي دفعها البواب للمندوبين (COD) مع كشف حساب لحظي معتمد من وكيل مراجعة الفواتير (#5).
                </p>
              </div>
              <div className="bg-slate-900 p-6 rounded-2xl border border-slate-800 space-y-2">
                <div className="text-xs font-bold text-sky-400">SHARED UTILITY SPLITTER</div>
                <h3 className="text-lg font-black text-white">صندوق اتحاد الملاك والمرافق</h3>
                <p className="text-xs text-slate-400">
                  تقسيم آلي لفواتير المياه المشتركة وكهرباء الأسانسير وصيانة الخزان مع إشعارات تذكير ذكية للشقق المتأخرة.
                </p>
              </div>
            </div>
          )}

        </main>
      </div>
    </div>
  );
}
