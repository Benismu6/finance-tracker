import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import google.generativeai as genai

# ==========================================
# 1. PAGE SETUP & HIGH-CONTRAST CSS
# ==========================================
st.set_page_config(
    page_title="Financial Command Hub",
    page_icon="🏠",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    header[data-testid="stHeader"], .stAppHeader, header { display: none !important; visibility: hidden !important; height: 0px !important; }
    div[data-testid="stDecoration"], #MainMenu, footer { display: none !important; visibility: hidden !important; }

    /* Centered on Desktop at max 750px, Full-Width on Mobile */
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 2rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
        max-width: 750px !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }
    
    /* Tab Container */
    div[data-baseweb="tab-list"] {
        background-color: #0F172A !important;
        border-radius: 12px !important;
        padding: 4px !important;
        gap: 4px !important;
        display: flex !important;
        width: 100% !important;
        overflow-x: auto !important;
        margin-bottom: 12px !important;
    }
    
    /* Tab Buttons */
    div[data-baseweb="tab-list"] button, button[data-baseweb="tab"] {
        background-color: #1E293B !important;
        border-radius: 8px !important;
        padding: 8px 12px !important;
        margin: 2px !important;
        border: 1px solid #334155 !important;
        flex: 1 0 auto !important;
    }
    
    div[data-baseweb="tab-list"] button *, button[data-baseweb="tab"] *, div[data-baseweb="tab-list"] p, button[data-baseweb="tab"] p {
        color: #F8FAFC !important;
        font-weight: 700 !important;
        font-size: 13px !important;
        opacity: 1 !important;
        visibility: visible !important;
        white-space: nowrap !important;
    }
    
    button[data-baseweb="tab"][aria-selected="true"], div[data-baseweb="tab-list"] button[aria-selected="true"] {
        background-color: #2563EB !important;
        border: 1px solid #60A5FA !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] *, div[data-baseweb="tab-list"] button[aria-selected="true"] * {
        color: #FFFFFF !important;
        font-weight: 800 !important;
    }
    div[data-baseweb="tab-highlight"] { display: none !important; }

    /* UI Cards */
    .hero-card {
        background: linear-gradient(135deg, #1E3A8A 0%, #0F172A 100%);
        border: 1px solid #3B82F6;
        border-radius: 14px;
        padding: 16px;
        color: white;
        margin-bottom: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.25);
    }
    .metric-val { font-size: 26px; font-weight: 800; color: #38BDF8; }
    .metric-sub { font-size: 12px; color: #94A3B8; }
    
    .stat-box {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 10px;
        text-align: center;
    }
    
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 48px;
        font-size: 16px;
        font-weight: 700;
        background-color: #2563EB;
        color: white;
        border: none;
        box-shadow: 0 2px 6px rgba(37,99,235,0.4);
    }
    
    .badge-opt { background-color: #065F46; color: #6EE7B7; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; }
    .badge-warn { background-color: #7C2D12; color: #FDBA74; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; }
    .badge-biz { background-color: #312E81; color: #C7D2FE; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. ROLLING DATE CALCULATION ENGINE
# ==========================================
today_dt = date.today()

def get_next_recurring_date(target_day: int, ref_date: date) -> date:
    """
    Computes the NEXT upcoming date for recurring monthly schedules.
    target_day = -1 indicates last day of month.
    """
    y, m = ref_date.year, ref_date.month
    if target_day == -1:
        last_day = calendar.monthrange(y, m)[1]
        cand = date(y, m, last_day)
        if cand < ref_date:
            next_m = m + 1 if m < 12 else 1
            next_y = y if m < 12 else y + 1
            cand = date(next_y, next_m, calendar.monthrange(next_y, next_m)[1])
        return cand
    
    max_d = calendar.monthrange(y, m)[1]
    cand = date(y, m, min(target_day, max_d))
    if cand < ref_date:
        next_m = m + 1 if m < 12 else 1
        next_y = y if m < 12 else y + 1
        max_d_next = calendar.monthrange(next_y, next_m)[1]
        cand = date(next_y, next_m, min(target_day, max_d_next))
    return cand

# ==========================================
# 3. DATA CONNECTION & GSHEET WRITER
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

def append_tx_to_sheet(row_values):
    """
    Directly accesses the underlying authenticated gspread client
    to append a row safely without permission or overwrite conflicts.
    """
    try:
        raw_client = conn._instance.client
    except Exception:
        raw_client = conn._instance
        
    sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    spreadsheet = raw_client.open_by_url(sheet_url)
    worksheet = spreadsheet.worksheet("Master_Transactions")
    worksheet.append_row(row_values, value_input_option="USER_ENTERED")

def get_ledger_data():
    try:
        df = conn.read(worksheet="Master_Transactions", ttl="0")
        if df is not None and not df.empty:
            df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0.0)
            return df
    except Exception:
        pass
    return pd.DataFrame(columns=[
        "Transaction_ID", "Date", "Account", "Type", "Category", 
        "Merchant", "Amount", "Goal_Tag", "Notes"
    ])

df_tx = get_ledger_data()

cash_registry = [
    {"name": "BofA 5522", "role": "Primary Operating Checking", "base": 251.67},
    {"name": "SECU 4987", "role": "Dedicated Home Savings / HYSA", "base": 4212.10}
]

# Personal CC definitions with recurring schedule days
personal_cc_definitions = [
    {"name": "Chase 1993", "base": 517.70, "limit": 10600.00, "due_day": 1, "close_day": 4, "is_primary": True, "target": "$0.00"},
    {"name": "Chase 2207", "base": 9.52, "limit": 4900.00, "due_day": 1, "close_day": 4, "is_azeo_active": True, "target": "~$10.00 (1%)"},
    {"name": "BofA 5309", "base": 22.21, "limit": 7500.00, "due_day": 24, "close_day": 27, "target": "$0.00"},
    {"name": "BofA 7197", "base": 37.12, "limit": 3500.00, "due_day": 24, "close_day": 27, "target": "$0.00"},
    {"name": "Apple 1765", "base": 0.00, "limit": 2000.00, "due_day": -1, "close_day": 3, "target": "$0.00"},
    {"name": "TJX", "base": 0.00, "limit": 3200.00, "due_day": 5, "close_day": 8, "target": "$0.00"}
]

biz_cc_definitions = [
    {"name": "Chase 0431", "base": 505.07, "limit": 0.00, "due_day": 1, "close_day": 7, "is_business": True, "target": "Business Expense"}
]

# Build live personal CC list with dynamically rolling dates
live_personal_cc = []
for card in personal_cc_definitions:
    c_name = card["name"]
    spent = df_tx[(df_tx["Account"] == c_name) & (df_tx["Type"] == "Expense")]["Amount"].sum()
    paid = df_tx[(df_tx["Account"] == c_name) & (df_tx["Type"] == "CC Payment")]["Amount"].sum()
    current_bal = max(card["base"] + spent - paid, 0.0)
    
    next_due = get_next_recurring_date(card["due_day"], today_dt)
    next_close = get_next_recurring_date(card["close_day"], today_dt)
    pay_by_date = next_due - timedelta(days=1)
    
    card_dict = dict(card)
    card_dict["current_balance"] = current_bal
    card_dict["utilization"] = (current_bal / card["limit"]) * 100 if card["limit"] > 0 else 0.0
    card_dict["due_str"] = next_due.strftime("%b %d")
    card_dict["close_str"] = next_close.strftime("%b %d")
    card_dict["pay_by_str"] = f"By {pay_by_date.strftime('%b %d')}"
    live_personal_cc.append(card_dict)

# Build live business CC list with rolling dates
live_biz_cc = []
for card in biz_cc_definitions:
    c_name = card["name"]
    spent = df_tx[(df_tx["Account"] == c_name) & (df_tx["Type"] == "Expense")]["Amount"].sum()
    paid = df_tx[(df_tx["Account"] == c_name) & (df_tx["Type"] == "CC Payment")]["Amount"].sum()
    current_bal = max(card["base"] + spent - paid, 0.0)
    
    next_due = get_next_recurring_date(card["due_day"], today_dt)
    next_close = get_next_recurring_date(card["close_day"], today_dt)
    pay_by_date = next_due - timedelta(days=1)
    
    card_dict = dict(card)
    card_dict["current_balance"] = current_bal
    card_dict["due_str"] = next_due.strftime("%b %d")
    card_dict["close_str"] = next_close.strftime("%b %d")
    card_dict["pay_by_str"] = f"By {pay_by_date.strftime('%b %d')}"
    live_biz_cc.append(card_dict)

total_cash = sum(c["base"] for c in cash_registry)
personal_cc_debt = sum(c["current_balance"] for c in live_personal_cc)
personal_cc_limit = sum(c["limit"] for c in live_personal_cc)
personal_utilization = (personal_cc_debt / personal_cc_limit) * 100 if personal_cc_limit > 0 else 0.0

biz_cc_debt = sum(c["current_balance"] for c in live_biz_cc)
total_all_debt = personal_cc_debt + biz_cc_debt
net_liquid_cash = total_cash - total_all_debt

HOME_GOAL = 26500.00
goal_progress = min(total_cash / HOME_GOAL, 1.0)
remaining_goal = max(HOME_GOAL - total_cash, 0.0)

# ==========================================
# 4. AI EXECUTIVE SUMMARY
# ==========================================
def generate_ai_insights():
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = f"""
            Act as an elite financial advisor. Provide a concise 2-sentence update:
            - Net Liquid Cash: ${net_liquid_cash:,.2f} (Total Cash: ${total_cash:,.2f}, Personal CCs: ${personal_cc_debt:,.2f}, Biz CC: ${biz_cc_debt:,.2f}).
            - Personal Credit Util: {personal_utilization:.2f}% across ${personal_cc_limit:,.2f} limit.
            - Upcoming Actions: Pay BofA 5309 and BofA 7197 by Aug 23. Pay Chase 1993 and Chase 0431 by Aug 31. Keep Chase 2207 at $9.52 for AZEO boost.
            """
            response = model.generate_content(prompt)
            return response.text.replace("$", r"\$")
    except Exception:
        pass
    return r"💡 **Key Next Steps:** Pay off BofA 5309 (\$22.21) & BofA 7197 (\$37.12) by August 23 to report \$0 on statement close. Maintain Chase 2207 at ~\$10 for AZEO personal credit optimization."

# ==========================================
# 5. APP TABS
# ==========================================
tabs = st.tabs(["⚡ Command Center", "📊 Analytics & Charts", "💳 Accounts & Credit Hub", "🏠 Home Goal"])

# ------------------------------------------
# TAB 1: COMMAND CENTER
# ------------------------------------------
with tabs[0]:
    st.markdown(f"""
    <div class="hero-card">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="font-weight:700; font-size:15px;">💵 Net Liquid Cash</span>
            <span style="color:#93C5FD; font-size:12px;">Personal Util: {personal_utilization:.2f}%</span>
        </div>
        <div class="metric-val">${net_liquid_cash:,.2f}</div>
        <div class="metric-sub">Total Cash: ${total_cash:,.2f} | Personal Debt: ${personal_cc_debt:,.2f} | Biz Debt: ${biz_cc_debt:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.info(generate_ai_insights())

    st.subheader("⚡ Fast Entry")
    tab_exp, tab_inc, tab_pay = st.tabs(["💸 Expense", "💵 Income", "🔄 CC Payment"])
    
    account_dropdown = [
        "Chase 1993 (Primary Daily)",
        "Chase 0431 (Business CC)",
        "Chase 2207 (AZEO 1%)",
        "BofA 5309",
        "BofA 7197",
        "Apple 1765",
        "TJX",
        "BofA 5522 (Checking)",
        "SECU 4987 (Savings / Home Fund)"
    ]
    
    categories_list = [
        "Groceries & Food", "Vehicle & Gas", "Housing & Rent", 
        "Dining Out & Coffee", "Utilities & Phone", "Personal & Entertainment", 
        "Subscriptions & Software", "Business Operations", "Miscellaneous / Buffer"
    ]

    with tab_exp:
        with st.form("log_expense_form", clear_on_submit=True):
            amt = st.number_input("Amount ($)", min_value=0.01, step=1.00, format="%.2f", key="f_exp_amt")
            selected_acc = st.selectbox("Card / Account", account_dropdown, index=0, key="f_exp_acc")
            selected_cat = st.selectbox("Category", categories_list, key="f_exp_cat")
            vendor = st.text_input("Merchant / Description", placeholder="e.g. Shell, Trader Joe's, Chipotle", key="f_exp_ven")
            entry_date = st.date_input("Date", value=datetime.today(), key="f_exp_date")
            goal_tag = st.selectbox("Goal Tag", ["General Living", "Baltimore 1st Home", "Emergency Vault", "Business"], key="f_exp_gt")
            
            if st.form_submit_button("Record Expense"):
                clean_acc = selected_acc.split(" (")[0]
                tx_id = f"TX-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                date_str = entry_date.strftime("%Y-%m-%d")
                
                new_row_values = [
                    tx_id,
                    date_str,
                    clean_acc,
                    "Expense",
                    selected_cat,
                    vendor,
                    float(amt),
                    goal_tag,
                    "Mobile App Entry"
                ]
                try:
                    append_tx_to_sheet(new_row_values)
                    st.success(f"✅ Successfully written to Google Sheets: ${amt:.2f} to {selected_cat} on {clean_acc}!")
                    st.rerun()
                except Exception as err:
                    st.error(f"❌ Write Error: {err}")

    with tab_inc:
        with st.form("log_income_form", clear_on_submit=True):
            inc_amt = st.number_input("Amount ($)", min_value=0.01, step=1.00, format="%.2f", key="f_inc_amt")
            inc_acc = st.selectbox("Deposit Into", ["BofA 5522 (Checking)", "SECU 4987 (Savings / Home Fund)"], key="f_inc_acc")
            inc_cat = st.selectbox("Income Source", ["W2 Salary", "Uber Income", "Other Income"], key="f_inc_cat")
            inc_desc = st.text_input("Note", placeholder="e.g. Bi-weekly Paycheck, Uber Payout", key="f_inc_desc")
            inc_date = st.date_input("Date", value=datetime.today(), key="f_inc_date")
            
            if st.form_submit_button("Record Income"):
                clean_inc_acc = inc_acc.split(" (")[0]
                tx_id = f"TX-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                date_str = inc_date.strftime("%Y-%m-%d")
                goal = "Baltimore 1st Home" if "SECU" in clean_inc_acc else "General Living"
                
                new_row_values = [
                    tx_id,
                    date_str,
                    clean_inc_acc,
                    "Income",
                    inc_cat,
                    inc_desc,
                    float(inc_amt),
                    goal,
                    "Mobile App Entry"
                ]
                try:
                    append_tx_to_sheet(new_row_values)
                    st.success(f"✅ Logged ${inc_amt:.2f} {inc_cat} into {clean_inc_acc}!")
                    st.rerun()
                except Exception as err:
                    st.error(f"❌ Write Error: {err}")

    with tab_pay:
        with st.form("log_payment_form", clear_on_submit=True):
            pay_amt = st.number_input("Payment Amount ($)", min_value=0.01, step=1.00, format="%.2f", key="f_pay_amt")
            from_account = st.selectbox("Paid From", ["BofA 5522 (Checking)", "SECU 4987 (Savings)"], key="f_pay_from")
            all_ccs = [c["name"] for c in personal_cc_definitions] + [c["name"] for c in biz_cc_definitions]
            target_card = st.selectbox("Credit Card Paid", all_ccs, key="f_pay_to")
            pay_date = st.date_input("Date", value=datetime.today(), key="f_pay_date")
            
            if st.form_submit_button("Record CC Payment"):
                clean_from = from_account.split(" (")[0]
                tx_id = f"TX-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                date_str = pay_date.strftime("%Y-%m-%d")
                
                new_row_values = [
                    tx_id,
                    date_str,
                    target_card,
                    "CC Payment",
                    "CC Payment",
                    f"Paid from {clean_from}",
                    float(pay_amt),
                    "General Living",
                    "Mobile App Entry"
                ]
                try:
                    append_tx_to_sheet(new_row_values)
                    st.success(f"✅ Recorded ${pay_amt:.2f} payment to {target_card}!")
                    st.rerun()
                except Exception as err:
                    st.error(f"❌ Write Error: {err}")

# ------------------------------------------
# TAB 2: ANALYTICS & CHARTS (STACKED BLOCKS)
# ------------------------------------------
with tabs[1]:
    st.subheader("📊 Financial Analytics & Trends")

    if "selected_date" not in st.session_state:
        st.session_state.selected_date = date.today()

    # Global Calendar Jump
    with st.expander("📅 Jump to Specific Date / Past Year", expanded=False):
        picked_date = st.date_input(
            "Select any date to view historical analytics:",
            value=st.session_state.selected_date,
            key="jump_calendar_picker"
        )
        if picked_date != st.session_state.selected_date:
            st.session_state.selected_date = picked_date
            st.rerun()

    ref_date = st.session_state.selected_date

    # Prepare DataFrame
    df_clean = df_tx.copy() if (df_tx is not None and not df_tx.empty) else pd.DataFrame(columns=["Date", "Type", "Category", "Amount"])
    if not df_clean.empty and "Date" in df_clean.columns:
        df_clean["Date_DT"] = pd.to_datetime(df_clean["Date"], errors="coerce").dt.date
        df_clean["Amount"] = pd.to_numeric(df_clean["Amount"], errors="coerce").fillna(0.0)
    else:
        df_clean["Date_DT"] = pd.Series(dtype="object")

    # ==========================================
    # BLOCK 1: WEEKLY ANALYTICS (TOP BLOCK)
    # ==========================================
    week_start = ref_date - timedelta(days=ref_date.weekday())
    week_end = week_start + timedelta(days=6)

    st.markdown("### 🗓️ Weekly Analytics")
    
    w_col1, w_col2, w_col3 = st.columns([1, 4, 1])
    with w_col1:
        if st.button("◀", key="prev_week_btn", help="Previous Week"):
            st.session_state.selected_date = ref_date - timedelta(days=7)
            st.rerun()
    with w_col2:
        st.markdown(
            f"<div style='text-align:center; font-weight:700; font-size:14px; color:#38BDF8; padding-top:8px;'>"
            f"{week_start.strftime('%b %d')} – {week_end.strftime('%b %d, %Y')}</div>",
            unsafe_allow_html=True
        )
    with w_col3:
        if st.button("▶", key="next_week_btn", help="Next Week"):
            st.session_state.selected_date = ref_date + timedelta(days=7)
            st.rerun()

    df_week = df_clean[(df_clean["Date_DT"] >= week_start) & (df_clean["Date_DT"] <= week_end)] if not df_clean.empty else pd.DataFrame()

    w_income = df_week[df_week["Type"] == "Income"]["Amount"].sum() if not df_week.empty else 0.0
    w_expense = df_week[df_week["Type"] == "Expense"]["Amount"].sum() if not df_week.empty else 0.0
    w_net = w_income - w_expense

    ws_1, ws_2, ws_3 = st.columns(3)
    with ws_1:
        st.markdown(f"""<div class="stat-box"><div style="font-size:10px; color:#94A3B8;">INCOME</div><div style="font-size:15px; font-weight:700; color:#34D399;">+${w_income:,.2f}</div></div>""", unsafe_allow_html=True)
    with ws_2:
        st.markdown(f"""<div class="stat-box"><div style="font-size:10px; color:#94A3B8;">EXPENSES</div><div style="font-size:15px; font-weight:700; color:#F87171;">-${w_expense:,.2f}</div></div>""", unsafe_allow_html=True)
    with ws_3:
        net_color = "#38BDF8" if w_net >= 0 else "#F87171"
        st.markdown(f"""<div class="stat-box"><div style="font-size:10px; color:#94A3B8;">NET CASH</div><div style="font-size:15px; font-weight:700; color:{net_color};">${w_net:,.2f}</div></div>""", unsafe_allow_html=True)

    w_exp_df = df_week[df_week["Type"] == "Expense"] if not df_week.empty else pd.DataFrame()
    if not w_exp_df.empty:
        w_cat_summary = w_exp_df.groupby("Category")["Amount"].sum().reset_index()
        fig_week_pie = px.pie(
            w_cat_summary, values="Amount", names="Category", hole=0.5,
            title=f"Week of {week_start.strftime('%b %d')} Spending",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_week_pie.update_layout(
            margin=dict(l=10, r=10, t=35, b=10), height=260, showlegend=True,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#CBD5E1")
        )
        st.plotly_chart(fig_week_pie, use_container_width=True)
    else:
        st.caption("ℹ️ No expenses recorded for this specific week.")

    st.divider()

    # ==========================================
    # BLOCK 2: MONTHLY ANALYTICS (BOTTOM BLOCK)
    # ==========================================
    m_year, m_month = ref_date.year, ref_date.month
    month_start = date(m_year, m_month, 1)
    last_day_num = calendar.monthrange(m_year, m_month)[1]
    month_end = date(m_year, m_month, last_day_num)

    st.markdown("### 📆 Monthly Analytics")
    
    m_col1, m_col2, m_col3 = st.columns([1, 4, 1])
    with m_col1:
        if st.button("◀", key="prev_month_btn", help="Previous Month"):
            prev_m = m_month - 1 if m_month > 1 else 12
            prev_y = m_year if m_month > 1 else m_year - 1
            st.session_state.selected_date = date(prev_y, prev_m, 1)
            st.rerun()
    with m_col2:
        st.markdown(
            f"<div style='text-align:center; font-weight:700; font-size:16px; color:#38BDF8; padding-top:8px;'>"
            f"{month_start.strftime('%B %Y')}</div>",
            unsafe_allow_html=True
        )
    with m_col3:
        if st.button("▶", key="next_month_btn", help="Next Month"):
            next_m = m_month + 1 if m_month < 12 else 1
            next_y = m_year if m_month < 12 else m_year + 1
            st.session_state.selected_date = date(next_y, next_m, 1)
            st.rerun()

    df_month = df_clean[(df_clean["Date_DT"] >= month_start) & (df_clean["Date_DT"] <= month_end)] if not df_clean.empty else pd.DataFrame()

    m_income = df_month[df_month["Type"] == "Income"]["Amount"].sum() if not df_month.empty else 0.0
    m_expense = df_month[df_month["Type"] == "Expense"]["Amount"].sum() if not df_month.empty else 0.0
    m_net = m_income - m_expense

    ms_1, ms_2, ms_3 = st.columns(3)
    with ms_1:
        st.markdown(f"""<div class="stat-box"><div style="font-size:10px; color:#94A3B8;">MONTH INCOME</div><div style="font-size:15px; font-weight:700; color:#34D399;">+${m_income:,.2f}</div></div>""", unsafe_allow_html=True)
    with ms_2:
        st.markdown(f"""<div class="stat-box"><div style="font-size:10px; color:#94A3B8;">MONTH EXPENSES</div><div style="font-size:15px; font-weight:700; color:#F87171;">-${m_expense:,.2f}</div></div>""", unsafe_allow_html=True)
    with ms_3:
        m_net_color = "#38BDF8" if m_net >= 0 else "#F87171"
        st.markdown(f"""<div class="stat-box"><div style="font-size:10px; color:#94A3B8;">MONTH NET</div><div style="font-size:15px; font-weight:700; color:{m_net_color};">${m_net:,.2f}</div></div>""", unsafe_allow_html=True)

    m_exp_df = df_month[df_month["Type"] == "Expense"] if not df_month.empty else pd.DataFrame()
    if not m_exp_df.empty:
        m_cat_summary = m_exp_df.groupby("Category")["Amount"].sum().reset_index()
        fig_month_pie = px.pie(
            m_cat_summary, values="Amount", names="Category", hole=0.55,
            title=f"{month_start.strftime('%B %Y')} Full Breakdown",
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        fig_month_pie.update_layout(
            margin=dict(l=10, r=10, t=35, b=10), height=280, showlegend=True,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#CBD5E1")
        )
        st.plotly_chart(fig_month_pie, use_container_width=True)
    else:
        st.caption(f"ℹ️ No expenses recorded yet for {month_start.strftime('%B %Y')}.")

    # Clickable weeks inside this month
    st.markdown("#### 🔍 Jump to a Week in this Month:")
    curr_w_start = month_start - timedelta(days=month_start.weekday())
    week_buttons = []
    while curr_w_start <= month_end:
        curr_w_end = curr_w_start + timedelta(days=6)
        week_buttons.append((curr_w_start, curr_w_end))
        curr_w_start += timedelta(days=7)

    for i in range(0, len(week_buttons), 2):
        b_cols = st.columns(2)
        for j, (w_s, w_e) in enumerate(week_buttons[i:i+2]):
            with b_cols[j]:
                label = f"{w_s.strftime('%b %d')} – {w_e.strftime('%b %d')}"
                if st.button(f"🔎 {label}", key=f"btn_w_{w_s.strftime('%Y%m%d')}"):
                    st.session_state.selected_date = w_s
                    st.rerun()

# ------------------------------------------
# TAB 3: ACCOUNTS & CREDIT HUB
# ------------------------------------------
with tabs[2]:
    st.subheader("🏦 Cash & Checking Spread")
    st.caption("How your liquid cash is distributed across checking and savings.")
    
    for acc in cash_registry:
        pct_of_total = (acc["base"] / total_cash) * 100 if total_cash > 0 else 0.0
        st.markdown(f"""
        <div style="background:#1E293B; border-radius:10px; padding:12px 14px; margin-bottom:8px; border:1px solid #334155;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <span style="font-weight:700; font-size:15px; color:#F8FAFC;">{acc['name']}</span>
                    <div style="font-size:12px; color:#94A3B8;">{acc['role']}</div>
                </div>
                <div style="text-align:right;">
                    <span style="font-weight:700; font-size:16px; color:#38BDF8;">${acc['base']:,.2f}</span>
                    <div style="font-size:11px; color:#64748B;">{pct_of_total:.1f}% of cash</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    st.subheader("💳 Personal Credit Cards (AZEO Strategy)")
    st.caption(f"Overall Personal Util: **{personal_utilization:.2f}%** (${personal_cc_debt:,.2f} / ${personal_cc_limit:,.2f}). Maintain **Chase 2207** at ~$10 and all others at $0.")
    
    for c in live_personal_cc:
        bal = c["current_balance"]
        limit = c["limit"]
        util = c["utilization"]
        
        if c.get("is_azeo_active"):
            badge = '<span class="badge-opt">✅ AZEO ACTIVE (~1%)</span>'
            action = f"Leave ~{c['target']} to report on {c['close_str']}"
        elif bal > 0:
            badge = '<span class="badge-warn">⚠️ PAY TO $0</span>'
            action = f"Pay ${bal:.2f} {c['pay_by_str']} (Due {c['due_str']})"
        else:
            badge = '<span class="badge-opt">✅ ZERO REPORTING ($0)</span>'
            action = f"Next Due: {c['due_str']} | Closes: {c['close_str']}"
            
        st.markdown(f"""
        <div style="background:#1E293B; border-radius:10px; padding:12px 14px; margin-bottom:8px; border:1px solid #334155;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <span style="font-weight:700; font-size:15px; color:#F8FAFC;">{c['name']}</span>
                    <span style="font-size:12px; color:#64748B; margin-left:6px;">Limit: ${limit:,.0f}</span>
                </div>
                <div style="text-align:right;">
                    <span style="font-weight:700; font-size:15px; color:#F8FAFC;">${bal:.2f}</span>
                    <span style="font-size:11px; color:#94A3B8; margin-left:4px;">({util:.1f}%)</span>
                </div>
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-top:6px;">
                <span style="font-size:12px; color:#CBD5E1;">{action}</span>
                <div>{badge}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    st.subheader("💼 Business Credit Cards")
    st.caption("Business cards do not report to your personal credit score.")
    
    for c in live_biz_cc:
        st.markdown(f"""
        <div style="background:#1E293B; border-radius:10px; padding:12px 14px; margin-bottom:8px; border:1px solid #334155;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <span style="font-weight:700; font-size:15px; color:#F8FAFC;">{c['name']}</span>
                    <span style="font-size:12px; color:#64748B; margin-left:6px;">Business Card</span>
                </div>
                <div style="text-align:right;">
                    <span style="font-weight:700; font-size:15px; color:#F8FAFC;">${c['current_balance']:.2f}</span>
                </div>
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-top:6px;">
                <span style="font-size:12px; color:#CBD5E1;">Due: {c['due_str']} | Closes: {c['close_str']} ({c['pay_by_str']})</span>
                <div><span class="badge-biz">💼 BUSINESS</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ------------------------------------------
# TAB 4: GOALS HUB
# ------------------------------------------
with tabs[3]:
    st.subheader("🏠 Baltimore Home Purchase Target")
    st.progress(goal_progress)
    st.caption(f"**${total_cash:,.2f}** saved of **${HOME_GOAL:,.2f}** goal ({(goal_progress*100):.1f}%)")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"""
        <div class="stat-box">
            <div style="font-size:11px; color:#94A3B8;">REMAINING GOAL</div>
            <div style="font-size:18px; font-weight:700; color:#38BDF8;">${remaining_goal:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with col_b:
        st.markdown(f"""
        <div class="stat-box">
            <div style="font-size:11px; color:#94A3B8;">TARGET DEADLINE</div>
            <div style="font-size:16px; font-weight:700; color:#34D399;">March 1, 2027</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("""
    ---
    **10% Down Acquisition Strategy Summary:**
    * **Target Price:** $300,000 | **Down Payment (10%):** $30,000
    * **Estimated Closing & Prepaids:** $11,000
    * **Credits & Assistance Applied:** -$21,000
      * *2.5% Buyer Agent Commission Credit:* -$7,500
      * *Maryland Mortgage Program (MMP) DPA:* -$9,000
      * *Seller Concessions (1.5%):* -$4,500
    * **Net Cash at Closing:** $20,000
    * **Post-Closing 3-Mo Reserves:** $6,500
    * **Total Liquid Target:** **$26,500**
    """)
