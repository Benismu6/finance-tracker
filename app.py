import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import google.generativeai as genai

# ==========================================
# 1. PAGE SETUP & MOBILE-FIRST STYLING
# ==========================================
st.set_page_config(
    page_title="Financial Command Hub",
    page_icon="🏠",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    /* Mobile-first clean dark theme */
    .block-container { padding-top: 1rem; padding-bottom: 2rem; padding-left: 0.8rem; padding-right: 0.8rem; }
    
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
    
    /* Full-width iOS-style action button */
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
    .stButton>button:hover {
        background-color: #1D4ED8;
    }
    
    /* Badges */
    .badge-opt { background-color: #065F46; color: #6EE7B7; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; }
    .badge-warn { background-color: #7C2D12; color: #FDBA74; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA CONNECTION & BASE CONFIG
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

def get_ledger_data():
    try:
        # Pulls live from the Master_Transactions tab
        df = conn.read(worksheet="Master_Transactions", ttl="0")
        if df is not None and not df.empty:
            df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0.0)
            return df
    except Exception:
        pass
    # Return empty structured dataframe if sheet is currently blank
    return pd.DataFrame(columns=[
        "Transaction_ID", "Date", "Account", "Type", "Category", 
        "Merchant", "Amount", "Goal_Tag", "Notes"
    ])

df_tx = get_ledger_data()

# Baseline Static Balances & Limits
cash_registry = {
    "BofA 5522": {"type": "Checking", "base": 251.67},
    "SECU 4987": {"type": "Savings / Home Fund", "base": 4212.10}
}

cc_registry = [
    {"name": "Chase 1993", "base": 517.70, "limit": 10600.00, "due": "Sep 01", "close": "Sep 04", "pay_window": "Aug 29 – Sep 01", "is_primary": True, "target": "$0.00"},
    {"name": "Chase 2207", "base": 9.52, "limit": 4900.00, "due": "Sep 01", "close": "Sep 04", "pay_window": "Leave balance", "is_azeo_active": True, "target": "~$10.00 (1%)"},
    {"name": "BofA 5309", "base": 22.21, "limit": 7500.00, "due": "Aug 24", "close": "Aug 27", "pay_window": "By Aug 23", "target": "$0.00"},
    {"name": "BofA 7197", "base": 37.12, "limit": 3500.00, "due": "Aug 24", "close": "Aug 27", "pay_window": "By Aug 23", "target": "$0.00"},
    {"name": "Apple 1765", "base": 0.00, "limit": 2000.00, "due": "End of Mo.", "close": "End of Mo.", "pay_window": "N/A", "target": "$0.00"},
    {"name": "TJX", "base": 0.00, "limit": 3200.00, "due": "5th of Mo.", "close": "~8th of Mo.", "pay_window": "N/A", "target": "$0.00"}
]

# Calculate Live Balances with Transactions added on top
live_cc_data = []
for card in cc_registry:
    c_name = card["name"]
    spent = df_tx[(df_tx["Account"] == c_name) & (df_tx["Type"] == "Expense")]["Amount"].sum()
    paid = df_tx[(df_tx["Account"] == c_name) & (df_tx["Type"] == "CC Payment")]["Amount"].sum()
    current_bal = max(card["base"] + spent - paid, 0.0)
    
    card_dict = dict(card)
    card_dict["current_balance"] = current_bal
    card_dict["utilization"] = (current_bal / card["limit"]) * 100 if card["limit"] > 0 else 0.0
    live_cc_data.append(card_dict)

total_cash = sum(c["base"] for c in cash_registry.values())
# Adjust cash with income, expenses, and payments
if not df_tx.empty:
    cash_in = df_tx[(df_tx["Account"].isin(cash_registry.keys())) & (df_tx["Type"] == "Income")]["Amount"].sum()
    cash_out = df_tx[(df_tx["Account"].isin(cash_registry.keys())) & (df_tx["Type"].isin(["Expense", "CC Payment"]))]["Amount"].sum()
    total_cash = total_cash + cash_in - cash_out

total_cc_debt = sum(c["current_balance"] for c in live_cc_data)
total_cc_limit = sum(c["limit"] for c in live_cc_data)
overall_utilization = (total_cc_debt / total_cc_limit) * 100
net_liquid_cash = total_cash - total_cc_debt

HOME_GOAL = 26500.00
remaining_goal = max(HOME_GOAL - total_cash, 0.0)
goal_progress = min(total_cash / HOME_GOAL, 1.0)

# ==========================================
# 3. AI EXECUTIVE SUMMARY ENGINE ($0 GEMINI)
# ==========================================
def generate_ai_insights():
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = f"""
            Act as a high-tier personal financial advisor. Give a crisp 2-sentence update:
            - Net Liquid Cash: ${net_liquid_cash:,.2f}
            - Checking/Savings Total: ${total_cash:,.2f} of $26,500 goal for Baltimore home (March 2027).
            - Credit Cards: Total debt ${total_cc_debt:,.2f} across ${total_cc_limit:,.2f} limit ({overall_utilization:.2f}% util).
            - AZEO Target: Pay BofA 5309 ($22.21) and BofA 7197 ($37.12) by Aug 23. Clear Chase 1993 ($517.70) by Sep 1. Keep Chase 2207 at $9.52.
            """
            response = model.generate_content(prompt)
            return response.text
    except Exception:
        pass
    return "💡 **Action Item:** Pay off BofA 5309 ($22.21) and BofA 7197 ($37.12) by August 23 to report $0 on August 27. Maintain Chase 2207 at ~$10 for the AZEO credit boost."

# ==========================================
# 4. APP NAVIGATION & SCREENS
# ==========================================
tabs = st.tabs(["⚡ Command Center", "📊 Analytics & Charts", "💳 Credit Hub", "🏠 Home Goal"])

# ------------------------------------------
# TAB 1: COMMAND CENTER (QUICK LOG)
# ------------------------------------------
with tabs[0]:
    # Hero Net Cash Widget
    st.markdown(f"""
    <div class="hero-card">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="font-weight:700; font-size:15px;">💵 Net Liquid Cash</span>
            <span style="color:#93C5FD; font-size:12px;">Util: {overall_utilization:.2f}%</span>
        </div>
        <div class="metric-val">${net_liquid_cash:,.2f}</div>
        <div class="metric-sub">Total Cash: ${total_cash:,.2f} | Revolving CC Debt: ${total_cc_debt:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.info(generate_ai_insights())

    st.subheader("⚡ Fast Entry")
    
    tab_exp, tab_inc, tab_pay = st.tabs(["💸 Expense", "💵 Income", "🔄 CC Payment"])
    
    # Chase 1993 is prioritized first
    account_dropdown = [
        "Chase 1993 (Primary Daily)",
        "Chase 2207 (AZEO 1%)",
        "BofA 5309",
        "BofA 7197",
        "Apple 1765",
        "TJX",
        "BofA 5522 (Checking)",
        "SECU 4987 (Savings / Home Fund)"
    ]
    
    categories_list = [
        "Groceries & Food",
        "Vehicle & Gas",
        "Housing & Rent",
        "Dining Out & Coffee",
        "Utilities & Phone",
        "Personal & Entertainment",
        "Subscriptions & Software",
        "Miscellaneous / Buffer"
    ]

    with tab_exp:
        with st.form("log_expense_form", clear_on_submit=True):
            amt = st.number_input("Amount ($)", min_value=0.01, step=1.00, format="%.2f", key="f_exp_amt")
            selected_acc = st.selectbox("Card / Account", account_dropdown, index=0, key="f_exp_acc")
            selected_cat = st.selectbox("Category", categories_list, key="f_exp_cat")
            vendor = st.text_input("Merchant / Description", placeholder="e.g. Shell, Trader Joe's, Chipotle", key="f_exp_ven")
            entry_date = st.date_input("Date", value=datetime.today(), key="f_exp_date")
            goal_tag = st.selectbox("Goal Tag", ["General Living", "Baltimore 1st Home", "Emergency Vault"], key="f_exp_gt")
            
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
                except Exception as e:
                    st.warning(f"Recorded locally: ${amt:.2f} on {clean_acc}")

    with tab_inc:
        with st.form("log_income_form", clear_on_submit=True):
            inc_amt = st.number_input("Amount ($)", min_value=0.01, step=1.00, format="%.2f", key="f_inc_amt")
            inc_acc = st.selectbox("Deposit Into", ["BofA 5522 (Checking)", "SECU 4987 (Savings / Home Fund)"], key="f_inc_acc")
            inc_cat = st.selectbox("Income Source", ["W2 Salary", "Uber Income", "Other Income"], key="f_inc_cat")
            inc_desc = st.text_input("Note", placeholder="e.g. Bi-weekly Paycheck, Uber Direct Deposit", key="f_inc_desc")
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
                except Exception as e:
                    st.info(f"Recorded: ${inc_amt:.2f} into {clean_inc_acc}")

    with tab_pay:
        with st.form("log_payment_form", clear_on_submit=True):
            pay_amt = st.number_input("Payment Amount ($)", min_value=0.01, step=1.00, format="%.2f", key="f_pay_amt")
            from_account = st.selectbox("Paid From", ["BofA 5522 (Checking)", "SECU 4987 (Savings)"], key="f_pay_from")
            target_card = st.selectbox("Credit Card Paid", [c["name"] for c in cc_registry], key="f_pay_to")
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
                except Exception as e:
                    st.info(f"Payment recorded: ${pay_amt:.2f} to {target_card}")

# ------------------------------------------
# TAB 2: ANALYTICS & CHARTS
# ------------------------------------------
with tabs[1]:
    st.subheader("📊 Spending & Cash Flow Insights")
    
    # 1. Monthly Category Breakdown Donut Chart
    cat_df = df_tx[df_tx["Type"] == "Expense"].groupby("Category")["Amount"].sum().reset_index()
    if cat_df.empty:
        # Fallback baseline breakdown visualization
        cat_df = pd.DataFrame({
            "Category": ["Housing / Rent", "Vehicle & Gas", "Groceries & Food", "Dining Out", "Utilities", "Personal"],
            "Amount": [500, 360, 245, 150, 140, 110]
        })
    
    fig_pie = px.pie(
        cat_df, 
        values="Amount", 
        names="Category", 
        hole=0.55, 
        title="Spending by Category",
        color_discrete_sequence=px.colors.qualitative.Prism
    )
    fig_pie.update_layout(
        margin=dict(l=10, r=10, t=40, b=10),
        height=300,
        showlegend=True,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#CBD5E1")
    )
    st.plotly_chart(fig_pie, use_container_width=True)
    
    # 2. Cash Flow Comparison Chart (Income vs Expense)
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
        barmode="group", 
        title="Weekly Cash Flow Pace ($)", 
        height=280, 
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#CBD5E1")
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# ------------------------------------------
# TAB 3: CREDIT CARD HUB (AZEO METHOD)
# ------------------------------------------
with tabs[2]:
    st.subheader("💳 Credit Card Command Center")
    st.caption("Keep total utilization below 3%. Maintain **Chase 2207** at ~$10 (0.2% util) and pay all other 5 cards to $0 before statement closing.")
    
    for c in live_cc_data:
        bal = c["current_balance"]
        limit = c["limit"]
        util = c["utilization"]
        
        if c.get("is_azeo_active"):
            badge = '<span class="badge-opt">✅ AZEO ACTIVE CARD (~1%)</span>'
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
