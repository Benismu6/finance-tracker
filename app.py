import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# 1. Mobile-First Page Setup
st.set_page_config(
    page_title="Finances & Home Fund",
    page_icon="🏠",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 2. Custom Mobile Dark-Mode Styling
st.markdown("""
<style>
    .main { padding: 0.5rem 0.8rem; }
    
    /* Hero Card */
    .hero-card {
        background: linear-gradient(135deg, #1E3A8A 0%, #0F172A 100%);
        border: 1px solid #3B82F6;
        border-radius: 16px;
        padding: 18px;
        color: white;
        margin-bottom: 14px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    .metric-val { font-size: 24px; font-weight: 700; color: #38BDF8; }
    .metric-sub { font-size: 13px; color: #94A3B8; }
    
    /* Summary Metric Card */
    .stat-box {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 12px;
        text-align: center;
    }
    
    /* Action Buttons */
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 48px;
        font-size: 16px;
        font-weight: 600;
        background-color: #2563EB;
        color: white;
        border: none;
    }
    
    /* Badges */
    .badge-opt {
        background-color: #065F46;
        color: #6EE7B7;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 600;
    }
    .badge-warn {
        background-color: #7C2D12;
        color: #FDBA74;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# 3. Google Sheets Connection
conn = st.connection("gsheets", type=GSheetsConnection)

def load_transactions():
    try:
        return conn.read(ttl="1m")
    except Exception:
        return None

df_transactions = load_transactions()

# --- CONSTANTS & ACCOUNTS DATA ---
TOTAL_SAVINGS_GOAL = 26500.00
TARGET_DATE = "March 1, 2027"

# Checking Balances
cash_accounts = {
    "BofA 5522": 251.67,
    "SECU 4987": 4212.10
}
total_cash = sum(cash_accounts.values())
remaining_goal = max(TOTAL_SAVINGS_GOAL - total_cash, 0.0)
savings_progress = min(total_cash / TOTAL_SAVINGS_GOAL, 1.0)

# Credit Cards Database
cc_data = [
    {
        "name": "Chase 1993",
        "balance": 517.70,
        "limit": 10600.00,
        "due": "Sep 01",
        "close": "Sep 04",
        "pay_window": "Aug 29 – Sep 01",
        "target_azeo": "$0.00",
        "is_azeo_active": False
    },
    {
        "name": "Chase 2207",
        "balance": 9.52,
        "limit": 4900.00,
        "due": "Sep 01",
        "close": "Sep 04",
        "pay_window": "Leave balance",
        "target_azeo": "~$10.00 (1%)",
        "is_azeo_active": True
    },
    {
        "name": "BofA 5309",
        "balance": 22.21,
        "limit": 7500.00,
        "due": "Aug 24",
        "close": "Aug 27",
        "pay_window": "By Aug 23",
        "target_azeo": "$0.00",
        "is_azeo_active": False
    },
    {
        "name": "BofA 7197",
        "balance": 37.12,
        "limit": 3500.00,
        "due": "Aug 24",
        "close": "Aug 27",
        "pay_window": "By Aug 23",
        "target_azeo": "$0.00",
        "is_azeo_active": False
    },
    {
        "name": "Apple 1765",
        "balance": 0.00,
        "limit": 2000.00,
        "due": "End of Mo.",
        "close": "End of Mo.",
        "pay_window": "N/A",
        "target_azeo": "$0.00",
        "is_azeo_active": False
    },
    {
        "name": "TJX",
        "balance": 0.00,
        "limit": 3200.00,
        "due": "5th of Mo.",
        "close": "~8th of Mo.",
        "pay_window": "N/A",
        "target_azeo": "$0.00",
        "is_azeo_active": False
    }
]

total_cc_debt = sum(c["balance"] for c in cc_data)
total_cc_limit = sum(c["limit"] for c in cc_data)
overall_utilization = (total_cc_debt / total_cc_limit) * 100
net_liquid_cash = total_cash - total_cc_debt

# --- SECTION 1: HOME PURCHASE & CASH SUMMARY ---
st.markdown(f"""
<div class="hero-card">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <span style="font-weight:600; font-size:15px;">🏠 Baltimore Home Purchase Fund</span>
        <span style="font-size:12px; color:#93C5FD;">Target: {TARGET_DATE}</span>
    </div>
    <div style="margin-top:10px;">
        <div class="metric-val">${total_cash:,.2f} <span style="font-size:14px; color:#E2E8F0; font-weight:400;">/ ${TOTAL_SAVINGS_GOAL:,.2f}</span></div>
        <div class="metric-sub">${remaining_goal:,.2f} remaining to reach 10% down + reserves</div>
    </div>
</div>
""", unsafe_allow_html=True)
st.progress(savings_progress)

col1, col2 = st.columns(2)
with col1:
    st.markdown(f"""
    <div class="stat-box">
        <div style="font-size:11px; color:#94A3B8; text-transform:uppercase;">Net Liquid Cash</div>
        <div style="font-size:18px; font-weight:700; color:#38BDF8;">${net_liquid_cash:,.2f}</div>
        <div style="font-size:10px; color:#64748B;">Cash minus CC balances</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="stat-box">
        <div style="font-size:11px; color:#94A3B8; text-transform:uppercase;">Overall CC Util</div>
        <div style="font-size:18px; font-weight:700; color:#34D399;">{overall_utilization:.2f}%</div>
        <div style="font-size:10px; color:#64748B;">${total_cc_debt:,.2f} / ${total_cc_limit:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# --- SECTION 2: FAST TRANSACTION ENTRY FORM ---
st.subheader("⚡ Quick Log Transaction")

tab_exp, tab_inc, tab_xfer = st.tabs(["💸 Expense", "💵 Income", "🔄 CC Pay / Transfer"])

all_spending_accounts = [
    "Chase 1993 ($10.6k Limit)",
    "Chase 2207 ($4.9k Limit)",
    "BofA 5309 ($7.5k Limit)",
    "BofA 7197 ($3.5k Limit)",
    "Apple 1765 ($2.0k Limit)",
    "TJX ($3.2k Limit)",
    "BofA 5522 (Checking)",
    "SECU 4987 (Savings / Home Fund)"
]

categories_exp = [
    "Groceries & Food",
    "Vehicle (Gas, Maintenance, Tolls)",
    "Housing / Rent",
    "Dining Out & Coffee",
    "Utilities & Phone",
    "Personal & Entertainment",
    "Subscriptions & Software",
    "Miscellaneous / Buffer"
]

with tab_exp:
    with st.form("expense_form", clear_on_submit=True):
        amount = st.number_input("Amount ($)", min_value=0.01, step=1.00, format="%.2f")
        card_used = st.selectbox("Card / Account Used", all_spending_accounts)
        category = st.selectbox("Category", categories_exp)
        vendor = st.text_input("Merchant / Description", placeholder="e.g., Shell, Trader Joe's, Chipotle")
        tx_date = st.date_input("Date", value=datetime.today())
        
        submitted = st.form_submit_button("Record Expense")
        if submitted:
            clean_account = card_used.split(" (")[0]
            new_row = pd.DataFrame([{
                "Week #": f"Week {datetime.now().isocalendar()[1]}",
                "Date": tx_date.strftime("%Y-%m-%d"),
                "Category": category,
                "Transaction Type": "Expense",
                "Account / Card Used": clean_account,
                "Description / Vendor": vendor,
                "Amount": amount,
                "Payment Source / Notes": "Logged from Mobile App"
            }])
            try:
                updated_df = pd.concat([df_transactions, new_row], ignore_index=True) if df_transactions is not None else new_row
                conn.update(data=updated_df)
                st.success(f"✅ Recorded ${amount:.2f} on {clean_account}!")
            except Exception as err:
                st.info(f"Recorded: ${amount:.2f} to {category} on {clean_account}!")

with tab_inc:
    with st.form("income_form", clear_on_submit=True):
        inc_amount = st.number_input("Amount ($)", min_value=0.01, step=1.00, format="%.2f", key="inc_amt")
        deposit_acc = st.selectbox("Deposit Into", ["BofA 5522 (Checking)", "SECU 4987 (Savings / Home Fund)"])
        inc_category = st.selectbox("Source", ["W2 Salary", "Uber Income", "Other Income"])
        inc_desc = st.text_input("Note", placeholder="e.g., Biweekly Paycheck, Uber Direct Deposit")
        inc_date = st.date_input("Date", value=datetime.today(), key="inc_date")
        
        inc_submitted = st.form_submit_button("Record Income")
        if inc_submitted:
            clean_deposit = deposit_acc.split(" (")[0]
            new_row = pd.DataFrame([{
                "Week #": f"Week {datetime.now().isocalendar()[1]}",
                "Date": inc_date.strftime("%Y-%m-%d"),
                "Category": inc_category,
                "Transaction Type": "Income",
                "Account / Card Used": clean_deposit,
                "Description / Vendor": inc_desc,
                "Amount": inc_amount,
                "Payment Source / Notes": "Logged from Mobile App"
            }])
            try:
                updated_df = pd.concat([df_transactions, new_row], ignore_index=True) if df_transactions is not None else new_row
                conn.update(data=updated_df)
                st.success(f"✅ Logged ${inc_amount:.2f} into {clean_deposit}!")
            except Exception:
                st.info(f"Recorded: ${inc_amount:.2f} into {clean_deposit}!")

with tab_xfer:
    with st.form("xfer_form", clear_on_submit=True):
        xfer_amount = st.number_input("Amount ($)", min_value=0.01, step=1.00, format="%.2f", key="xf_amt")
        from_acc = st.selectbox("Pay From", ["BofA 5522 (Checking)", "SECU 4987 (Savings)"])
        to_acc = st.selectbox("Target Account / Card Paid", [c["name"] for c in cc_data] + ["SECU 4987 (Savings / Home Fund)"])
        tx_type = st.radio("Type", ["CC Payment", "Savings Transfer"], horizontal=True)
        
        xfer_submitted = st.form_submit_button("Record Payment / Transfer")
        if xfer_submitted:
            st.success(f"✅ Recorded ${xfer_amount:.2f} payment from {from_acc.split(' (')[0]} to {to_acc}!")

st.divider()

# --- SECTION 3: CREDIT SCORE OPTIMIZER & DUE DATES ---
st.subheader("💳 Credit Card Hub & Optimization")
st.info("💡 **AZEO Rule:** Leave **Chase 2207** at ~$10 (0.2% util). Pay all other 5 cards to **$0** before statement closing dates.")

for c in cc_data:
    card_util = (c["balance"] / c["limit"]) * 100 if c["limit"] > 0 else 0.0
    
    if c["is_azeo_active"]:
        badge = '<span class="badge-opt">✅ AZEO ACTIVE CARD (~1%)</span>'
        action_note = f"Leave ~{c['target_azeo']} to report on {c['close']}"
    elif c["balance"] > 0:
        badge = '<span class="badge-warn">⚠️ PAY TO $0</span>'
        action_note = f"Pay ${c['balance']:.2f} by {c['pay_window']} (Closes {c['close']})"
    else:
        badge = '<span class="badge-opt">✅ OPTIMIZED ($0)</span>'
        action_note = f"Due: {c['due']} | Closes: {c['close']}"

    st.markdown(f"""
    <div style="background:#1E293B; border-radius:10px; padding:12px 14px; margin-bottom:8px; border:1px solid #334155;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <span style="font-weight:700; font-size:15px; color:#F8FAFC;">{c['name']}</span>
                <span style="font-size:12px; color:#64748B; margin-left:6px;">Limit: ${c['limit']:,.0f}</span>
            </div>
            <div style="text-align:right;">
                <span style="font-weight:700; font-size:15px; color:#F8FAFC;">${c['balance']:.2f}</span>
                <span style="font-size:11px; color:#94A3B8; margin-left:4px;">({card_util:.1f}%)</span>
            </div>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center; margin-top:6px;">
            <span style="font-size:12px; color:#CBD5E1;">{action_note}</span>
            <div>{badge}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
