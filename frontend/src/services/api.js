/**
 * El-Beh El-Bawab v2.0 Complete API Client
 * يربط الواجهة الأمامية بجميع مسارات البايثون (Auth, Orders, Wallet, Reviews, Buildings, Notifications)
 */

const API_BASE_URL = window.EL_BEH_API_URL || "http://localhost:8000/api";

export const ElBehApi = {
  // 1. المصادقة وتسجيل الدخول (Authentication)
  async login(phone, inviteCode = "NILE-15", otpCode = "1234") {
    const res = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ phone, invite_code: inviteCode, otp_code: otpCode }),
    });
    if (!res.ok) throw new Error("بيانات الدخول غير صحيحة");
    return res.json();
  },

  async registerUser(userPayload, inviteCode = "NILE-15") {
    const res = await fetch(`${API_BASE_URL}/auth/register?invite_code=${encodeURIComponent(inviteCode)}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(userPayload),
    });
    if (!res.ok) throw new Error("تعذر تسجيل الحساب الجديد");
    return res.json();
  },

  // 2. العمارات ولوحة الإعلانات (Buildings & Announcements)
  async getBuildings() {
    const res = await fetch(`${API_BASE_URL}/buildings`);
    if (!res.ok) throw new Error("فشل تحميل بيانات العمارات");
    return res.json();
  },

  async getAnnouncements(buildingId = 1) {
    const res = await fetch(`${API_BASE_URL}/buildings/${buildingId}/announcements`);
    if (!res.ok) throw new Error("فشل تحميل إعلانات العمارة");
    return res.json();
  },

  async createAnnouncement(buildingId, payload) {
    const res = await fetch(`${API_BASE_URL}/buildings/${buildingId}/announcements`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ building_id: buildingId, ...payload }),
    });
    if (!res.ok) throw new Error("تعذر نشر الإعلان");
    return res.json();
  },

  // 3. المستخدمون وحالة تواجد البواب (Users & Availability)
  async getUsers(buildingId = 1, role = null) {
    const params = new URLSearchParams({ building_id: buildingId });
    if (role) params.append("role", role);
    const res = await fetch(`${API_BASE_URL}/users?${params.toString()}`);
    if (!res.ok) throw new Error("فشل تحميل المستخدمين");
    return res.json();
  },

  async toggleAvailability(userId, isAvailable) {
    const res = await fetch(`${API_BASE_URL}/users/${userId}/availability?is_available=${isAvailable}`, {
      method: "PATCH",
    });
    if (!res.ok) throw new Error("تعذر تحديث حالة التواجد");
    return res.json();
  },

  // 4. الطلبات والخدمات والإحصائيات (Orders & Stats)
  async getStats(buildingId = 1) {
    const res = await fetch(`${API_BASE_URL}/orders/stats/${buildingId}`);
    if (!res.ok) throw new Error("فشل تحميل الإحصائيات");
    return res.json();
  },

  async getOrders({ buildingId = 1, status = null, residentId = null, category = null } = {}) {
    const params = new URLSearchParams({ building_id: buildingId });
    if (status) params.append("status", status);
    if (residentId) params.append("resident_id", residentId);
    if (category) params.append("category", category);
    const res = await fetch(`${API_BASE_URL}/orders?${params.toString()}`);
    if (!res.ok) throw new Error("فشل تحميل الطلبات");
    return res.json();
  },

  async createOrder(orderPayload) {
    const res = await fetch(`${API_BASE_URL}/orders`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(orderPayload),
    });
    if (!res.ok) throw new Error("تعذر إرسال الطلب");
    return res.json();
  },

  async updateOrderStatus(orderId, { status, bawab_id = 1, actual_items_cost = null, is_paid = null, notes = null }) {
    const res = await fetch(`${API_BASE_URL}/orders/${orderId}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status, bawab_id, actual_items_cost, is_paid, notes }),
    });
    if (!res.ok) throw new Error("تعذر تحديث حالة الطلب");
    return res.json();
  },

  // 5. المحفظة المالية وحساب العهدة (Wallet & Settlements)
  async getWalletSummary(buildingId = 1) {
    const res = await fetch(`${API_BASE_URL}/wallet/summary/${buildingId}`);
    if (!res.ok) throw new Error("فشل تحميل ملخص المحفظة");
    return res.json();
  },

  async getWalletTransactions(buildingId = 1, userId = null) {
    const params = new URLSearchParams({ building_id: buildingId });
    if (userId) params.append("user_id", userId);
    const res = await fetch(`${API_BASE_URL}/wallet/transactions?${params.toString()}`);
    if (!res.ok) throw new Error("فشل تحميل المعاملات المالية");
    return res.json();
  },

  async createWalletTransaction(payload) {
    const res = await fetch(`${API_BASE_URL}/wallet/transactions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error("تعذر تسجيل العملية المالية");
    return res.json();
  },

  // 6. التقييمات والمراجعات (Reviews)
  async getBawabReviews(bawabId = 1) {
    const res = await fetch(`${API_BASE_URL}/reviews/${bawabId}`);
    if (!res.ok) throw new Error("فشل تحميل التقييمات");
    return res.json();
  },

  async submitReview(payload) {
    const res = await fetch(`${API_BASE_URL}/reviews`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error("تعذر إرسال التقييم");
    return res.json();
  },

  // 7. الإشعارات (Notifications)
  async getNotifications(userId) {
    const res = await fetch(`${API_BASE_URL}/notifications/${userId}`);
    if (!res.ok) throw new Error("فشل تحميل الإشعارات");
    return res.json();
  },

  // 8. وكلاء الذكاء الاصطناعي والمحادثة الفورية
  async chatWithAi(message, residentId = 2, buildingId = 1, history = []) {
    const res = await fetch(`${API_BASE_URL}/ai-agents/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        resident_id: residentId,
        building_id: buildingId,
        history,
      }),
    });
    if (!res.ok) throw new Error("فشل التواصل مع المساعد الذكي");
    return res.json();
  },

  async invokeAiAgent(agentId, prompt, buildingId = 1, context = null) {
    const res = await fetch(`${API_BASE_URL}/ai-agents/invoke`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        agent_id: agentId,
        prompt,
        building_id: buildingId,
        context,
      }),
    });
    if (!res.ok) throw new Error("فشل تشغيل وكيل الذكاء الاصطناعي");
    return res.json();
  },

  async getAiAgentLogs(buildingId = 1) {
    const res = await fetch(`${API_BASE_URL}/ai-agents/logs/${buildingId}`);
    if (!res.ok) throw new Error("فشل جلب سجلات الذكاء الاصطناعي");
    return res.json();
  },
};

