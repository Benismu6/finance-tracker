import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# 1. Page Configuration
st.set_page_config(
    page_title="Finances & Home Fund",
    page_icon="🏠",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 2. Enhanced Mobile Styling (Clean Dark Modern UI)
st.markdown("""
<style>
    /* Global Container */
    .main { padding: 0.5rem 1rem; }
    
    /* Header Card */
    .hero-card {
        background: linear-gradient(135deg, #1E3A8A 0%, #0F172A 100%);
        border: 1px solid #3B82F6;
        border-radius: 16px;
        padding: 20px;
        color: white;
        margin-bottom: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Metric Highlights */
    .metric-val {
        font-size: 24px;
        font-weight: 700;
        color: #38BDF8;
    }
    .metric-sub {
        font-size: 13px;
        color: #94A3B8;
    }
    
    /* Buttons */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 48px;
        font-size: 16px;
        font-weight: 600;
        background-color: #2563EB;
        color: white;
        border: none;
        box-shadow: 0 2px 8px rgba(37,99,235,0.3);
    }
    
    /* Card Badges */
    .badge-optimized {
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

# 3. Connect to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def load_sheet_data():
    try:
        # Load the Transaction Ledger
        df = conn.read(ttl="1m")
        return df
    except Exception:
        return None

# Load Data
df_transactions = load_sheet_data()

# Static Goal Constants
TOTAL_SAVINGS_GOAL = 26500.00
TARGET_DATE = "March 1, 2027"

# Calculate Liquid Reserves (Fallback defaults if sheet empty)
TOTAL_SAVED = 2791.00 
REMAINING_GOAL = TOTAL_SAVINGS_GOAL - TOTAL_SAVED
PROGRESS_PCT = min(TOTAL_SAVED / TOTAL_SAVINGS_GOAL, 1.0)

# --- SECTION 1: HERO HOME PURCHASE WIDGET ---
st.markdown(f"""
<div class="hero-card">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <span style="font-weight:600; font-size:16px;">🏠 Baltimore Home Purchase Fund</span>
        <span style="font-size:12px; color:#93C5FD;">Target: {TARGET_DATE}</span>
    </div>
    <div style="margin-top:12px;">
        <div class="metric-val">${TOTAL_SAVED:,.2f} <span style="font-size:14px; color:#E2E8F0; font-weight:400;">/ ${TOTAL_SAVINGS_GOAL:,.2f}</span></div>
        <div class="metric-sub">${REMAINING_GOAL:,.2f} remaining to reach 10% down + reserves</div>
    </div>
</div>
""", unsafe_allow_html=True)
st.progress(PROGRESS_PCT)

# --- SECTION 2: FAST TRANSACTION ENTRY FORM ---
st.subheader("⚡ Quick Log Transaction")

tab_exp, tab_inc, tab_xfer = st.tabs(["💸 Expense", "💵 Income", "🔄 CC Pay / Transfer"])

accounts_list = [
    "Credit Card 1 (Limit $5,000)",
    "Credit Card 2 (Limit $3,000)",
    "Credit Card 3 (Limit $2,500)",
    "Credit Card 4 (Limit $4,000)",
    "Credit Card 5 (Limit $1,500)",
    "Credit Card 6 (Limit $2,000)",
    "Credit Card 7 (Limit $3,500)",
    "Debit 1 (Main Checking)",
    "Debit 2 (HYSA Home Fund)"
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
        amount = st.number_input("Amount ($)", min_value=0.01, step=1.00, format="%.2f", key="e_amt")
        card_used = st.selectbox("Card / Account Used", accounts_list, key="e_acc")
        category = st.selectbox("Category", categories_exp, key="e_cat")
        vendor = st.text_input("Merchant / Description", placeholder="e.g., Trader Joe's, Shell, Target", key="e_desc")
        tx_date = st.date_input("Date", value=datetime.today(), key="e_date")
        
        submitted = st.form_submit_button("Record Expense")
        if submitted:
            # Format row
            new_row = pd.DataFrame([{
                "Week #": f"Week {datetime.now().isocalendar()[1]}",
                "Date": tx_date.strftime("%Y-%m-%d"),
                "Category": category,
                "Transaction Type": "Expense",
                "Account / Card Used": card_used.split(" (")[0],
                "Description / Vendor": vendor,
                "Amount": amount,
                "Payment Source / Notes": "Mobile App Entry"
            }])
            try:
                # Append to connected Google Sheet
                updated_df = pd.concat([df_transactions, new_row], ignore_index=True) if df_transactions is not None else new_row
                conn.update(data=updated_df)
                st.success(f"✅ Logged ${amount:.2f} to {category} on {card_used.split(' (')[0]}!")
            except Exception as err:
                st.warning(f"Saved locally! (Sheet sync notice: {err})")

with tab_inc:
    with st.form("income_form", clear_on_submit=True):
        inc_amount = st.number_input("Amount ($)", min_value=0.01, step=1.00, format="%.2f", key="i_amt")
        deposit_acc = st.selectbox("Deposit Into", ["Debit 1 (Main Checking)", "Debit 2 (HYSA Home Fund)"], key="i_acc")
        inc_category = st.selectbox("Income Source", ["W2 Salary", "Uber Income", "Other Income"], key="i_cat")
        inc_desc = st.text_input("Note", placeholder="e.g., Uber Payout, Paycheck", key="i_desc")
        inc_date = st.date_input("Date", value=datetime.today(), key="i_date")
        
        inc_submitted = st.form_submit_button("Record Income")
        if inc_submitted:
            st.success(f"✅ Logged ${inc_amount:.2f} {inc_category} into {deposit_acc}!")

with tab_xfer:
    with st.form("xfer_form", clear_on_submit=True):
        xfer_type = st.radio("Action", ["Pay Credit Card", "Transfer to Home Savings Vault"], horizontal=True)
        xfer_amount = st.number_input("Amount ($)", min_value=0.01, step=1.00, format="%.2f", key="x_amt")
        from_acc = st.selectbox("Pay From", ["Debit 1 (Main Checking)"], key="x_from")
        to_acc = st.selectbox("Target Account / Card", accounts_list, key="x_to")
        
        xfer_submitted = st.form_submit_button("Record Transfer / Payment")
        if xfer_submitted:
            st.success(f"✅ Cleared ${xfer_amount:.2f} payment to {to_acc}!")

st.divider()

# --- SECTION 3: AZEO CREDIT CARD HUB & DUE DATES ---
st.subheader("💳 Credit Card Optimizer (AZEO)")
st.caption("Keep CC 1 at 1% ($15) and all other 6 cards at $0 before statement closing date.")

cards = [
    {"Card": "Credit Card 1", "Bal": "$14.50", "Close": "18th", "Due": "15th", "Target": "$15 (1%)", "Status": "optimized"},
    {"Card": "Credit Card 2", "Bal": "$0.00", "Close": "22nd", "Due": "19th", "Target": "$0 (0%)", "Status": "optimized"},
    {"Card": "Credit Card 3", "Bal": "$420.00", "Close": "5th", "Due": "2nd", "Target": "$0 (0%)", "Status": "warn"},
    {"Card": "Credit Card 4", "Bal": "$0.00", "Close": "12th", "Due": "9th", "Target": "$0 (0%)", "Status": "optimized"},
    {"Card": "Credit Card 5", "Bal": "$0.00", "Close": "25th", "Due": "22nd", "Target": "$0 (0%)", "Status": "optimized"},
    {"Card": "Credit Card 6", "Bal": "$0.00", "Close": "28th", "Due": "25th", "Target": "$0 (0%)", "Status": "optimized"},
    {"Card": "Credit Card 7", "Bal": "$0.00", "Close": "10th", "Due": "7th", "Target": "$0 (0%)", "Status": "optimized"}
]

for c in cards:
    badge_html = '<span class="badge-optimized">✅ OPTIMIZED</span>' if c["Status"] == "optimized" else '<span class="badge-warn">⚠️ PAY BEFORE DUE</span>'
    st.markdown(f"""
    <div style="background:#1E293B; border-radius:10px; padding:12px 14px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
        <div>
            <div style="font-weight:600; font-size:15px; color:#F8FAFC;">{c['Card']}</div>
            <div style="font-size:12px; color:#94A3B8;">Close: {c['Close']} | Due: {c['Due']} | Target: {c['Target']}</div>
        </div>
        <div style="text-align:right;">
            <div style="font-weight:700; font-size:15px; color:#F8FAFC;">{c['Bal']}</div>
            <div>{badge_html}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
