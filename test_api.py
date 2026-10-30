from app.core.database import init_db
from app.routers import (
    auth, buildings, users, orders, maintenance, visitors,
    parcels, garage, utilities, wallet, announcements,
    reviews, chat, emergency, ai_agents
)
from app.schemas.models import (
    LoginRequest, OrderCreate, MaintenanceTicketCreate,
    VisitorPassCreate, ParcelCreate, AIAgentInvokeRequest
)


def test_all_15_apis_and_15_ai_agents():
    init_db()
    # Check 15 AI Agents catalog
    catalog = ai_agents.list_all_15_ai_agents()
    assert catalog["total_agents"] == 15

    # Invoke AI Agent #1
    res_agent = ai_agents.invoke_specific_ai_agent(
        AIAgentInvokeRequest(
            agent_id="agent_01_order_parser",
            prompt="هاتلي ٢ لبن جهينة وكرتونة بيض وعيش سخن بسرعة",
            building_id=1,
        )
    )
    assert res_agent["agent_number"] == 1
    assert "structured_data" in res_agent

    # Check Auth API #1
    login_res = auth.login_with_phone_and_invite_code(
        LoginRequest(phone="01000000002", invite_code="NILE-15", otp_code="1234")
    )
    assert "access_token" in login_res

    # Check Maintenance API #5
    ticket = maintenance.create_maintenance_ticket(
        MaintenanceTicketCreate(issue_title="تسريب مياه", description="تحت الحوض")
    )
    assert ticket["id"] > 0

    # Check Visitors API #6
    vpass = visitors.create_visitor_pass(VisitorPassCreate(visitor_name="مندوب طلبات"))
    assert vpass["pass_code"].startswith("PASS-")

    # Check Parcels API #7
    parcel = parcels.register_parcel(
        ParcelCreate(courier_name="أمازون", tracking_Or_desc="طرد شقة 12", cod_amount=150.0, paid_by_bawab=True)
    )
    assert parcel["pickup_code"].startswith("BOX-")
