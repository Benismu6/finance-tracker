import streamlit as st
import pandas as pd
from datetime import datetime

# Configure mobile viewport
st.set_page_config(page_title="Finances & Home Fund", page_icon="🏠", layout="centered")

# --- CUSTOM MOBILE STYLING ---
st.markdown("""
    <style>
    .metric-card {
        background-color: #1E293B;
        border-radius: 12px;
        padding: 16px;
        color: white;
        margin-bottom: 12px;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 48px;
        font-weight: 600;
        background-color: #2563EB;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# --- 1. HOME FUND PROGRESS HEADER ---
TOTAL_GOAL = 26500.00
# In a full deployment, these pull dynamically from your sheet/ledger:
SAVED_TO_DATE = 2791.00  
progress = min(SAVED_TO_DATE / TOTAL_GOAL, 1.0)

st.title("🏠 Baltimore Home Fund")
st.progress(progress)
st.caption(f"**${SAVED_TO_DATE:,.2f}** saved of **${TOTAL_GOAL:,.2f}** goal ({(progress*100):.1f}%)")

st.divider()

# --- 2. FAST TRANSACTION INPUT FORM ---
st.subheader("⚡ Quick Log")
with st.form("transaction_form", clear_on_submit=True):
    t_type = st.radio("Type", ["Expense", "Income", "CC Payment / Transfer"], horizontal=True)
    amount = st.number_input("Amount ($)", min_value=0.01, step=1.00, format="%.2f")
    
    account = st.selectbox("Card / Account", [
        "Debit 1 (Main Checking)",
        "Debit 2 (HYSA Home Fund)",
        "Credit Card 1 (Limit: $5,000)",
        "Credit Card 2 (Limit: $3,000)",
        "Credit Card 3 (Limit: $2,500)",
        "Credit Card 4 (Limit: $4,000)",
        "Credit Card 5 (Limit: $1,500)",
        "Credit Card 6 (Limit: $2,000)",
        "Credit Card 7 (Limit: $3,500)"
    ])
    
    category = st.selectbox("Category", [
        "Groceries & Food",
        "Vehicle (Gas, Maintenance, Tolls)",
        "Housing / Rent",
        "Dining Out & Coffee",
        "Utilities & Phone",
        "Personal & Buffer",
        "W2 Salary Income",
        "Uber Income",
        "Home Fund Savings Transfer"
    ])
    
    description = st.text_input("Merchant / Note", placeholder="e.g., Shell, Trader Joe's, Paycheck")
    date = st.date_input("Date", value=datetime.today())
    
    submitted = st.form_submit_button("Record Transaction")
    if submitted:
        # Code here appends the row to Google Sheets or your transactions CSV
        st.success(f"✅ Recorded: ${amount:.2f} to {category} on {account}!")

st.divider()

# --- 3. AZEO CREDIT SCORE OPTIMIZER SNAPSHOT ---
st.subheader("💳 Credit Card Command")
st.info("💡 **AZEO Rule:** Pay 2–3 days before statement close. Keep CC 1 at ~$15 and all others at $0.")

cards_data = [
    {"Card": "CC 1", "Balance": "$14.50", "Close": "18th", "Due": "15th", "Status": "✅ Optimized (1%)"},
    {"Card": "CC 2", "Balance": "$0.00", "Close": "22nd", "Due": "19th", "Status": "✅ Zero"},
    {"Card": "CC 3", "Balance": "$420.00", "Close": "5th", "Due": "2nd", "Status": "⚠️ Pay before Sep 2"},
]
st.dataframe(pd.DataFrame(cards_data), hide_index=True, use_container_width=True)
