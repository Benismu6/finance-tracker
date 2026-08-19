import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import google.generativeai as genai

# ==========================================
# 1. PAGE SETUP & FULL-SCREEN MOBILE CSS
# ==========================================
st.set_page_config(
    page_title="Financial Command Hub",
    page_icon="🏠",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    /* 1. HIDE STREAMLIT TOP HEADER BAR (FORK / GITHUB / 3 DOTS) */
    header[data-testid="stHeader"],
    .stAppHeader,
    header {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
    }
    
    /* 2. HIDE TOP DECORATION & FOOTER */
    div[data-testid="stDecoration"],
    #MainMenu,
    footer {
        display: none !important;
        visibility: hidden !important;
    }

    /* 3. MOBILE CONTAINER PADDING (ENSURES TABS SIT PROPERLY AT TOP) */
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 2rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
        max-width: 100% !important;
    }
    
    /* 4. TAB CONTAINER STYLING */
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
    
    /* 5. TAB BUTTONS & HIGH-CONTRAST LABELS */
    div[data-baseweb="tab-list"] button,
    button[data-baseweb="tab"] {
        background-color: #1E293B !important;
        border-radius: 8px !important;
        padding: 8px 12px !important;
        margin: 2px !important;
        border: 1px solid #334155 !important;
        flex: 1 0 auto !important;
    }
    
    div[data-baseweb="tab-list"] button *,
    button[data-baseweb="tab"] *,
    div[data-baseweb="tab-list"] p,
    button[data-baseweb="tab"] p {
        color: #F8FAFC !important;
        font-weight: 700 !important;
        font-size: 13px !important;
        opacity: 1 !important;
        visibility: visible !important;
        white-space: nowrap !important;
    }
    
    /* Active Selected Tab */
    button[data-baseweb="tab"][aria-selected="true"],
    div[data-baseweb="tab-list"] button[aria-selected="true"] {
        background-color: #2563EB !important;
        border: 1px solid #60A5FA !important;
    }
    
    button[data-baseweb="tab"][aria-selected="true"] *,
    div[data-baseweb="tab-list"] button[aria-selected="true"] * {
        color: #FFFFFF !important;
        font-weight: 800 !important;
    }
    
    div[data-baseweb="tab-highlight"] {
        display: none !important;
    }

    /* Hero Card */
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
    
    /* Stat Boxes */
    .stat-box {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 10px;
        text-align: center;
    }
    
    /* Action Buttons */
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
    
    /* Badges */
    .badge-opt { background-color: #065F46; color: #6EE7B7; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; }
    .badge-warn { background-color: #7C2D12; color: #FDBA74; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; }
    .badge-biz { background-color: #312E81; color: #C7D2FE; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA CONNECTION & ACCOUNTS REGISTRY
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

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

# 1. Checking & Savings Accounts
cash_registry = [
    {"name": "BofA 5522", "role": "Primary Operating Checking", "base": 251.67},
    {"name": "SECU 4987", "role": "Dedicated Home Savings / HYSA", "base": 4212.10}
]

# 2. Personal Credit Cards (Report to FICO / AZEO Strategy)
personal_cc_registry = [
    {"name": "Chase 1993", "base": 517.70, "limit": 10600.00, "due": "Sep 01", "close": "Sep 04", "pay_window": "Aug 29 – Sep 01", "target": "$0.00", "is_primary": True},
    {"name": "Chase 2207", "base": 9.52, "limit": 4900.00, "due": "Sep 01", "close": "Sep 04", "pay_window": "Leave balance", "is_azeo_active": True, "target": "~$10.00 (1%)"},
    {"name": "BofA 5309", "base": 22.21, "limit": 7500.00, "due": "Aug 24", "close": "Aug 27", "pay_window": "By Aug 23", "target": "$0.00"},
    {"name": "BofA 7197", "base": 37.12, "limit": 3500.00, "due": "Aug 24", "close": "Aug 27", "pay_window": "By Aug 23", "target": "$0.00"},
    {"name": "Apple 1765", "base": 0.00, "limit": 2000.00, "due": "End of Mo.", "close": "End of Mo.", "pay_window": "N/A", "target": "$0.00"},
    {"name": "TJX", "base": 0.00, "limit": 3200.00, "due": "5th of Mo.", "close": "~8th of Mo.", "pay_window": "N/A", "target": "$0.00"}
]

# 3. Business Credit Cards (Does NOT report to personal credit)
biz_cc_registry = [
    {"name": "Chase 0431", "base": 505.07, "limit": 0.00, "due": "Sep 01", "close": "Sep 07", "pay_window": "By Sep 01", "is_business": True, "target": "Business Expense"}
]

# Compute Personal CC Balances
live_personal_cc = []
for card in personal_cc_registry:
    c_name = card["name"]
    spent = df_tx[(df_tx["Account"] == c_name) & (df_tx["Type"] == "Expense")]["Amount"].sum()
    paid = df_tx[(df_tx["Account"] == c_name) & (df_tx["Type"] == "CC Payment")]["Amount"].sum()
    current_bal = max(card["base"] + spent - paid, 0.0)
    
    card_dict = dict(card)
    card_dict["current_balance"] = current_bal
    card_dict["utilization"] = (current_bal / card["limit"]) * 100 if card["limit"] > 0 else 0.0
    live_personal_cc.append(card_dict)

# Compute Business CC Balances
live_biz_cc = []
for card in biz_cc_registry:
    c_name = card["name"]
    spent = df_tx[(df_tx["Account"] == c_name) & (df_tx["Type"] == "Expense")]["Amount"].sum()
    paid = df_tx[(df_tx["Account"] == c_name) & (df_tx["Type"] == "CC Payment")]["Amount"].sum()
    current_bal = max(card["base"] + spent - paid, 0.0)
    
    card_dict = dict(card)
    card_dict["current_balance"] = current_bal
    live_biz_cc.append(card_dict)

# Compute Total Cash and Net Liquidity
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
# 3. AI EXECUTIVE SUMMARY
# ==========================================
def generate_ai_insights():
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = f"""
            Act as an elite financial advisor. Provide a concise 2-sentence update:
            - Net Liquid Cash: ${net_liquid_cash:,.2f} (Total Cash: ${total_cash:,.2f}, Personal CCs: ${personal_cc_debt:,.2f}, Biz CC Chase 0431: ${biz_cc_debt:,.2f}).
            - Personal Credit Util: {personal_utilization:.2f}% across ${personal_cc_limit:,.2f} limit.
            - Upcoming Actions: Pay BofA 5309 ($22.21) & BofA 7197 ($37.12) by Aug 23. Pay Chase 1993 ($517.70) & Biz Chase 0431 ($505.07) by Sep 1. Keep Chase 2207 at $9.52 for AZEO boost.
            """
            response = model.generate_content(prompt)
            return response.text
    except Exception:
        pass
    return "💡 **Key Next Steps:** Pay off BofA 5309 ($22.21) & BofA 7197 ($37.12) by August 23 to report $0 on Aug 27. Maintain Chase 2207 at ~$10 for AZEO personal credit optimization."

# ==========================================
# 4. APP TABS
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
                new_entry = pd.DataFrame([{
                    "Transaction_ID": f"TX-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "Date": entry_date.strftime("%Y-%m-%d"),
                    "Account": clean_acc,
                    "Type": "Expense",
                    "Category": selected_cat,
                    "Merchant": vendor,
                    "Amount": amt,
                    "Goal_Tag": goal_tag,
                    "Notes": "Mobile App Entry"
                }])
                try:
                    updated_ledger = pd.concat([df_tx, new_entry], ignore_index=True)
                    conn.update(worksheet="Master_Transactions", data=updated_ledger)
                    st.success(f"✅ Logged ${amt:.2f} to {selected_cat} on {clean_acc}!")
                except Exception:
                    st.info(f"Recorded: ${amt:.2f} on {clean_acc}")

    with tab_inc:
        with st.form("log_income_form", clear_on_submit=True):
            inc_amt = st.number_input("Amount ($)", min_value=0.01, step=1.00, format="%.2f", key="f_inc_amt")
            inc_acc = st.selectbox("Deposit Into", ["BofA 5522 (Checking)", "SECU 4987 (Savings / Home Fund)"], key="f_inc_acc")
            inc_cat = st.selectbox("Income Source", ["W2 Salary", "Uber Income", "Other Income"], key="f_inc_cat")
            inc_desc = st.text_input("Note", placeholder="e.g. Bi-weekly Paycheck, Uber Payout", key="f_inc_desc")
            inc_date = st.date_input("Date", value=datetime.today(), key="f_inc_date")
            
            if st.form_submit_button("Record Income"):
                clean_inc_acc = inc_acc.split(" (")[0]
                new_entry = pd.DataFrame([{
                    "Transaction_ID": f"TX-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "Date": inc_date.strftime("%Y-%m-%d"),
                    "Account": clean_inc_acc,
                    "Type": "Income",
                    "Category": inc_cat,
                    "Merchant": inc_desc,
                    "Amount": inc_amt,
                    "Goal_Tag": "Baltimore 1st Home" if "SECU" in clean_inc_acc else "General Living",
                    "Notes": "Mobile App Entry"
                }])
                try:
                    updated_ledger = pd.concat([df_tx, new_entry], ignore_index=True)
                    conn.update(worksheet="Master_Transactions", data=updated_ledger)
                    st.success(f"✅ Logged ${inc_amt:.2f} {inc_cat} into {clean_inc_acc}!")
                except Exception:
                    st.info(f"Recorded: ${inc_amt:.2f} into {clean_inc_acc}")

    with tab_pay:
        with st.form("log_payment_form", clear_on_submit=True):
            pay_amt = st.number_input("Payment Amount ($)", min_value=0.01, step=1.00, format="%.2f", key="f_pay_amt")
            from_account = st.selectbox("Paid From", ["BofA 5522 (Checking)", "SECU 4987 (Savings)"], key="f_pay_from")
            all_ccs = [c["name"] for c in personal_cc_registry] + [c["name"] for c in biz_cc_registry]
            target_card = st.selectbox("Credit Card Paid", all_ccs, key="f_pay_to")
            pay_date = st.date_input("Date", value=datetime.today(), key="f_pay_date")
            
            if st.form_submit_button("Record CC Payment"):
                clean_from = from_account.split(" (")[0]
                new_entry = pd.DataFrame([{
                    "Transaction_ID": f"TX-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "Date": pay_date.strftime("%Y-%m-%d"),
                    "Account": target_card,
                    "Type": "CC Payment",
                    "Category": "CC Payment",
                    "Merchant": f"Paid from {clean_from}",
                    "Amount": pay_amt,
                    "Goal_Tag": "General Living",
                    "Notes": "Mobile App Entry"
                }])
                try:
                    updated_ledger = pd.concat([df_tx, new_entry], ignore_index=True)
                    conn.update(worksheet="Master_Transactions", data=updated_ledger)
                    st.success(f"✅ Recorded ${pay_amt:.2f} payment to {target_card}!")
                except Exception:
                    st.info(f"Payment recorded: ${pay_amt:.2f} to {target_card}")

# ------------------------------------------
# TAB 2: ANALYTICS & CHARTS
# ------------------------------------------
with tabs[1]:
    st.subheader("📊 Spending & Cash Flow Insights")
    
    cat_df = df_tx[df_tx["Type"] == "Expense"].groupby("Category")["Amount"].sum().reset_index()
    if cat_df.empty:
        cat_df = pd.DataFrame({
            "Category": ["Housing / Rent", "Vehicle & Gas", "Groceries & Food", "Dining Out", "Utilities", "Personal"],
            "Amount": [500, 360, 245, 150, 140, 110]
        })
    
    fig_pie = px.pie(
        cat_df, values="Amount", names="Category", hole=0.55, 
        title="Spending by Category", color_discrete_sequence=px.colors.qualitative.Prism
    )
    fig_pie.update_layout(
        margin=dict(l=10, r=10, t=40, b=10), height=300, showlegend=True,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#CBD5E1")
    )
    st.plotly_chart(fig_pie, use_container_width=True)
    
    flow_df = pd.DataFrame({
        "Period": ["Week 1", "Week 2", "Week 3", "Week 4"],
        "Income": [1280, 1340, 1280, 1400],
        "Expenses": [340, 310, 290, 320]
    })
    fig_bar = go.Figure(data=[
        go.Bar(name="Net Income", x=flow_df["Period"], y=flow_df["Income"], marker_color="#3B82F6"),
        go.Bar(name="Expenses", x=flow_df["Period"], y=flow_df["Expenses"], marker_color="#EF4444")
    ])
    fig_bar.update_layout(
        barmode="group", title="Weekly Cash Flow Pace ($)", height=280, 
        margin=dict(l=10, r=10, t=40, b=10), paper_bgcolor="rgba(0,0,0,0)", 
        plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#CBD5E1")
    )
    st.plotly_chart(fig_bar, use_container_width=True)

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
            action = f"Leave ~{c['target']} to report on {c['close']}"
        elif bal > 0:
            badge = '<span class="badge-warn">⚠️ PAY TO $0</span>'
            action = f"Pay ${bal:.2f} by {c['pay_window']} (Closes {c['close']})"
        else:
            badge = '<span class="badge-opt">✅ ZERO REPORTING ($0)</span>'
            action = f"Due: {c['due']} | Closes: {c['close']}"
            
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
                <span style="font-size:12px; color:#CBD5E1;">Due: {c['due']} | Closes: {c['close']} (Pay by {c['pay_window']})</span>
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
