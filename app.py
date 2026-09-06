import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import calendar
import traceback
import re
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection
import gspread
from google.oauth2.service_account import Credentials
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

    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 2rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
        max-width: 750px !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }
    
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
        text-decoration: none !important;
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

    .hero-card {
        background: linear-gradient(135deg, #1E3A8A 0%, #0F172A 100%);
        border: 1px solid #3B82F6;
        border-radius: 14px;
        padding: 16px;
        color: white;
        margin-bottom: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.25);
    }
    .metric-val { 
        font-size: 30px; 
        font-weight: 800; 
        color: #38BDF8; 
        text-align: right;
        letter-spacing: -0.5px;
    }
    .metric-sub { font-size: 12px; color: #94A3B8; text-align: right; }
    
    .stat-box {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 10px;
        text-align: right;
    }
    
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 38px;
        font-size: 13px;
        font-weight: 700;
        background-color: #2563EB;
        color: white;
        border: none;
        box-shadow: 0 2px 6px rgba(37,99,235,0.4);
    }

    /* 20% SMALLER ADD ACCOUNT BUTTON WITH TIGHTER VERTICAL ALIGNMENT */
    div.small-add-btn {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        width: 100%;
    }
    div.small-add-btn button {
        height: 20px !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        padding: 3px 10px !important;
        border-radius: 8px !important;
        margin: 0 !important;
        white-space: nowrap !important;
    }

    /* EXACT ORIGINAL CARD CONTAINER */
    details.card-container {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 12px;
        margin-bottom: 10px;
        overflow: hidden;
        transition: border-color 0.2s ease;
    }
    details.card-container[open] {
        border-color: #3B82F6;
    }
    details.card-container > summary {
        list-style: none;
        outline: none;
        cursor: pointer;
        padding: 14px 16px;
        background-color: #1E293B;
        user-select: none;
    }
    details.card-container > summary::-webkit-details-marker {
        display: none;
    }
    details.card-container > summary:hover {
        background-color: #243248;
    }
    .card-drawer {
        background-color: #0F172A;
        padding: 12px 14px;
        border-top: 1px solid #334155;
    }

    /* ACTION BUTTONS INSIDE CARDS (UNUNDERLINED) */
    button.drawer-btn {
        display: inline-block;
        padding: 6px 12px;
        font-size: 11px;
        font-weight: 700;
        border-radius: 6px;
        text-decoration: none !important;
        text-align: center;
        cursor: pointer;
        user-select: none;
        border: 1px solid transparent;
        line-height: 1.4;
        outline: none !important;
        margin-right: 6px;
        margin-bottom: 6px;
    }
    button.drawer-btn:focus, button.drawer-btn:active, button.drawer-btn:hover {
        text-decoration: none !important;
        outline: none !important;
    }
    .drawer-btn-blue {
        background-color: #2563EB;
        color: #FFFFFF !important;
        border-color: #3B82F6;
    }
    .drawer-btn-blue:hover {
        background-color: #1D4ED8;
    }
    .drawer-btn-purple {
        background-color: #7C3AED;
        color: #FFFFFF !important;
        border-color: #8B5CF6;
    }
    .drawer-btn-purple:hover {
        background-color: #6D28D9;
    }
    .drawer-btn-emerald {
        background-color: #059669;
        color: #FFFFFF !important;
        border-color: #10B981;
    }
    .drawer-btn-emerald:hover {
        background-color: #047857;
    }
    .drawer-btn-slate {
        background-color: #334155;
        color: #F1F5F9 !important;
        border-color: #475569;
    }
    .drawer-btn-slate:hover {
        background-color: #475569;
    }

    /* ZERO-PIXEL INVISIBLE TRIGGER CONTAINER */
    div.st-key-hidden_triggers {
        position: fixed !important;
        top: 0px !important;
        left: 0px !important;
        width: 0px !important;
        height: 0px !important;
        opacity: 0 !important;
        overflow: hidden !important;
        z-index: -9999 !important;
        pointer-events: auto !important;
    }
    div.st-key-hidden_triggers button {
        width: 0px !important;
        height: 0px !important;
        min-height: 0px !important;
        padding: 0 !important;
        margin: 0 !important;
        border: none !important;
        opacity: 0 !important;
        pointer-events: auto !important;
    }

    .badge-opt { background-color: #065F46; color: #6EE7B7; padding: 4px 9px; border-radius: 6px; font-size: 11px; font-weight: 700; white-space: nowrap; }
    .badge-warn { background-color: #7C2D12; color: #FDBA74; padding: 4px 9px; border-radius: 6px; font-size: 11px; font-weight: 700; white-space: nowrap; }
    .badge-biz { background-color: #312E81; color: #C7D2FE; padding: 4px 9px; border-radius: 6px; font-size: 11px; font-weight: 700; white-space: nowrap; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATE & CYCLE CALCULATION ENGINE
# ==========================================
today_dt = date.today()

def get_next_recurring_date(target_day: int, ref_date: date) -> date:
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

def get_prev_recurring_date(target_day: int, ref_date: date) -> date:
    y, m = ref_date.year, ref_date.month
    if target_day == -1:
        prev_m = m - 1 if m > 1 else 12
        prev_y = y if m > 1 else y - 1
        return date(prev_y, prev_m, calendar.monthrange(prev_y, prev_m)[1])
    
    max_d = calendar.monthrange(y, m)[1]
    cand = date(y, m, min(target_day, max_d))
    if cand <= ref_date:
        return cand
    else:
        prev_m = m - 1 if m > 1 else 12
        prev_y = y if m > 1 else y - 1
        max_d_prev = calendar.monthrange(prev_y, prev_m)[1]
        return date(prev_y, prev_m, min(target_day, max_d_prev))

# ==========================================
# 3. GSHEETS BACKEND (LEDGER & ACCOUNTS REGISTRY)
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

def get_authorized_gspread():
    gs_secrets = dict(st.secrets["connections"]["gsheets"])
    sa_keys = [
        "type", "project_id", "private_key_id", "private_key",
        "client_email", "client_id", "auth_uri", "token_uri",
        "auth_provider_x509_cert_url", "client_x509_cert_url"
    ]
    service_account_info = {k: gs_secrets[k] for k in sa_keys if k in gs_secrets}
    if "private_key" in service_account_info:
        service_account_info["private_key"] = service_account_info["private_key"].replace("\\n", "\n")

    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_info(service_account_info, scopes=scopes)
    gc = gspread.authorize(credentials)
    return gc, gs_secrets["spreadsheet"]

def append_tx_to_sheet(row_values):
    gc, sheet_url = get_authorized_gspread()
    spreadsheet = gc.open_by_url(sheet_url)
    worksheet = spreadsheet.worksheet("Master_Transactions")
    worksheet.append_row(row_values, value_input_option="USER_ENTERED")

def append_multiple_tx_to_sheet(rows_list):
    gc, sheet_url = get_authorized_gspread()
    spreadsheet = gc.open_by_url(sheet_url)
    worksheet = spreadsheet.worksheet("Master_Transactions")
    worksheet.append_rows(rows_list, value_input_option="USER_ENTERED")

def append_account_to_sheet(row_values):
    gc, sheet_url = get_authorized_gspread()
    spreadsheet = gc.open_by_url(sheet_url)
    try:
        worksheet = spreadsheet.worksheet("Accounts_Master")
    except Exception:
        worksheet = spreadsheet.add_worksheet(title="Accounts_Master", rows=50, cols=10)
        worksheet.append_row(["Account_Name", "Account_Type", "Role_Or_Memo", "Base_Balance", "Credit_Limit", "Due_Day", "Close_Day"])
    worksheet.append_row(row_values, value_input_option="USER_ENTERED")

def get_ledger_data():
    try:
        df = conn.read(worksheet="Master_Transactions", ttl="0")
        if df is not None and not df.empty:
            df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0.0)
            df["Date_DT"] = pd.to_datetime(df["Date"], errors="coerce").dt.date
            if "Account" in df.columns:
                df["Account"] = df["Account"].astype(str).str.strip().str.replace(" C ", " ").str.replace(" S ", " ")
            if "Type" in df.columns:
                df["Type"] = df["Type"].astype(str).str.strip()
            return df
    except Exception:
        pass
    return pd.DataFrame(columns=[
        "Transaction_ID", "Date", "Account", "Type", "Category", 
        "Merchant", "Amount", "Goal_Tag", "Item_Description", "Notes"
    ])

def get_accounts_registry():
    try:
        df_acc = conn.read(worksheet="Accounts_Master", ttl="0")
        if df_acc is not None and not df_acc.empty:
            if "Account_Name" in df_acc.columns:
                df_acc["Account_Name"] = df_acc["Account_Name"].astype(str).str.strip().str.replace(" C ", " ").str.replace(" S ", " ")
            df_acc["Base_Balance"] = pd.to_numeric(df_acc["Base_Balance"], errors="coerce").fillna(0.0)
            df_acc["Credit_Limit"] = pd.to_numeric(df_acc["Credit_Limit"], errors="coerce").fillna(0.0)
            df_acc["Due_Day"] = pd.to_numeric(df_acc["Due_Day"], errors="coerce").fillna(1).astype(int)
            df_acc["Close_Day"] = pd.to_numeric(df_acc["Close_Day"], errors="coerce").fillna(4).astype(int)
            return df_acc
    except Exception:
        pass
    return pd.DataFrame([
        {"Account_Name": "BofA 5522", "Account_Type": "Cash / Bank", "Role_Or_Memo": "Primary Operating Checking", "Base_Balance": 251.67, "Credit_Limit": 0, "Due_Day": 0, "Close_Day": 0},
        {"Account_Name": "BofA 3881", "Account_Type": "Cash / Bank", "Role_Or_Memo": "BofA Secondary Savings", "Base_Balance": 0.00, "Credit_Limit": 0, "Due_Day": 0, "Close_Day": 0},
        {"Account_Name": "SECU 4987", "Account_Type": "Cash / Bank", "Role_Or_Memo": "SECU Primary Checking", "Base_Balance": 4212.10, "Credit_Limit": 0, "Due_Day": 0, "Close_Day": 0},
        {"Account_Name": "SECU 4979", "Account_Type": "Cash / Bank", "Role_Or_Memo": "Dedicated Home Savings / HYSA", "Base_Balance": 0.00, "Credit_Limit": 0, "Due_Day": 0, "Close_Day": 0},
        {"Account_Name": "SoFi 3854", "Account_Type": "Cash / Bank", "Role_Or_Memo": "SoFi Primary Checking", "Base_Balance": 0.00, "Credit_Limit": 0, "Due_Day": 0, "Close_Day": 0},
        {"Account_Name": "SoFi 4777", "Account_Type": "Cash / Bank", "Role_Or_Memo": "SoFi High-Yield Savings", "Base_Balance": 0.00, "Credit_Limit": 0, "Due_Day": 0, "Close_Day": 0},
        {"Account_Name": "Loan to Parents", "Account_Type": "Cash / Bank", "Role_Or_Memo": "Appliance Loan", "Base_Balance": 0.00, "Credit_Limit": 0, "Due_Day": 0, "Close_Day": 0},
        {"Account_Name": "Chase 1993", "Account_Type": "Personal CC", "Role_Or_Memo": "Primary Daily", "Base_Balance": 517.70, "Credit_Limit": 10600.00, "Due_Day": 1, "Close_Day": 4},
        {"Account_Name": "Chase 2207", "Account_Type": "Personal CC", "Role_Or_Memo": "AZEO 1%", "Base_Balance": 9.52, "Credit_Limit": 4900.00, "Due_Day": 1, "Close_Day": 4},
        {"Account_Name": "BofA 5309", "Account_Type": "Personal CC", "Role_Or_Memo": "Buffer Card", "Base_Balance": 22.21, "Credit_Limit": 7500.00, "Due_Day": 24, "Close_Day": 27},
        {"Account_Name": "BofA 7197", "Account_Type": "Personal CC", "Role_Or_Memo": "Buffer Card", "Base_Balance": 37.12, "Credit_Limit": 3500.00, "Due_Day": 24, "Close_Day": 27},
        {"Account_Name": "Apple 1765", "Account_Type": "Personal CC", "Role_Or_Memo": "Digital Wallet", "Base_Balance": 0.00, "Credit_Limit": 2000.00, "Due_Day": -1, "Close_Day": 3},
        {"Account_Name": "TJX", "Account_Type": "Personal CC", "Role_Or_Memo": "Retail Card", "Base_Balance": 0.00, "Credit_Limit": 3200.00, "Due_Day": 5, "Close_Day": 8},
        {"Account_Name": "Chase 0431", "Account_Type": "Business CC", "Role_Or_Memo": "Business CC", "Base_Balance": 505.07, "Credit_Limit": 0.00, "Due_Day": 1, "Close_Day": 7}
    ])

df_tx = get_ledger_data()
df_registry = get_accounts_registry()

# 1. DYNAMIC CASH BALANCES (WITH TRANSFERS INCLUDED)
live_cash_registry = []
cash_df = df_registry[df_registry["Account_Type"] == "Cash / Bank"]

for _, acc in cash_df.iterrows():
    a_name = acc["Account_Name"]
    base_val = float(acc["Base_Balance"])
    inc_val = df_tx[(df_tx["Account"] == a_name) & (df_tx["Type"] == "Income")]["Amount"].sum()
    exp_val = df_tx[(df_tx["Account"] == a_name) & (df_tx["Type"] == "Expense")]["Amount"].sum()
    cc_paid_out = df_tx[(df_tx["Type"] == "CC Payment") & (df_tx["Merchant"].str.contains(a_name, na=False))]["Amount"].sum()
    
    transfers_in = df_tx[(df_tx["Account"] == a_name) & (df_tx["Type"] == "Transfer") & (df_tx["Notes"].str.contains("Inflow", na=False))]["Amount"].sum()
    transfers_out = df_tx[(df_tx["Account"] == a_name) & (df_tx["Type"] == "Transfer") & (df_tx["Notes"].str.contains("Outflow", na=False))]["Amount"].sum()
    
    current_cash = base_val + inc_val - exp_val - cc_paid_out + transfers_in - transfers_out
    live_cash_registry.append({
        "name": a_name,
        "role": acc["Role_Or_Memo"],
        "base": base_val,
        "current_balance": max(current_cash, 0.0)
    })

total_cash = sum(c["current_balance"] for c in live_cash_registry)

# 2. DYNAMIC PERSONAL CC BALANCES
raw_personal_cards = []
p_cc_df = df_registry[df_registry["Account_Type"] == "Personal CC"]

for _, card in p_cc_df.iterrows():
    c_name = card["Account_Name"]
    base_bal = float(card["Base_Balance"])
    limit_bal = float(card["Credit_Limit"])
    due_d = int(card["Due_Day"])
    close_d = int(card["Close_Day"])
    
    last_close = get_prev_recurring_date(close_d, today_dt)
    next_due = get_next_recurring_date(due_d, today_dt)
    next_close = get_next_recurring_date(close_d, today_dt)
    
    spent_all = df_tx[(df_tx["Account"] == c_name) & (df_tx["Type"] == "Expense")]["Amount"].sum()
    paid_all = df_tx[(df_tx["Account"] == c_name) & (df_tx["Type"] == "CC Payment")]["Amount"].sum()
    current_live_bal = max(base_bal + spent_all - paid_all, 0.0)
    
    charges_prior = df_tx[(df_tx["Account"] == c_name) & (df_tx["Type"] == "Expense") & (df_tx["Date_DT"] <= last_close)]["Amount"].sum()
    stmt_balance_billed = max(base_bal + charges_prior - paid_all, 0.0)
    
    raw_personal_cards.append({
        "name": c_name,
        "base": base_bal,
        "limit": limit_bal,
        "due_day": due_d,
        "close_day": close_d,
        "current_balance": current_live_bal,
        "stmt_due": stmt_balance_billed,
        "next_due": next_due,
        "next_close": next_close
    })

non_zero_candidates = [c for c in raw_personal_cards if c["current_balance"] > 0]
if non_zero_candidates:
    azeo_card_name = min(non_zero_candidates, key=lambda x: abs(x["current_balance"] - 10.0))["name"]
else:
    azeo_card_name = "Chase 2207"

live_personal_cc = []
for c in raw_personal_cards:
    c_name = c["name"]
    bal = c["current_balance"]
    stmt_due = c["stmt_due"]
    next_due = c["next_due"]
    next_close = c["next_close"]
    
    is_azeo = (c_name == azeo_card_name)
    if stmt_due > 0.01:
        badge_html = '<span style="background-color:#7C2D12;color:#FDBA74;padding:4px 9px;border-radius:6px;font-size:11px;font-weight:700;white-space:nowrap;">⚠️ STMT DUE</span>'
        action_text = f"Pay ${stmt_due:.2f} stmt balance by {next_due.strftime('%b %d')}"
    elif is_azeo:
        badge_html = '<span style="background-color:#065F46;color:#6EE7B7;padding:4px 9px;border-radius:6px;font-size:11px;font-weight:700;white-space:nowrap;">✅ AZEO ACTIVE (~1%)</span>'
        action_text = f"Leave ${bal:.2f} to report on {next_close.strftime('%b %d')}"
    elif bal > 0.01:
        badge_html = '<span style="background-color:#7C2D12;color:#FDBA74;padding:4px 9px;border-radius:6px;font-size:11px;font-weight:700;white-space:nowrap;">⚠️ PAY BEFORE CLOSE</span>'
        action_text = f"Pay ${bal:.2f} by {next_close.strftime('%b %d')} to report $0"
    else:
        badge_html = '<span style="background-color:#065F46;color:#6EE7B7;padding:4px 9px;border-radius:6px;font-size:11px;font-weight:700;white-space:nowrap;">✅ $0 REPORTING</span>'
        action_text = f"Reports $0 on {next_close.strftime('%b %d')}"
        
    card_dict = dict(c)
    card_dict["is_azeo_active"] = is_azeo
    card_dict["utilization"] = (bal / c["limit"]) * 100 if c["limit"] > 0 else 0.0
    card_dict["due_str"] = next_due.strftime("%b %d")
    card_dict["close_str"] = next_close.strftime("%b %d")
    card_dict["action_text"] = action_text
    card_dict["badge_html"] = badge_html
    live_personal_cc.append(card_dict)

# 3. DYNAMIC BUSINESS CC BALANCES
live_biz_cc = []
b_cc_df = df_registry[df_registry["Account_Type"] == "Business CC"]

for _, card in b_cc_df.iterrows():
    c_name = card["Account_Name"]
    base_bal = float(card["Base_Balance"])
    due_d = int(card["Due_Day"])
    close_d = int(card["Close_Day"])
    
    spent = df_tx[(df_tx["Account"] == c_name) & (df_tx["Type"] == "Expense")]["Amount"].sum()
    paid = df_tx[(df_tx["Account"] == c_name) & (df_tx["Type"] == "CC Payment")]["Amount"].sum()
    current_bal = max(base_bal + spent - paid, 0.0)
    
    next_due = get_next_recurring_date(due_d, today_dt)
    next_close = get_next_recurring_date(close_d, today_dt)
    pay_by_date = next_due - timedelta(days=1)
    
    live_biz_cc.append({
        "name": c_name,
        "current_balance": current_bal,
        "due_str": next_due.strftime("%b %d"),
        "close_str": next_close.strftime("%b %d"),
        "pay_by_str": f"By {pay_by_date.strftime('%b %d')}"
    })

personal_cc_debt = sum(c["current_balance"] for c in live_personal_cc)
personal_cc_limit = sum(c["limit"] for c in live_personal_cc)
personal_utilization = (personal_cc_debt / personal_cc_limit) * 100 if personal_cc_limit > 0 else 0.0

biz_cc_debt = sum(c["current_balance"] for c in live_biz_cc)
total_all_debt = personal_cc_debt + biz_cc_debt
net_liquid_cash = total_cash - total_all_debt

HOME_GOAL = 26500.00
goal_progress = min(total_cash / HOME_GOAL, 1.0)
remaining_goal = max(HOME_GOAL - total_cash, 0.0)

# Categories Master List & Lean $300/wk Targets
categories_list = [
    "Vehicle & Gas", "Housing & Rent", "Groceries & Food", 
    "Personal & Entertainment", "Dining Out & Coffee", 
    "Business Operations", "Subscriptions & Software", "Miscellaneous / Buffer"
]

WEEKLY_BUDGET_TARGETS = {
    "Vehicle & Gas": 100.00,
    "Housing & Rent": 50.00,
    "Groceries & Food": 50.00,
    "Personal & Entertainment": 50.00,
    "Dining Out & Coffee": 30.00,
    "Business Operations": 10.00,
    "Subscriptions & Software": 10.00
}
WEEKLY_BUDGET_TOTAL = 300.00

CATEGORY_COLORS = {
    "Vehicle & Gas": "#3B82F6",
    "Housing & Rent": "#8B5CF6",
    "Groceries & Food": "#10B981",
    "Personal & Entertainment": "#F59E0B",
    "Dining Out & Coffee": "#EC4899",
    "Business Operations": "#06B6D4",
    "Subscriptions & Software": "#6366F1",
    "Miscellaneous / Buffer": "#64748B"
}

# ==========================================
# 4. CARD HTML RENDERING HELPERS
# ==========================================
def get_tx_rows_html(acc_name):
    if not df_tx.empty and "Account" in df_tx.columns:
        sub_tx = df_tx[
            (df_tx["Account"] == acc_name) | 
            ((df_tx["Type"] == "CC Payment") & (df_tx["Merchant"].str.contains(acc_name, na=False)))
        ].tail(5)
        
        if not sub_tx.empty:
            html = "<div style='font-size:12px; font-weight:700; color:#94A3B8; margin-top:8px; margin-bottom:6px;'>Last 5 Transactions:</div>"
            for _, r in sub_tx.iloc[::-1].iterrows():
                t_type = r.get("Type", "Expense")
                amt = float(r.get("Amount", 0.0))
                desc = r.get("Item_Description", "")
                vendor = r.get("Merchant", "")
                date_val = str(r.get("Date", ""))
                label = f"{vendor} — {desc}" if desc and str(desc).strip() != "" and str(desc).lower() != "nan" else vendor
                
                if t_type == "Income" or "Inflow" in str(r.get("Notes", "")):
                    amt_color = "#34D399"
                    prefix = "+"
                elif t_type == "CC Payment":
                    amt_color = "#60A5FA"
                    prefix = "-"
                elif t_type == "Transfer":
                    amt_color = "#C084FC"
                    prefix = "+" if "Inflow" in str(r.get("Notes", "")) else "-"
                else:
                    amt_color = "#F87171"
                    prefix = "-"
                
                html += f"""<div style="display:flex; justify-content:space-between; align-items:center; background:#162032; border-radius:6px; padding:6px 10px; margin-bottom:4px; font-size:12px; border:1px solid #334155;"><div><span style="color:#CBD5E1; font-weight:600;">{label}</span><div style="font-size:10px; color:#64748B;">{date_val} • {t_type}</div></div><div style="font-weight:800; color:{amt_color}; font-size:13px; text-align:right;">{prefix}${amt:,.2f}</div></div>"""
            return html
        else:
            return "<div style='font-size:12px; color:#64748B; padding:4px 0;'>ℹ️ No transactions recorded for this account yet.</div>"
    return "<div style='font-size:12px; color:#64748B; padding:4px 0;'>ℹ️ No ledger records available.</div>"

def render_account_card(title, subtitle, right_val, right_sub, extra_left="", extra_right="", tx_html="", action_buttons_html=""):
    bottom_bar = f"""<div style="display:flex; justify-content:space-between; align-items:center; margin-top:8px;"><span style="font-size:12px; color:#CBD5E1;">{extra_left}</span><div>{extra_right}</div></div>""" if (extra_left or extra_right) else ""
    val_color = '#38BDF8' if '$' in right_val and '.' in right_val else '#F8FAFC'
    
    card_html = f"""<details class="card-container"><summary><div style="display:flex; justify-content:space-between; align-items:center;"><div><span style="font-weight:700; font-size:15px; color:#F8FAFC;">{title}</span><div style="font-size:12px; color:#94A3B8;">{subtitle}</div></div><div style="text-align:right;"><span style="font-weight:800; font-size:18px; color:{val_color};">{right_val}</span><div style="font-size:11px; color:#64748B;">{right_sub}</div></div></div>{bottom_bar}</summary><div class="card-drawer">{action_buttons_html}{tx_html}</div></details>"""
    st.markdown(card_html, unsafe_allow_html=True)

# ==========================================
# 5. DYNAMIC TRANSACTION MODALS
# ==========================================
all_account_names = list(df_registry["Account_Name"])
deposit_accounts = list(df_registry[df_registry["Account_Type"] == "Cash / Bank"]["Account_Name"])

@st.dialog("Record Income / Deposit")
def modal_bank_income(acc_name):
    st.markdown(f"**Target Account:** `{acc_name}`")
    with st.form(f"form_m_inc_{acc_name}", clear_on_submit=True):
        inc_amt = st.number_input("Amount ($)", min_value=0.01, step=1.00, format="%.2f")
        inc_cat = st.selectbox("Source", ["W2 Salary", "Uber Income", "Other Income"])
        payer = st.text_input("Payer / Store", placeholder="e.g. Employer Payroll, Uber Payout, Client")
        memo = st.text_input("Memo (Optional)", placeholder="e.g. Paycheck deposit")
        tx_date = st.date_input("Date", value=datetime.today())
        gt = "Baltimore 1st Home" if ("4979" in acc_name or "SECU" in acc_name) else "General Living"
        
        if st.form_submit_button("Record Deposit"):
            row = [
                f"TX-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                tx_date.strftime("%Y-%m-%d"),
                acc_name,
                "Income",
                inc_cat,
                payer,
                float(inc_amt),
                gt,
                memo,
                "Card Quick Entry"
            ]
            try:
                append_tx_to_sheet(row)
                st.success(f"✅ Deposited ${inc_amt:.2f} into {acc_name}!")
                st.rerun()
            except Exception as err:
                st.error(f"Error: {err}")

@st.dialog("Execute Account Transfer")
def modal_bank_transfer(from_acc):
    st.markdown(f"**From Account:** `{from_acc}`")
    other_accounts = [a for a in deposit_accounts if a != from_acc]
    with st.form(f"form_m_trans_{from_acc}", clear_on_submit=True):
        trans_amt = st.number_input("Transfer Amount ($)", min_value=0.01, step=10.00, format="%.2f")
        to_acc = st.selectbox("Transfer Into", other_accounts if other_accounts else deposit_accounts)
        memo = st.text_input("Memo (Optional)", placeholder="e.g. Weekly savings sweep")
        tx_date = st.date_input("Date", value=datetime.today())
        
        if st.form_submit_button("Confirm Transfer"):
            if from_acc == to_acc:
                st.error("Source and destination must be different.")
            else:
                now_str = datetime.now().strftime('%Y%m%d%H%M%S')
                d_str = tx_date.strftime("%Y-%m-%d")
                memo_str = f" — {memo.strip()}" if memo.strip() else ""
                gt = "Baltimore 1st Home" if ("4979" in to_acc or "SECU" in to_acc) else "General Living"
                
                debit_row = [
                    f"TX-{now_str}-A", d_str, from_acc, "Transfer", "Transfer / Sweep",
                    f"Transfer to {to_acc}", float(trans_amt), gt, f"Outflow to {to_acc}{memo_str}", "Transfer Outflow"
                ]
                credit_row = [
                    f"TX-{now_str}-B", d_str, to_acc, "Transfer", "Transfer / Sweep",
                    f"Transfer from {from_acc}", float(trans_amt), gt, f"Inflow from {from_acc}{memo_str}", "Transfer Inflow"
                ]
                try:
                    append_multiple_tx_to_sheet([debit_row, credit_row])
                    st.success(f"✅ Transferred ${trans_amt:.2f} to {to_acc}!")
                    st.rerun()
                except Exception as err:
                    st.error(f"Error: {err}")

@st.dialog("Record Debit Expense")
def modal_bank_expense(acc_name):
    st.markdown(f"**Account:** `{acc_name}`")
    with st.form(f"form_m_b_exp_{acc_name}", clear_on_submit=True):
        amt = st.number_input("Amount ($)", min_value=0.01, step=1.00, format="%.2f")
        cat = st.selectbox("Category", categories_list)
        vendor = st.text_input("Merchant / Store", placeholder="e.g. Landlord, Shell, Trader Joe's")
        desc = st.text_input("Memo (Optional)", placeholder="e.g. Direct withdrawal")
        tx_date = st.date_input("Date", value=datetime.today())
        gt = st.selectbox("Goal Tag", ["General Living", "Baltimore 1st Home", "Emergency Vault", "Business"])
        
        if st.form_submit_button("Save Expense"):
            row = [
                f"TX-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                tx_date.strftime("%Y-%m-%d"),
                acc_name,
                "Expense",
                cat,
                vendor,
                float(amt),
                gt,
                desc,
                "Card Quick Entry"
            ]
            try:
                append_tx_to_sheet(row)
                st.success(f"✅ Saved ${amt:.2f} expense from {acc_name}!")
                st.rerun()
            except Exception as err:
                st.error(f"Error: {err}")

@st.dialog("Record Credit Card Charge")
def modal_card_expense(card_name):
    st.markdown(f"**Card:** `{card_name}`")
    with st.form(f"form_m_c_exp_{card_name}", clear_on_submit=True):
        amt = st.number_input("Amount ($)", min_value=0.01, step=1.00, format="%.2f")
        cat = st.selectbox("Category", categories_list)
        vendor = st.text_input("Merchant / Store", placeholder="e.g. Amazon, Shell, Quick Mart")
        desc = st.text_input("Memo (Optional)", placeholder="e.g. Gas, Work lunch")
        tx_date = st.date_input("Date", value=datetime.today())
        gt = st.selectbox("Goal Tag", ["General Living", "Baltimore 1st Home", "Emergency Vault", "Business"])
        
        if st.form_submit_button("Record Charge"):
            row = [
                f"TX-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                tx_date.strftime("%Y-%m-%d"),
                card_name,
                "Expense",
                cat,
                vendor,
                float(amt),
                gt,
                desc,
                "Card Quick Entry"
            ]
            try:
                append_tx_to_sheet(row)
                st.success(f"✅ Saved ${amt:.2f} charge on {card_name}!")
                st.rerun()
            except Exception as err:
                st.error(f"Error: {err}")

@st.dialog("Record Credit Card Payment")
def modal_card_payment(card_name, current_balance):
    st.markdown(f"**Card:** `{card_name}` | **Balance:** `${current_balance:,.2f}`")
    with st.form(f"form_m_c_pay_{card_name}", clear_on_submit=True):
        pay_amt = st.number_input("Payment Amount ($)", min_value=0.01, value=float(current_balance) if current_balance > 0 else 10.00, step=1.00, format="%.2f")
        from_acc = st.selectbox("Paid From", deposit_accounts)
        memo = st.text_input("Memo (Optional)", placeholder="e.g. Statement payoff, AZEO adjustment")
        tx_date = st.date_input("Date", value=datetime.today())
        
        if st.form_submit_button("Submit Payment"):
            row = [
                f"TX-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                tx_date.strftime("%Y-%m-%d"),
                card_name,
                "CC Payment",
                "CC Payment",
                f"Paid from {from_acc}",
                float(pay_amt),
                "General Living",
                memo,
                "Card Quick Entry"
            ]
            try:
                append_tx_to_sheet(row)
                st.success(f"✅ Recorded ${pay_amt:.2f} payment to {card_name}!")
                st.rerun()
            except Exception as err:
                st.error(f"Error: {err}")

@st.dialog("➕ Add New Account to Registry")
def open_new_account_dialog():
    st.caption("Register a new account or credit card. It will automatically update in Google Sheets and sync into your app.")
    with st.form("new_account_form", clear_on_submit=True):
        new_acc_name = st.text_input("Account Identifier (e.g. Capital One 1122)", placeholder="Card or Bank Name")
        new_acc_type = st.selectbox("Account Type", ["Cash / Bank", "Personal CC", "Business CC"])
        new_acc_role = st.text_input("Role / Memo (e.g. Dining Card, HYSA)", placeholder="Brief description")
        new_acc_base = st.number_input("Starting Base Balance ($)", min_value=0.00, step=10.00, format="%.2f")
        
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            new_limit = st.number_input("Credit Limit ($)", min_value=0.00, step=100.00, format="%.2f")
        with col_c2:
            new_due = st.number_input("Due Day of Month", min_value=-1, max_value=31, value=1)
        with col_c3:
            new_close = st.number_input("Statement Close Day", min_value=1, max_value=31, value=4)
            
        if st.form_submit_button("Save Account"):
            if not new_acc_name.strip():
                st.error("Please provide an account name.")
            else:
                row = [
                    new_acc_name.strip(),
                    new_acc_type,
                    new_acc_role.strip(),
                    float(new_acc_base),
                    float(new_limit) if new_acc_type != "Cash / Bank" else 0.0,
                    int(new_due) if new_acc_type != "Cash / Bank" else 0,
                    int(new_close) if new_acc_type != "Cash / Bank" else 0
                ]
                try:
                    append_account_to_sheet(row)
                    st.success(f"✅ Added {new_acc_name} to Accounts_Master!")
                    st.rerun()
                except Exception as err:
                    st.error(f"Error saving account: {err}")

# ==========================================
# 6. AI EXECUTIVE SUMMARY & KEY FETCHER
# ==========================================
def get_gemini_api_key():
    if "GEMINI_API_KEY" in st.secrets:
        return st.secrets["GEMINI_API_KEY"]
    if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
        return st.secrets["connections"]["gsheets"].get("GEMINI_API_KEY", None)
    return None

@st.cache_data(ttl=300, show_spinner=False)
def fetch_ai_insights_cached(net_cash, tot_cash, p_debt, b_debt, p_util, azeo_card, unpaid_stmt_cards):
    try:
        api_key = get_gemini_api_key()
        if api_key:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-3.6-flash")
            prompt = f"""
            You are a sharp personal wealth advisor. Today's date is {today_dt.strftime('%B %d, %Y')}.
            Provide a direct 2-sentence executive summary:
            - Net Liquid Cash is ${net_cash:,.2f} (Total Cash: ${tot_cash:,.2f}, Personal CC Debt: ${p_debt:,.2f}, Biz Debt: ${b_debt:,.2f}).
            - Personal Credit Util: {p_util:.2f}%.
            - Active AZEO Card: {azeo_card} (maintain at ~$10 for optimal credit reporting).
            - Cards with unpaid statement balances: {unpaid_stmt_cards if unpaid_stmt_cards else 'None, all statement balances are paid'}.
            Keep it punchy, practical, and under 35 words total.
            """
            response = model.generate_content(prompt)
            return response.text.replace("$", r"\$")
    except Exception:
        pass
    return f"💡 **Executive Snapshot:** Net liquid cash stands at \\${net_cash:,.2f} with credit utilization optimized at {p_util:.2f}%. Maintain {azeo_card} at ~\\$10 for your AZEO boost while clearing non-AZEO cards to \\$0."

# ==========================================
# 7. APP TABS & UI RENDERING
# ==========================================
tabs = st.tabs([
    "💳 Accounts & Credit Hub", 
    "⚡ Command Center", 
    "📊 Analytics & Charts", 
    "🏠 Home Goal", 
    "💬 AI Advisor"
])

# ------------------------------------------
# TAB 1: ACCOUNTS & CREDIT HUB (DEFAULT LOAD PAGE)
# ------------------------------------------
with tabs[0]:
    col_h1, col_h2 = st.columns([3.6, 1.2], vertical_alignment="center")
    with col_h1:
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:center; padding: 2px 0;">
            <h3 style="margin:0; padding:0; font-size:1.2rem; font-weight:700; color:#F8FAFC; line-height:1.2;">🏦 Cash & Checking</h3>
            <span style="font-size:1.15rem; font-weight:800; color:#38BDF8; margin-left: 8px;">${total_cash:,.2f}</span>
        </div>
        """, unsafe_allow_html=True)
    with col_h2:
        st.markdown('<div class="small-add-btn">', unsafe_allow_html=True)
        if st.button("➕ Add Account", key="btn_open_add_account"):
            open_new_account_dialog()
        st.markdown('</div>', unsafe_allow_html=True)

    # 1. CASH / BANK CARDS
    for acc in live_cash_registry:
        bal = acc["current_balance"]
        pct_of_total = (bal / total_cash) * 100 if total_cash > 0 else 0.0
        tx_rows = get_tx_rows_html(acc['name'])
        san_name = re.sub(r'[^a-zA-Z0-9_]', '_', acc['name'])
        
        btn_html = f"""
        <div style="display:flex; gap:6px; margin-bottom:8px; flex-wrap:wrap;">
            <button class="drawer-btn drawer-btn-emerald" type="button" data-trigger="trig_inc_{san_name}">💵 Deposit</button>
            <button class="drawer-btn drawer-btn-purple" type="button" data-trigger="trig_trans_{san_name}">🔁 Transfer</button>
            <button class="drawer-btn drawer-btn-slate" type="button" data-trigger="trig_bexp_{san_name}">💸 Expense</button>
        </div>
        """
        
        render_account_card(
            title=acc['name'],
            subtitle=acc['role'],
            right_val=f"${bal:,.2f}",
            right_sub=f"{pct_of_total:.1f}% of cash",
            tx_html=tx_rows,
            action_buttons_html=btn_html
        )

    st.divider()

    st.subheader("💳 Personal Credit Cards (AZEO Strategy)")
    st.caption(f"Overall Personal Util: **{personal_utilization:.2f}%** (${personal_cc_debt:,.2f} / ${personal_cc_limit:,.2f}). Active AZEO: **{azeo_card_name}**.")
    
    # 2. PERSONAL CREDIT CARDS
    for c in live_personal_cc:
        bal = c["current_balance"]
        limit = c["limit"]
        util = c["utilization"]
        tx_rows = get_tx_rows_html(c['name'])
        san_name = re.sub(r'[^a-zA-Z0-9_]', '_', c['name'])
        
        btn_html = f"""
        <div style="display:flex; gap:6px; margin-bottom:8px; flex-wrap:wrap;">
            <button class="drawer-btn drawer-btn-blue" type="button" data-trigger="trig_cexp_{san_name}">💳 Charge</button>
            <button class="drawer-btn drawer-btn-purple" type="button" data-trigger="trig_cpay_{san_name}">🔄 Pay Card</button>
        </div>
        """
        
        render_account_card(
            title=c['name'],
            subtitle=f"Limit: ${limit:,.0f} | Closes: {c['close_str']}",
            right_val=f"${bal:.2f}",
            right_sub=f"({util:.1f}%)",
            extra_left=c['action_text'],
            extra_right=c['badge_html'],
            tx_html=tx_rows,
            action_buttons_html=btn_html
        )

    st.divider()

    st.subheader("💼 Business Credit Cards")
    st.caption("Business cards do not report to your personal credit score.")
    
    # 3. BUSINESS CREDIT CARDS
    for c in live_biz_cc:
        bal = c["current_balance"]
        tx_rows = get_tx_rows_html(c['name'])
        san_name = re.sub(r'[^a-zA-Z0-9_]', '_', c['name'])
        
        btn_html = f"""
        <div style="display:flex; gap:6px; margin-bottom:8px; flex-wrap:wrap;">
            <button class="drawer-btn drawer-btn-blue" type="button" data-trigger="trig_bcexp_{san_name}">💳 Charge</button>
            <button class="drawer-btn drawer-btn-purple" type="button" data-trigger="trig_bcpay_{san_name}">🔄 Pay Card</button>
        </div>
        """
        
        render_account_card(
            title=c['name'],
            subtitle="Business Card",
            right_val=f"${bal:.2f}",
            right_sub="",
            extra_left=f"Due: {c['due_str']} | Closes: {c['close_str']}",
            extra_right='<span style="background-color:#312E81;color:#C7D2FE;padding:4px 9px;border-radius:6px;font-size:11px;font-weight:700;white-space:nowrap;">💼 BUSINESS</span>',
            tx_html=tx_rows,
            action_buttons_html=btn_html
        )

    # 4. ZERO-PIXEL INVISIBLE NATIVE STREAMLIT BUTTON TRIGGERS
    with st.container(key="hidden_triggers"):
        for acc in live_cash_registry:
            san_name = re.sub(r'[^a-zA-Z0-9_]', '_', acc['name'])
            if st.button(f"btn_inc_{san_name}", key=f"trig_inc_{san_name}"):
                modal_bank_income(acc['name'])
            if st.button(f"btn_trans_{san_name}", key=f"trig_trans_{san_name}"):
                modal_bank_transfer(acc['name'])
            if st.button(f"btn_bexp_{san_name}", key=f"trig_bexp_{san_name}"):
                modal_bank_expense(acc['name'])
                
        for c in live_personal_cc:
            san_name = re.sub(r'[^a-zA-Z0-9_]', '_', c['name'])
            if st.button(f"btn_cexp_{san_name}", key=f"trig_cexp_{san_name}"):
                modal_card_expense(c['name'])
            if st.button(f"btn_cpay_{san_name}", key=f"trig_cpay_{san_name}"):
                modal_card_payment(c['name'], c['current_balance'])
                
        for c in live_biz_cc:
            san_name = re.sub(r'[^a-zA-Z0-9_]', '_', c['name'])
            if st.button(f"btn_bcexp_{san_name}", key=f"trig_bcexp_{san_name}"):
                modal_card_expense(c['name'])
            if st.button(f"btn_bcpay_{san_name}", key=f"trig_bcpay_{san_name}"):
                modal_card_payment(c['name'], c['current_balance'])

    # 5. DELEGATED EVENT LISTENER
    components.html("""
    <script>
    (function() {
        var parentDoc;
        try {
            parentDoc = window.parent.document;
        } catch(e) {
            return;
        }
        if (!parentDoc) return;
        
        if (window.parent._hubClickAttached) return;
        window.parent._hubClickAttached = true;
        
        parentDoc.addEventListener('click', function(e) {
            var btn = e.target.closest('[data-trigger]');
            if (!btn) return;
            e.preventDefault();
            e.stopPropagation();
            
            var triggerKey = btn.getAttribute('data-trigger');
            if (!triggerKey) return;
            
            var targetBtn = parentDoc.querySelector('.st-key-' + triggerKey + ' button');
            if (targetBtn) {
                targetBtn.click();
            }
        }, true);
    })();
    </script>
    """, height=0, width=0)

# ------------------------------------------
# TAB 2: COMMAND CENTER
# ------------------------------------------
with tabs[1]:
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
    
    ai_placeholder = st.empty()
    ai_placeholder.caption("✨ *Fetching personalized AI insights...*")

    st.subheader("⚡ Fast Entry")
    tab_exp, tab_inc, tab_pay, tab_trans = st.tabs(["💸 Expense", "💵 Income", "🔄 CC Payment", "🔁 Transfer"])

    with tab_exp:
        with st.form("log_expense_form", clear_on_submit=True):
            amt = st.number_input("Amount ($)", min_value=0.01, step=1.00, format="%.2f", key="f_exp_amt")
            selected_acc = st.selectbox("Card / Account", all_account_names, key="f_exp_acc")
            selected_cat = st.selectbox("Category", categories_list, key="f_exp_cat")
            vendor = st.text_input("Merchant / Store", placeholder="e.g. Amazon, Shell, Trader Joe's", key="f_exp_ven")
            item_desc = st.text_input("Item Description (Optional)", placeholder="e.g. Phone case, Work lunch", key="f_exp_item")
            entry_date = st.date_input("Date", value=datetime.today(), key="f_exp_date")
            goal_tag = st.selectbox("Goal Tag", ["General Living", "Baltimore 1st Home", "Emergency Vault", "Business"], key="f_exp_gt")
            
            if st.form_submit_button("Record Expense"):
                tx_id = f"TX-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                date_str = entry_date.strftime("%Y-%m-%d")
                
                new_row_values = [
                    tx_id,
                    date_str,
                    selected_acc,
                    "Expense",
                    selected_cat,
                    vendor,
                    float(amt),
                    goal_tag,
                    item_desc,
                    "Mobile App Entry"
                ]
                try:
                    append_tx_to_sheet(new_row_values)
                    st.success(f"✅ Successfully written: ${amt:.2f} to {selected_cat} on {selected_acc}!")
                    st.rerun()
                except Exception as err:
                    st.error(f"❌ Write Error: {str(err)}\n{traceback.format_exc()}")

    with tab_inc:
        with st.form("log_income_form", clear_on_submit=True):
            inc_amt = st.number_input("Amount ($)", min_value=0.01, step=1.00, format="%.2f", key="f_inc_amt")
            inc_acc = st.selectbox("Deposit Into", deposit_accounts, key="f_inc_acc")
            inc_cat = st.selectbox("Income Source", ["W2 Salary", "Uber Income", "Other Income"], key="f_inc_cat")
            inc_desc = st.text_input("Payer / Source", placeholder="e.g. Employer Payroll, Uber Payout", key="f_inc_desc")
            inc_item = st.text_input("Income Memo (Optional)", placeholder="e.g. Weekend boost", key="f_inc_item")
            inc_date = st.date_input("Date", value=datetime.today(), key="f_inc_date")
            
            if st.form_submit_button("Record Income"):
                tx_id = f"TX-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                date_str = inc_date.strftime("%Y-%m-%d")
                goal = "Baltimore 1st Home" if "4979" in inc_acc or "SECU" in inc_acc else "General Living"
                
                new_row_values = [
                    tx_id,
                    date_str,
                    inc_acc,
                    "Income",
                    inc_cat,
                    inc_desc,
                    float(inc_amt),
                    goal,
                    inc_item,
                    "Mobile App Entry"
                ]
                try:
                    append_tx_to_sheet(new_row_values)
                    st.success(f"✅ Logged ${inc_amt:.2f} {inc_cat} into {inc_acc}!")
                    st.rerun()
                except Exception as err:
                    st.error(f"❌ Write Error: {str(err)}\n{traceback.format_exc()}")

    with tab_pay:
        with st.form("log_payment_form", clear_on_submit=True):
            all_live_cards = live_personal_cc + live_biz_cc
            card_balance_map = {c["name"]: c["current_balance"] for c in all_live_cards}
            all_cc_names = list(card_balance_map.keys())

            target_card = st.selectbox(
                "Credit Card Paid",
                all_cc_names,
                format_func=lambda x: f"{x}  —  ${card_balance_map.get(x, 0.0):,.2f} balance",
                key="f_pay_to"
            )

            pay_amt = st.number_input(
                "Payment Amount ($)", 
                min_value=0.01, 
                step=1.00, 
                format="%.2f", 
                key="f_pay_amt"
            )
            from_account = st.selectbox("Paid From", deposit_accounts, key="f_pay_from")
            pay_item = st.text_input("Payment Memo (Optional)", placeholder="e.g. Statement balance payoff", key="f_pay_item")
            pay_date = st.date_input("Date", value=datetime.today(), key="f_pay_date")
            
            if st.form_submit_button("Record CC Payment"):
                tx_id = f"TX-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                date_str = pay_date.strftime("%Y-%m-%d")
                
                new_row_values = [
                    tx_id,
                    date_str,
                    target_card,
                    "CC Payment",
                    "CC Payment",
                    f"Paid from {from_account}",
                    float(pay_amt),
                    "General Living",
                    pay_item,
                    "Mobile App Entry"
                ]
                try:
                    append_tx_to_sheet(new_row_values)
                    st.success(f"✅ Recorded ${pay_amt:.2f} payment to {target_card}!")
                    st.rerun()
                except Exception as err:
                    st.error(f"❌ Write Error: {str(err)}\n{traceback.format_exc()}")

    with tab_trans:
        with st.form("log_transfer_form", clear_on_submit=True):
            trans_amt = st.number_input("Transfer Amount ($)", min_value=0.01, step=10.00, format="%.2f", key="f_trans_amt")
            
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                from_trans_acc = st.selectbox("Transfer From", deposit_accounts, key="f_trans_from")
            with col_t2:
                default_to_idx = 1 if len(deposit_accounts) > 1 else 0
                to_trans_acc = st.selectbox("Transfer Into", deposit_accounts, index=default_to_idx, key="f_trans_to")
                
            trans_memo = st.text_input("Transfer Memo (Optional)", placeholder="e.g. Weekly savings sweep, Checking top-off", key="f_trans_memo")
            trans_date = st.date_input("Date", value=datetime.today(), key="f_trans_date")
            
            if st.form_submit_button("Execute Transfer"):
                if from_trans_acc == to_trans_acc:
                    st.error("❌ Source and destination accounts cannot be the same.")
                else:
                    now_str = datetime.now().strftime('%Y%m%d%H%M%S')
                    date_str = trans_date.strftime("%Y-%m-%d")
                    memo_str = f" — {trans_memo.strip()}" if trans_memo.strip() else ""
                    goal_tag = "Baltimore 1st Home" if ("4979" in to_trans_acc or "SECU" in to_trans_acc) else "General Living"
                    
                    debit_row = [
                        f"TX-{now_str}-A", date_str, from_trans_acc, "Transfer", "Transfer / Sweep",
                        f"Transfer to {to_trans_acc}", float(trans_amt), goal_tag, f"Outflow to {to_trans_acc}{memo_str}", "Transfer Outflow"
                    ]
                    credit_row = [
                        f"TX-{now_str}-B", date_str, to_trans_acc, "Transfer", "Transfer / Sweep",
                        f"Transfer from {from_trans_acc}", float(trans_amt), goal_tag, f"Inflow from {from_trans_acc}{memo_str}", "Transfer Inflow"
                    ]
                    
                    try:
                        append_multiple_tx_to_sheet([debit_row, credit_row])
                        st.success(f"✅ Successfully transferred ${trans_amt:.2f} from {from_trans_acc} to {to_trans_acc}!")
                        st.rerun()
                    except Exception as err:
                        st.error(f"❌ Write Error: {str(err)}\n{traceback.format_exc()}")

# ------------------------------------------
# TAB 3: ANALYTICS & CHARTS
# ------------------------------------------
with tabs[2]:
    st.subheader("📊 Financial Analytics & Trends")

    if "current_analytics_date" not in st.session_state:
        st.session_state.current_analytics_date = date.today()

    with st.expander("📅 Jump to Specific Date / Past Year", expanded=False):
        picked_date = st.date_input(
            "Select any date to view historical analytics:",
            value=st.session_state.current_analytics_date
        )
        if picked_date != st.session_state.current_analytics_date:
            st.session_state.current_analytics_date = picked_date
            st.rerun()

    ref_date = st.session_state.current_analytics_date
    df_clean = df_tx.copy() if not df_tx.empty else pd.DataFrame()

    # BLOCK 1: WEEKLY ANALYTICS
    week_start = ref_date - timedelta(days=ref_date.weekday())
    week_end = week_start + timedelta(days=6)

    st.markdown("### 🗓️ Weekly Analytics ($300 Budget Cap)")
    
    w_col1, w_col2, w_col3 = st.columns([1, 4, 1])
    with w_col1:
        if st.button("◀", key="prev_week_btn", help="Previous Week"):
            st.session_state.current_analytics_date = ref_date - timedelta(days=7)
            st.rerun()
    with w_col2:
        st.markdown(
            f"<div style='text-align:center; font-weight:700; font-size:14px; color:#38BDF8; padding-top:8px;'>"
            f"{week_start.strftime('%b %d')} – {week_end.strftime('%b %d, %Y')}</div>",
            unsafe_allow_html=True
        )
    with w_col3:
        if st.button("▶", key="next_week_btn", help="Next Week"):
            st.session_state.current_analytics_date = ref_date + timedelta(days=7)
            st.rerun()

    df_week = df_clean[(df_clean["Date_DT"] >= week_start) & (df_clean["Date_DT"] <= week_end)] if not df_clean.empty else pd.DataFrame()
    w_income = df_week[df_week["Type"] == "Income"]["Amount"].sum() if not df_week.empty else 0.0
    w_expense = df_week[df_week["Type"] == "Expense"]["Amount"].sum() if not df_week.empty else 0.0
    w_net = w_income - w_expense

    ws_1, ws_2, ws_3 = st.columns(3)
    with ws_1:
        st.markdown(f"""<div class="stat-box"><div style="font-size:10px; color:#94A3B8;">INCOME</div><div style="font-size:16px; font-weight:800; color:#34D399;">+${w_income:,.2f}</div></div>""", unsafe_allow_html=True)
    with ws_2:
        st.markdown(f"""<div class="stat-box"><div style="font-size:10px; color:#94A3B8;">EXPENSES</div><div style="font-size:16px; font-weight:800; color:#F87171;">-${w_expense:,.2f}</div></div>""", unsafe_allow_html=True)
    with ws_3:
        net_color = "#38BDF8" if w_net >= 0 else "#F87171"
        st.markdown(f"""<div class="stat-box"><div style="font-size:10px; color:#94A3B8;">NET CASH</div><div style="font-size:16px; font-weight:800; color:{net_color};">${w_net:,.2f}</div></div>""", unsafe_allow_html=True)

    w_exp_df = df_week[df_week["Type"] == "Expense"] if not df_week.empty else pd.DataFrame()
    
    # RADIAL PROGRESSION DONUT DATA (WEEKLY)
    w_donut_labels = []
    w_donut_values = []
    w_donut_colors = []
    w_donut_hovers = []

    for cat_name, budget_amt in WEEKLY_BUDGET_TARGETS.items():
        spent_amt = w_exp_df[w_exp_df["Category"] == cat_name]["Amount"].sum() if not w_exp_df.empty else 0.0
        base_color = CATEGORY_COLORS.get(cat_name, "#3B82F6")
        
        spent_slice = min(spent_amt, budget_amt)
        if spent_slice > 0:
            w_donut_labels.append(f"{cat_name} (Spent)")
            w_donut_values.append(spent_slice)
            w_donut_colors.append(base_color)
            w_donut_hovers.append(f"<b>{cat_name}</b><br>Spent: ${spent_amt:.2f} / ${budget_amt:.2f}<br>({(spent_amt/budget_amt*100):.1f}% of weekly limit)")
        
        unspent_slice = max(budget_amt - spent_amt, 0.0)
        if unspent_slice > 0:
            w_donut_labels.append(f"{cat_name} (Left)")
            w_donut_values.append(unspent_slice)
            w_donut_colors.append("rgba(51, 65, 85, 0.35)")
            w_donut_hovers.append(f"<b>{cat_name}</b><br>Remaining: ${unspent_slice:.2f} of ${budget_amt:.2f} budget")
        
        if spent_amt > budget_amt:
            over_slice = spent_amt - budget_amt
            w_donut_labels.append(f"{cat_name} (Over)")
            w_donut_values.append(over_slice)
            w_donut_colors.append("#EF4444")
            w_donut_hovers.append(f"<b>{cat_name} OVER BUDGET</b><br>Over by: +${over_slice:.2f}")

    if not w_exp_df.empty:
        other_exp = w_exp_df[~w_exp_df["Category"].isin(WEEKLY_BUDGET_TARGETS.keys())]
        unbudgeted_amt = other_exp["Amount"].sum()
        if unbudgeted_amt > 0:
            w_donut_labels.append("Unbudgeted / Misc")
            w_donut_values.append(unbudgeted_amt)
            w_donut_colors.append("#F87171")
            w_donut_hovers.append(f"<b>Unbudgeted Spending</b><br>${unbudgeted_amt:.2f}")

    w_rem_total = max(WEEKLY_BUDGET_TOTAL - w_expense, 0.0)
    w_diff_str = f"+${w_rem_total:,.2f} Left" if (WEEKLY_BUDGET_TOTAL - w_expense) >= 0 else f"-${abs(WEEKLY_BUDGET_TOTAL - w_expense):,.2f} Over"
    w_center_title = f"<b>${w_expense:,.2f}</b><br><span style='font-size:11px; color:#94A3B8;'>of $300 Budget</span><br><span style='font-size:12px; color:{'#34D399' if (WEEKLY_BUDGET_TOTAL - w_expense) >= 0 else '#F87171'};'><b>{w_diff_str}</b></span>"

    fig_week_donut = go.Figure(go.Pie(
        labels=w_donut_labels,
        values=w_donut_values,
        hole=0.55,
        sort=False,
        direction='clockwise',
        marker=dict(colors=w_donut_colors, line=dict(color='#0F172A', width=1.5)),
        hovertemplate="%{customdata}<extra></extra>",
        customdata=w_donut_hovers,
        textinfo='none'
    ))

    fig_week_donut.update_layout(
        margin=dict(l=10, r=10, t=30, b=10),
        height=320,
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#CBD5E1"),
        annotations=[dict(text=w_center_title, x=0.5, y=0.5, font_size=14, showarrow=False)]
    )
    st.plotly_chart(fig_week_donut, use_container_width=True)

    st.divider()

    # BLOCK 2: MONTHLY ANALYTICS
    m_year, m_month = ref_date.year, ref_date.month
    month_start = date(m_year, m_month, 1)
    month_end = date(m_year, m_month, calendar.monthrange(m_year, m_month)[1])

    days_in_month = (month_end - month_start).days + 1
    m_multiplier = days_in_month / 7.0
    monthly_budget_target = m_multiplier * WEEKLY_BUDGET_TOTAL

    st.markdown(f"### 📆 Monthly Analytics ({month_start.strftime('%B %Y')})")
    
    m_col1, m_col2, m_col3 = st.columns([1, 4, 1])
    with m_col1:
        if st.button("◀", key="prev_month_btn", help="Previous Month"):
            prev_m = m_month - 1 if m_month > 1 else 12
            prev_y = m_year if m_month > 1 else m_year - 1
            st.session_state.current_analytics_date = date(prev_y, prev_m, 1)
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
            st.session_state.current_analytics_date = date(next_y, next_m, 1)
            st.rerun()

    df_month = df_clean[(df_clean["Date_DT"] >= month_start) & (df_clean["Date_DT"] <= month_end)] if not df_clean.empty else pd.DataFrame()
    m_income = df_month[df_month["Type"] == "Income"]["Amount"].sum() if not df_month.empty else 0.0
    m_expense = df_month[df_month["Type"] == "Expense"]["Amount"].sum() if not df_month.empty else 0.0
    m_net = m_income - m_expense

    ms_1, ms_2, ms_3 = st.columns(3)
    with ms_1:
        st.markdown(f"""<div class="stat-box"><div style="font-size:10px; color:#94A3B8;">MONTH INCOME</div><div style="font-size:16px; font-weight:800; color:#34D399;">+${m_income:,.2f}</div></div>""", unsafe_allow_html=True)
    with ms_2:
        st.markdown(f"""<div class="stat-box"><div style="font-size:10px; color:#94A3B8;">MONTH EXPENSES</div><div style="font-size:16px; font-weight:800; color:#F87171;">-${m_expense:,.2f}</div></div>""", unsafe_allow_html=True)
    with ms_3:
        m_net_color = "#38BDF8" if m_net >= 0 else "#F87171"
        st.markdown(f"""<div class="stat-box"><div style="font-size:10px; color:#94A3B8;">MONTH NET</div><div style="font-size:16px; font-weight:800; color:{m_net_color};">${m_net:,.2f}</div></div>""", unsafe_allow_html=True)

    m_exp_df = df_month[df_month["Type"] == "Expense"] if not df_month.empty else pd.DataFrame()
    
    m_donut_labels = []
    m_donut_values = []
    m_donut_colors = []
    m_donut_hovers = []

    for cat_name, w_base in WEEKLY_BUDGET_TARGETS.items():
        m_cat_budget = w_base * m_multiplier
        spent_amt = m_exp_df[m_exp_df["Category"] == cat_name]["Amount"].sum() if not m_exp_df.empty else 0.0
        base_color = CATEGORY_COLORS.get(cat_name, "#3B82F6")
        
        spent_slice = min(spent_amt, m_cat_budget)
        if spent_slice > 0:
            m_donut_labels.append(f"{cat_name} (Spent)")
            m_donut_values.append(spent_slice)
            m_donut_colors.append(base_color)
            m_donut_hovers.append(f"<b>{cat_name}</b><br>Spent: ${spent_amt:.2f} / ${m_cat_budget:.2f}<br>({(spent_amt/m_cat_budget*100):.1f}% of month budget)")
        
        unspent_slice = max(m_cat_budget - spent_amt, 0.0)
        if unspent_slice > 0:
            m_donut_labels.append(f"{cat_name} (Left)")
            m_donut_values.append(unspent_slice)
            m_donut_colors.append("rgba(51, 65, 85, 0.35)")
            m_donut_hovers.append(f"<b>{cat_name}</b><br>Remaining: ${unspent_slice:.2f} of ${m_cat_budget:.2f} budget")
        
        if spent_amt > m_cat_budget:
            over_slice = spent_amt - m_cat_budget
            m_donut_labels.append(f"{cat_name} (Over)")
            m_donut_values.append(over_slice)
            m_donut_colors.append("#EF4444")
            m_donut_hovers.append(f"<b>{cat_name} OVER BUDGET</b><br>Over by: +${over_slice:.2f}")

    if not m_exp_df.empty:
        other_exp = m_exp_df[~m_exp_df["Category"].isin(WEEKLY_BUDGET_TARGETS.keys())]
        unbudgeted_amt = other_exp["Amount"].sum()
        if unbudgeted_amt > 0:
            m_donut_labels.append("Unbudgeted / Misc")
            m_donut_values.append(unbudgeted_amt)
            m_donut_colors.append("#F87171")
            m_donut_hovers.append(f"<b>Unbudgeted Spending</b><br>${unbudgeted_amt:.2f}")

    m_rem_total = max(monthly_budget_target - m_expense, 0.0)
    m_diff_str = f"+${m_rem_total:,.2f} Left" if (monthly_budget_target - m_expense) >= 0 else f"-${abs(monthly_budget_target - m_expense):,.2f} Over"
    m_center_title = f"<b>${m_expense:,.2f}</b><br><span style='font-size:11px; color:#94A3B8;'>of ${monthly_budget_target:,.0f} Budget</span><br><span style='font-size:12px; color:{'#34D399' if (monthly_budget_target - m_expense) >= 0 else '#F87171'};'><b>{m_diff_str}</b></span>"

    fig_month_donut = go.Figure(go.Pie(
        labels=m_donut_labels,
        values=m_donut_values,
        hole=0.55,
        sort=False,
        direction='clockwise',
        marker=dict(colors=m_donut_colors, line=dict(color='#0F172A', width=1.5)),
        hovertemplate="%{customdata}<extra></extra>",
        customdata=m_donut_hovers,
        textinfo='none'
    ))

    fig_month_donut.update_layout(
        margin=dict(l=10, r=10, t=30, b=10),
        height=320,
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#CBD5E1"),
        annotations=[dict(text=m_center_title, x=0.5, y=0.5, font_size=14, showarrow=False)]
    )
    st.plotly_chart(fig_month_donut, use_container_width=True)

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
                    st.session_state.current_analytics_date = w_s
                    st.rerun()

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
            <div style="font-size:18px; font-weight:800; color:#38BDF8;">${remaining_goal:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with col_b:
        st.markdown(f"""
        <div class="stat-box">
            <div style="font-size:11px; color:#94A3B8;">TARGET DEADLINE</div>
            <div style="font-size:16px; font-weight:800; color:#34D399;">March 1, 2027</div>
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
    * **Net Cash at Settlement:** $20,000
    * **Post-Closing 3-Mo Reserves:** $6,500
    * **Total Liquid Target:** **$26,500**
    """)

# ------------------------------------------
# TAB 5: AI FINANCIAL ADVISOR CHATBOT
# ------------------------------------------
with tabs[4]:
    st.subheader("💬 AI Financial Advisor")
    st.caption("Ask questions about your budget, credit card AZEO strategy, spending habits, or home purchase goal.")

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {"role": "assistant", "content": "Hey! I have real-time access to your ledger, balances, and $26.5k Baltimore home purchase target. What would you like to check or plan today?"}
        ]

    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_prompt := st.chat_input("Ask a question about your finances..."):
        st.session_state.chat_messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)

        recent_tx_summary = df_tx.tail(15).to_dict(orient="records") if not df_tx.empty else "No transactions logged yet."
        
        system_context = f"""
        You are an elite, highly knowledgeable personal financial advisor and real estate strategist assisting the user.
        Today's date is {today_dt.strftime('%B %d, %Y')}.
        You have direct access to their live financial snapshot:
        - Total Cash on Hand: ${total_cash:,.2f} across checking and savings accounts.
        - Total Personal CC Debt: ${personal_cc_debt:,.2f} across ${personal_cc_limit:,.2f} limit (Overall Util: {personal_utilization:.2f}%)
        - Business CC Debt: ${biz_cc_debt:,.2f} (Chase 0431)
        - Net Liquid Cash: ${net_liquid_cash:,.2f}
        - 1st Home Goal: $26,500 target by March 1, 2027 (${total_cash:,.2f} saved so far, ${remaining_goal:,.2f} remaining).
        - Dynamic AZEO Card: {azeo_card_name}.
        - Recent 15 Ledger Entries: {recent_tx_summary}

        Provide direct, helpful, and concise guidance. When mentioning money, escape dollar signs with a backslash (e.g. \\$200).
        """

        with st.chat_message("assistant"):
            try:
                api_key = get_gemini_api_key()
                if api_key:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel(
                        "gemini-3.6-flash",
                        system_instruction=system_context
                    )
                    
                    history_payload = []
                    for m in st.session_state.chat_messages[:-1]:
                        gemini_role = "user" if m["role"] == "user" else "model"
                        history_payload.append({"role": gemini_role, "parts": [m["content"]]})

                    chat_session = model.start_chat(history=history_payload)
                    response = chat_session.send_message(user_prompt)
                    bot_reply = response.text.replace("$", r"\$")
                else:
                    bot_reply = "⚠️ GEMINI_API_KEY is not configured in your Streamlit Secrets. Please add your key to enable live AI responses."
            except Exception as e:
                bot_reply = f"⚠️ Could not generate response: {e}"

            st.markdown(bot_reply)
            st.session_state.chat_messages.append({"role": "assistant", "content": bot_reply})

# ==========================================
# 8. ASYNC POPULATE SUMMARY PLACEHOLDER
# ==========================================
unpaid_stmt_list = [f"{c['name']} (${c['stmt_due']:.2f})" for c in live_personal_cc if c.get('stmt_due', 0) > 0.01]
unpaid_stmt_str = ", ".join(unpaid_stmt_list)

ai_insight_text = fetch_ai_insights_cached(
    net_liquid_cash, total_cash, personal_cc_debt, biz_cc_debt, personal_utilization, azeo_card_name, unpaid_stmt_str
)
ai_placeholder.info(ai_insight_text)
