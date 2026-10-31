/**
 * El-Beh El-Bawab v3.0 Unified Mobile SDK
 * يربط تطبيق الموبايل بجميع الـ 15 APIs والـ 15 AI Agents في سيرفر البايثون FastAPI
 */

const BASE_URL = "http://localhost:8000/api";

export const ElBehMobileSDK = {
  // 01. Auth API
  login: (phone, invite_code = "NILE-15", otp_code = "1234") =>
    fetch(`${BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ phone, invite_code, otp_code }),
    }).then((r) => r.json()),

  // 02. Buildings API
  getBuildings: () => fetch(`${BASE_URL}/buildings`).then((r) => r.json()),

  // 03. Users & Bawab Availability API
  getUsers: (buildingId = 1) => fetch(`${BASE_URL}/users?building_id=${buildingId}`).then((r) => r.json()),
  toggleAvailability: (userId, isAvailable) =>
    fetch(`${BASE_URL}/users/${userId}/availability?is_available=${isAvailable}`, { method: "PATCH" }).then((r) => r.json()),

  // 04. Orders & Errands API
  getOrders: (buildingId = 1) => fetch(`${BASE_URL}/orders?building_id=${buildingId}`).then((r) => r.json()),
  createOrder: (payload) =>
    fetch(`${BASE_URL}/orders`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then((r) => r.json()),
  updateOrderStatus: (orderId, payload) =>
    fetch(`${BASE_URL}/orders/${orderId}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then((r) => r.json()),

  // 05. Maintenance API
  getMaintenanceTickets: (buildingId = 1) => fetch(`${BASE_URL}/maintenance?building_id=${buildingId}`).then((r) => r.json()),
  createMaintenanceTicket: (payload) =>
    fetch(`${BASE_URL}/maintenance`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then((r) => r.json()),

  // 06. Visitors & Security Gate API
  getVisitorPasses: (buildingId = 1) => fetch(`${BASE_URL}/visitors?building_id=${buildingId}`).then((r) => r.json()),
  createVisitorPass: (payload) =>
    fetch(`${BASE_URL}/visitors`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then((r) => r.json()),

  // 07. Parcels & Safe-Keeping API
  getParcels: (buildingId = 1) => fetch(`${BASE_URL}/parcels?building_id=${buildingId}`).then((r) => r.json()),
  registerParcel: (payload) =>
    fetch(`${BASE_URL}/parcels`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then((r) => r.json()),

  // 08. Garage & Car Wash API
  getGarageVehicles: (buildingId = 1) => fetch(`${BASE_URL}/garage?building_id=${buildingId}`).then((r) => r.json()),

  // 09. Shared Utilities API
  getUtilityBills: (buildingId = 1) => fetch(`${BASE_URL}/utilities?building_id=${buildingId}`).then((r) => r.json()),

  // 10. Wallet & Custody Ledger API
  getWalletSummary: (buildingId = 1) => fetch(`${BASE_URL}/wallet/summary/${buildingId}`).then((r) => r.json()),
  getWalletTransactions: (buildingId = 1) => fetch(`${BASE_URL}/wallet/transactions?building_id=${buildingId}`).then((r) => r.json()),

  // 11. Announcements API
  getAnnouncements: (buildingId = 1) => fetch(`${BASE_URL}/announcements/${buildingId}`).then((r) => r.json()),

  // 12. Reviews API
  getReviews: (bawabId = 1) => fetch(`${BASE_URL}/reviews/${bawabId}`).then((r) => r.json()),

  // 13. Chat & Voice Replies API
  getChatMessages: (buildingId = 1) => fetch(`${BASE_URL}/chat/${buildingId}`).then((r) => r.json()),
  sendChatMessage: (payload) =>
    fetch(`${BASE_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then((r) => r.json()),

  // 14. Emergency SOS API
  getEmergencyAlerts: (buildingId = 1) => fetch(`${BASE_URL}/emergency/${buildingId}`).then((r) => r.json()),
  triggerSOS: (payload) =>
    fetch(`${BASE_URL}/emergency/sos`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then((r) => r.json()),

  // 15. 15 AI Agents Hub API
  getAll15Agents: () => fetch(`${BASE_URL}/ai-agents`).then((r) => r.json()),
  invokeAIAgent: (agent_id, prompt, building_id = 1) =>
    fetch(`${BASE_URL}/ai-agents/invoke`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ agent_id, prompt, building_id }),
    }).then((r) => r.json()),
};
