import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import calendar
import traceback
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

    div.small-add-btn {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        width: 100%;
    }
    div.small-add-btn button {
        height: 30px !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        padding: 3px 10px !important;
        border-radius: 8px !important;
        margin: 0 !important;
        white-space: nowrap !important;
    }

    div[data-testid="stExpander"] {
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
        background-color: #1E293B !important;
        margin-bottom: 10px !important;
        overflow: hidden !important;
    }
    div[data-testid="stExpander"] summary {
        background-color: #1E293B !important;
        padding: 12px 14px !important;
        font-size: 14px !important;
        color: #F8FAFC !important;
        border-radius: 12px !important;
    }
    div[data-testid="stExpander"] summary:hover {
        background-color: #243248 !important;
    }
    div[data-testid="stExpander"] summary p {
        font-weight: 700 !important;
        color: #F8FAFC !important;
        font-size: 14px !important;
        margin: 0 !important;
    }
    div[data-testid="stExpander"] div[role="region"] {
        background-color: #0F172A !important;
        padding: 12px !important;
        border-top: 1px solid #334155 !important;
    }

    .top-success-popup {
        position: fixed !important;
        top: 22px !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        z-index: 99999999 !important;
        background: linear-gradient(135deg, #065F46 0%, #047857 100%) !important;
        border: 2px solid #34D399 !important;
        color: #FFFFFF !important;
        padding: 13px 26px !important;
        border-radius: 12px !important;
        font-weight: 800 !important;
        font-size: 14px !important;
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.65), 0 0 16px rgba(52, 211, 153, 0.45) !important;
        display: flex !important;
        align-items: center !important;
        gap: 10px !important;
        text-align: center !important;
        max-width: 90% !important;
    }

    .badge-opt { background-color: #065F46; color: #6EE7B7; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; }
    .badge-warn { background-color: #7C2D12; color: #FDBA74; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; }
    .badge-biz { background-color: #312E81; color: #C7D2FE; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

if "success_notification" in st.session_state and st.session_state["success_notification"]:
    s_msg = st.session_state["success_notification"]
    del st.session_state["success_notification"]
    st.markdown(
        f'<div class="top-success-popup"><span style="font-size:18px;">✅</span><span>{s_msg}</span></div>',
        unsafe_allow_html=True
    )

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
# 3. GSHEETS BACKEND & DATA REGISTRY
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

# 1. CASH BALANCES
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

# 2. PERSONAL CC BALANCES & AZEO
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
        badge_html = '<span class="badge-warn">⚠️ STMT DUE</span>'
        action_text = f"Pay ${stmt_due:.2f} stmt balance by {next_due.strftime('%b %d')}"
    elif is_azeo:
        badge_html = '<span class="badge-opt">✅ AZEO ACTIVE (~1%)</span>'
        action_text = f"Leave ${bal:.2f} to report on {next_close.strftime('%b %d')}"
    elif bal > 0.01:
        badge_html = '<span class="badge-warn">⚠️ PAY BEFORE CLOSE</span>'
        action_text = f"Pay ${bal:.2f} by {next_close.strftime('%b %d')} to report $0"
    else:
        badge_html = '<span class="badge-opt">✅ $0 REPORTING</span>'
        action_text = f"Reports $0 on {next_close.strftime('%b %d')}"
        
    card_dict = dict(c)
    card_dict["is_azeo_active"] = is_azeo
    card_dict["utilization"] = (bal / c["limit"]) * 100 if c["limit"] > 0 else 0.0
    card_dict["due_str"] = next_due.strftime("%b %d")
    card_dict["close_str"] = next_close.strftime("%b %d")
    card_dict["action_text"] = action_text
    card_dict["badge_html"] = badge_html
    live_personal_cc.append(card_dict)

# 3. BUSINESS CC BALANCES
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

categories_list = [
    "Vehicle & Gas", "Housing & Rent", "Groceries & Food", 
    "Personal & Entertainment", "Dining Out & Coffee", 
    "Business Operations", "Subscriptions & Software", "Miscellaneous / Buffer"
]

all_account_names = list(df_registry["Account_Name"])
deposit_accounts = list(df_registry[df_registry["Account_Type"] == "Cash / Bank"]["Account_Name"])

# ==========================================
# 4. MODALS (@st.dialog)
# ==========================================
@st.dialog("Record Income / Deposit")
def modal_bank_income(acc_name):
    st.markdown(f"**Target Account:** `{acc_name}`")
    with st.form(f"form_m_inc_{acc_name}", clear_on_submit=True):
        inc_amt = st.number_input("Amount ($)", value=None, min_value=0.01, step=1.00, format="%.2f", placeholder="0.00")
        inc_cat = st.selectbox("Source", ["W2 Salary", "Uber Income", "Other Income"])
        payer = st.text_input("Payer / Store", placeholder="e.g. Employer Payroll, Uber Payout, Client")
        memo = st.text_input("Memo (Optional)", placeholder="e.g. Paycheck deposit")
        tx_date = st.date_input("Date", value=datetime.today())
        gt = "Baltimore 1st Home" if ("4979" in acc_name or "SECU" in acc_name) else "General Living"
        
        if st.form_submit_button("Record Deposit"):
            if inc_amt is None or inc_amt <= 0:
                st.error("Please enter a valid amount.")
            else:
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
                    st.session_state["success_notification"] = f"Deposited ${inc_amt:,.2f} into {acc_name}!"
                    st.rerun()
                except Exception as err:
                    st.error(f"Error: {err}")

@st.dialog("Execute Account Transfer")
def modal_bank_transfer(from_acc):
    st.markdown(f"**From Account:** `{from_acc}`")
    other_accounts = [a for a in deposit_accounts if a != from_acc]
    target_options = other_accounts if other_accounts else deposit_accounts
    with st.form(f"form_m_trans_{from_acc}", clear_on_submit=True):
        trans_amt = st.number_input("Transfer Amount ($)", value=None, min_value=0.01, step=10.00, format="%.2f", placeholder="0.00")
        to_acc = st.selectbox("Transfer Into", target_options)
        memo = st.text_input("Memo (Optional)", placeholder="e.g. Weekly savings sweep")
        tx_date = st.date_input("Date", value=datetime.today())
        
        if st.form_submit_button("Confirm Transfer"):
            if trans_amt is None or trans_amt <= 0:
                st.error("Please enter a valid transfer amount.")
            elif from_acc == to_acc:
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
                    st.session_state["success_notification"] = f"Transferred ${trans_amt:,.2f} from {from_acc} to {to_acc}!"
                    st.rerun()
                except Exception as err:
                    st.error(f"Error: {err}")

@st.dialog("Record Debit Expense")
def modal_bank_expense(acc_name):
    st.markdown(f"**Account:** `{acc_name}`")
    with st.form(f"form_m_b_exp_{acc_name}", clear_on_submit=True):
        amt = st.number_input("Amount ($)", value=None, min_value=0.01, step=1.00, format="%.2f", placeholder="0.00")
        cat = st.selectbox("Category", categories_list)
        vendor = st.text_input("Merchant / Store", placeholder="e.g. Landlord, Shell, Trader Joe's")
        desc = st.text_input("Memo (Optional)", placeholder="e.g. Direct withdrawal")
        tx_date = st.date_input("Date", value=datetime.today())
        gt = st.selectbox("Goal Tag", ["General Living", "Baltimore 1st Home", "Emergency Vault", "Business"])
        
        if st.form_submit_button("Save Expense"):
            if amt is None or amt <= 0:
                st.error("Please enter a valid expense amount.")
            else:
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
                    st.session_state["success_notification"] = f"Saved ${amt:,.2f} expense from {acc_name}!"
                    st.rerun()
                except Exception as err:
                    st.error(f"Error: {err}")

@st.dialog("Record Credit Card Charge")
def modal_card_expense(card_name):
    st.markdown(f"**Card:** `{card_name}`")
    with st.form(f"form_m_c_exp_{card_name}", clear_on_submit=True):
        amt = st.number_input("Amount ($)", value=None, min_value=0.01, step=1.00, format="%.2f", placeholder="0.00")
        cat = st.selectbox("Category", categories_list)
        vendor = st.text_input("Merchant / Store", placeholder="e.g. Amazon, Shell, Quick Mart")
        desc = st.text_input("Memo (Optional)", placeholder="e.g. Gas, Work lunch")
        tx_date = st.date_input("Date", value=datetime.today())
        gt = st.selectbox("Goal Tag", ["General Living", "Baltimore 1st Home", "Emergency Vault", "Business"])
        
        if st.form_submit_button("Record Charge"):
            if amt is None or amt <= 0:
                st.error("Please enter a valid charge amount.")
            else:
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
                    st.session_state["success_notification"] = f"Saved ${amt:,.2f} charge on {card_name}!"
                    st.rerun()
                except Exception as err:
                    st.error(f"Error: {err}")

@st.dialog("Record Credit Card Payment")
def modal_card_payment(card_name, current_balance):
    st.markdown(f"**Card:** `{card_name}` | **Balance:** `${current_balance:,.2f}`")
    with st.form(f"form_m_c_pay_{card_name}", clear_on_submit=True):
        pay_amt = st.number_input("Payment Amount ($)", value=None, min_value=0.01, step=1.00, format="%.2f", placeholder="0.00")
        from_acc = st.selectbox("Paid From", deposit_accounts)
        memo = st.text_input("Memo (Optional)", placeholder="e.g. Statement payoff, AZEO adjustment")
        tx_date = st.date_input("Date", value=datetime.today())
        
        if st.form_submit_button("Submit Payment"):
            if pay_amt is None or pay_amt <= 0:
                st.error("Please enter a valid payment amount.")
            else:
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
                    st.session_state["success_notification"] = f"Recorded ${pay_amt:,.2f} payment to {card_name}!"
                    st.rerun()
                except Exception as err:
                    st.error(f"Error: {err}")

@st.dialog("➕ Add New Account to Registry")
def open_new_account_dialog():
    with st.form("new_account_form", clear_on_submit=True):
        new_acc_name = st.text_input("Account Identifier (e.g. Capital One 1122)")
        new_acc_type = st.radio("Account Type", ["Cash / Bank", "Personal CC", "Business CC"], horizontal=True)
        new_acc_role = st.text_input("Role / Memo (e.g. Dining Card, HYSA)")
        new_acc_base = st.number_input("Starting Base Balance ($)", value=0.00, min_value=0.00, step=10.00, format="%.2f")
        
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            new_limit = st.number_input("Credit Limit ($)", value=0.00, min_value=0.00, step=100.00, format="%.2f")
        with col_c2:
            new_due = st.number_input("Due Day", min_value=-1, max_value=31, value=1)
        with col_c3:
            new_close = st.number_input("Close Day", min_value=1, max_value=31, value=4)
            
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
                    st.session_state["success_notification"] = f"Added {new_acc_name} to Accounts_Master!"
                    st.rerun()
                except Exception as err:
                    st.error(f"Error saving account: {err}")

# ==========================================
# 5. AI INSIGHTS
# ==========================================
def get_gemini_api_key():
    if "GEMINI_API_KEY" in st.secrets:
        return st.secrets["GEMINI_API_KEY"]
    if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
        return st.secrets["connections"]["gsheets"].get("GEMINI_API_KEY", None)
    return None

@st.cache_data(ttl=300, show_spinner=False)
def fetch_ai_insights_cached(net_cash, tot_cash, p_debt, b_debt, p_util, azeo_card, unpaid_cards):
    try:
        api_key = get_gemini_api_key()
        if api_key:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-3.6-flash")
            prompt = f"""
            You are a sharp financial advisor. Today's date is {today_dt.strftime('%B %d, %Y')}.
            Provide a direct 2-sentence executive summary:
            - Net Liquid Cash: ${net_cash:,.2f} (Total Cash: ${tot_cash:,.2f}, Personal CCs: ${p_debt:,.2f}, Biz: ${b_debt:,.2f}).
            - Personal Util: {p_util:.2f}%.
            - Active AZEO Card: {azeo_card} (keep at ~$10 for reporting boost).
            - Unpaid cards: {unpaid_cards if unpaid_cards else 'None, all paid'}.
            Keep it punchy, practical, and under 35 words.
            """
            response = model.generate_content(prompt)
            return response.text.replace("$", r"\$")
    except Exception:
        pass
    return f"💡 **Executive Snapshot:** Net liquid cash stands at \\${net_cash:,.2f} with utilization optimized at {p_util:.2f}%. Maintain {azeo_card} at ~\\$10 for your AZEO boost."

# ==========================================
# 6. APP TABS & UI RENDERING (DEFAULT TAB 0: HUB)
# ==========================================
tabs = st.tabs([
    "💳 Accounts & Credit Hub", 
    "⚡ Command Center", 
    "📊 Analytics & Charts", 
    "🏠 Home Goal", 
    "💬 AI Advisor"
])

def render_card_transactions(acc_name):
    if not df_tx.empty and "Account" in df_tx.columns:
        sub_tx = df_tx[
            (df_tx["Account"] == acc_name) | 
            ((df_tx["Type"] == "CC Payment") & (df_tx["Merchant"].str.contains(acc_name, na=False)))
        ].tail(5)
        
        if not sub_tx.empty:
            st.markdown("<div style='font-size:12px; font-weight:700; color:#94A3B8; margin-top:6px; margin-bottom:4px;'>Last 5 Transactions:</div>", unsafe_allow_html=True)
            for _, r in sub_tx.iloc[::-1].iterrows():
                t_type = r.get("Type", "Expense")
                amt = float(r.get("Amount", 0.0))
                desc = r.get("Item_Description", "")
                vendor = r.get("Merchant", "")
                date_val = str(r.get("Date", ""))
                
                label = f"{vendor} — {desc}" if desc and str(desc).strip() != "" and str(desc).lower() != "nan" else vendor
                amt_color = "#34D399" if t_type == "Income" else ("#60A5FA" if t_type == "CC Payment" else "#F87171")
                prefix = "+" if t_type == "Income" else "-"
                
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; align-items:center; background:#162032; border-radius:6px; padding:6px 10px; margin-bottom:4px; font-size:12px; border:1px solid #334155;">
                    <div>
                        <span style="color:#CBD5E1; font-weight:600;">{label}</span>
                        <div style="font-size:10px; color:#64748B;">{date_val} • {t_type}</div>
                    </div>
                    <div style="font-weight:800; color:{amt_color}; font-size:13px; text-align:right;">
                        {prefix}${amt:,.2f}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("ℹ️ No transactions recorded for this account yet.")
    else:
        st.caption("ℹ️ No ledger records available.")

# ------------------------------------------
# TAB 0: ACCOUNTS & CREDIT HUB (DEFAULT LOAD)
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

    for acc in live_cash_registry:
        bal = acc["current_balance"]
        pct_of_total = (bal / total_cash) * 100 if total_cash > 0 else 0.0
        card_title = f"💵  {acc['name']}  —  ${bal:,.2f}  ({pct_of_total:.1f}% of cash)"
        
        with st.expander(card_title, expanded=False):
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <span style="font-size:12px; color:#94A3B8;"><b>Role:</b> {acc['role']}</span>
                <span style="font-weight:800; font-size:16px; color:#38BDF8;">${bal:,.2f}</span>
            </div>
            """, unsafe_allow_html=True)
            
            c_btn1, c_btn2, c_btn3 = st.columns(3)
            with c_btn1:
                if st.button("💵 Deposit", key=f"btn_inc_{acc['name']}"):
                    modal_bank_income(acc['name'])
            with c_btn2:
                if st.button("🔁 Transfer", key=f"btn_trans_{acc['name']}"):
                    modal_bank_transfer(acc['name'])
            with c_btn3:
                if st.button("💸 Expense", key=f"btn_bexp_{acc['name']}"):
                    modal_bank_expense(acc['name'])
                    
            render_card_transactions(acc["name"])

    st.divider()

    st.subheader("💳 Personal Credit Cards (AZEO Strategy)")
    st.caption(f"Overall Personal Util: **{personal_utilization:.2f}%** (${personal_cc_debt:,.2f} / ${personal_cc_limit:,.2f}). Active AZEO: **{azeo_card_name}**.")
    
    for c in live_personal_cc:
        bal = c["current_balance"]
        limit = c["limit"]
        util = c["utilization"]
        card_title = f"💳  {c['name']}  —  ${bal:.2f} ({util:.1f}%)  |  {c['badge_html']}"
        
        with st.expander(card_title, expanded=False):
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                <span style="font-size:12px; color:#94A3B8;"><b>Limit:</b> ${limit:,.0f}</span>
                <span style="font-weight:800; font-size:16px; color:#F8FAFC;">${bal:.2f}</span>
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <span style="font-size:12px; color:#CBD5E1;">{c['action_text']}</span>
                <div>{c['badge_html']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            c_btn1, c_btn2 = st.columns(2)
            with c_btn1:
                if st.button("💳 Charge", key=f"btn_cexp_{c['name']}"):
                    modal_card_expense(c['name'])
            with c_btn2:
                if st.button("🔄 Pay Card", key=f"btn_cpay_{c['name']}"):
                    modal_card_payment(c['name'], c['current_balance'])
                    
            render_card_transactions(c["name"])

    st.divider()

    st.subheader("💼 Business Credit Cards")
    st.caption("Business cards do not report to your personal credit score.")
    
    for c in live_biz_cc:
        bal = c["current_balance"]
        card_title = f"💼  {c['name']}  —  ${bal:.2f}  |  💼 BUSINESS"
        
        with st.expander(card_title, expanded=False):
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                <span style="font-size:12px; color:#94A3B8;"><b>Business Card</b></span>
                <span style="font-weight:800; font-size:16px; color:#F8FAFC;">${bal:.2f}</span>
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <span style="font-size:12px; color:#CBD5E1;">Due: {c['due_str']} | Closes: {c['close_str']}</span>
                <div><span class="badge-biz">💼 BUSINESS</span></div>
            </div>
            """, unsafe_allow_html=True)
            
            c_btn1, c_btn2 = st.columns(2)
            with c_btn1:
                if st.button("💳 Charge", key=f"btn_bcexp_{c['name']}"):
                    modal_card_expense(c['name'])
            with c_btn2:
                if st.button("🔄 Pay Card", key=f"btn_bcpay_{c['name']}"):
                    modal_card_payment(c['name'], c['current_balance'])
                    
            render_card_transactions(c["name"])

# ------------------------------------------
# TAB 1: COMMAND CENTER
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
            amt = st.number_input("Amount ($)", value=None, min_value=0.01, step=1.00, format="%.2f", placeholder="0.00")
            selected_acc = st.selectbox("Card / Account", all_account_names)
            selected_cat = st.selectbox("Category", categories_list)
            vendor = st.text_input("Merchant / Store", placeholder="e.g. Amazon, Shell, Trader Joe's")
            item_desc = st.text_input("Item Description (Optional)", placeholder="e.g. Phone case, Work lunch")
            entry_date = st.date_input("Date", value=datetime.today())
            goal_tag = st.selectbox("Goal Tag", ["General Living", "Baltimore 1st Home", "Emergency Vault", "Business"])
            
            if st.form_submit_button("Record Expense"):
                if amt is None or amt <= 0:
                    st.error("Please enter a valid amount.")
                else:
                    tx_id = f"TX-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    date_str = entry_date.strftime("%Y-%m-%d")
                    row = [tx_id, date_str, selected_acc, "Expense", selected_cat, vendor, float(amt), goal_tag, item_desc, "Mobile App Entry"]
                    try:
                        append_tx_to_sheet(row)
                        st.session_state["success_notification"] = f"Saved ${amt:,.2f} expense to {selected_acc}!"
                        st.rerun()
                    except Exception as err:
                        st.error(f"Error: {err}")

    with tab_inc:
        with st.form("log_income_form", clear_on_submit=True):
            inc_amt = st.number_input("Amount ($)", value=None, min_value=0.01, step=1.00, format="%.2f", placeholder="0.00")
            inc_acc = st.selectbox("Deposit Into", deposit_accounts)
            inc_cat = st.selectbox("Income Source", ["W2 Salary", "Uber Income", "Other Income"])
            payer = st.text_input("Payer / Store", placeholder="e.g. Employer Payroll, Uber Payout")
            memo = st.text_input("Memo (Optional)", placeholder="e.g. Paycheck deposit")
            tx_date = st.date_input("Date", value=datetime.today())
            
            if st.form_submit_button("Record Income"):
                if inc_amt is None or inc_amt <= 0:
                    st.error("Please enter a valid amount.")
                else:
                    gt = "Baltimore 1st Home" if ("4979" in inc_acc or "SECU" in inc_acc) else "General Living"
                    row = [
                        f"TX-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        tx_date.strftime("%Y-%m-%d"),
                        inc_acc,
                        "Income",
                        inc_cat,
                        payer,
                        float(inc_amt),
                        gt,
                        memo,
                        "Mobile App Entry"
                    ]
                    try:
                        append_tx_to_sheet(row)
                        st.session_state["success_notification"] = f"Deposited ${inc_amt:,.2f} into {inc_acc}!"
                        st.rerun()
                    except Exception as err:
                        st.error(f"Error: {err}")

    with tab_pay:
        with st.form("log_payment_form", clear_on_submit=True):
            all_live_cards = live_personal_cc + live_biz_cc
            card_balance_map = {c["name"]: c["current_balance"] for c in all_live_cards}
            all_cc_names = list(card_balance_map.keys())

            target_card = st.selectbox(
                "Credit Card Paid",
                all_cc_names,
                format_func=lambda x: f"{x}  —  ${card_balance_map.get(x, 0.0):,.2f} balance"
            )
            pay_amt = st.number_input("Payment Amount ($)", value=None, min_value=0.01, step=1.00, format="%.2f", placeholder="0.00")
            from_account = st.selectbox("Paid From", deposit_accounts)
            memo = st.text_input("Memo (Optional)", placeholder="e.g. Statement payoff")
            tx_date = st.date_input("Date", value=datetime.today())
            
            if st.form_submit_button("Record CC Payment"):
                if pay_amt is None or pay_amt <= 0:
                    st.error("Please enter a valid payment amount.")
                else:
                    row = [
                        f"TX-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        tx_date.strftime("%Y-%m-%d"),
                        target_card,
                        "CC Payment",
                        "CC Payment",
                        f"Paid from {from_account}",
                        float(pay_amt),
                        "General Living",
                        memo,
                        "Mobile App Entry"
                    ]
                    try:
                        append_tx_to_sheet(row)
                        st.session_state["success_notification"] = f"Recorded ${pay_amt:,.2f} payment to {target_card}!"
                        st.rerun()
                    except Exception as err:
                        st.error(f"Error: {err}")

    with tab_trans:
        with st.form("log_transfer_form", clear_on_submit=True):
            trans_amt = st.number_input("Transfer Amount ($)", value=None, min_value=0.01, step=10.00, format="%.2f", placeholder="0.00")
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                from_trans_acc = st.selectbox("Transfer From", deposit_accounts)
            with col_t2:
                default_to_idx = 1 if len(deposit_accounts) > 1 else 0
                to_trans_acc = st.selectbox("Transfer Into", deposit_accounts, index=default_to_idx)
            memo = st.text_input("Transfer Memo (Optional)", placeholder="e.g. Savings sweep")
            tx_date = st.date_input("Date", value=datetime.today())
            
            if st.form_submit_button("Execute Transfer"):
                if trans_amt is None or trans_amt <= 0:
                    st.error("Please enter a valid transfer amount.")
                elif from_trans_acc == to_trans_acc:
                    st.error("Source and destination must be different.")
                else:
                    now_str = datetime.now().strftime('%Y%m%d%H%M%S')
                    d_str = tx_date.strftime("%Y-%m-%d")
                    memo_str = f" — {memo.strip()}" if memo.strip() else ""
                    gt = "Baltimore 1st Home" if ("4979" in to_trans_acc or "SECU" in to_trans_acc) else "General Living"
                    
                    debit_row = [f"TX-{now_str}-A", d_str, from_trans_acc, "Transfer", "Transfer / Sweep", f"Transfer to {to_trans_acc}", float(trans_amt), gt, f"Outflow to {to_trans_acc}{memo_str}", "Transfer Outflow"]
                    credit_row = [f"TX-{now_str}-B", d_str, to_trans_acc, "Transfer", "Transfer / Sweep", f"Transfer from {from_trans_acc}", float(trans_amt), gt, f"Inflow from {from_trans_acc}{memo_str}", "Transfer Inflow"]
                    try:
                        append_multiple_tx_to_sheet([debit_row, credit_row])
                        st.session_state["success_notification"] = f"Transferred ${trans_amt:,.2f} from {from_trans_acc} to {to_trans_acc}!"
                        st.rerun()
                    except Exception as err:
                        st.error(f"Error: {err}")

# ------------------------------------------
# TAB 2: ANALYTICS & CHARTS
# ------------------------------------------
with tabs[2]:
    st.subheader("📊 Financial Analytics & Trends")
    if "current_analytics_date" not in st.session_state:
        st.session_state.current_analytics_date = date.today()

    ref_date = st.session_state.current_analytics_date
    df_clean = df_tx.copy() if not df_tx.empty else pd.DataFrame()

    week_start = ref_date - timedelta(days=ref_date.weekday())
    week_end = week_start + timedelta(days=6)
    st.markdown(f"### 🗓️ Weekly Analytics ({week_start.strftime('%b %d')} – {week_end.strftime('%b %d')})")
    
    df_week = df_clean[(df_clean["Date_DT"] >= week_start) & (df_clean["Date_DT"] <= week_end)] if not df_clean.empty else pd.DataFrame()
    w_income = df_week[df_week["Type"] == "Income"]["Amount"].sum() if not df_week.empty else 0.0
    w_expense = df_week[df_week["Type"] == "Expense"]["Amount"].sum() if not df_week.empty else 0.0
    
    ws_1, ws_2 = st.columns(2)
    with ws_1:
        st.markdown(f"""<div class="stat-box"><div style="font-size:10px; color:#94A3B8;">INCOME</div><div style="font-size:16px; font-weight:800; color:#34D399;">+${w_income:,.2f}</div></div>""", unsafe_allow_html=True)
    with ws_2:
        st.markdown(f"""<div class="stat-box"><div style="font-size:10px; color:#94A3B8;">EXPENSES</div><div style="font-size:16px; font-weight:800; color:#F87171;">-${w_expense:,.2f}</div></div>""", unsafe_allow_html=True)

# ------------------------------------------
# TAB 3: HOME GOAL
# ------------------------------------------
with tabs[3]:
    st.subheader("🏠 Baltimore Home Purchase Target")
    st.progress(goal_progress)
    st.caption(f"**${total_cash:,.2f}** saved of **${HOME_GOAL:,.2f}** goal ({(goal_progress*100):.1f}%)[cite: 1]")

# ------------------------------------------
# TAB 4: AI ADVISOR
# ------------------------------------------
with tabs[4]:
    st.subheader("💬 AI Financial Advisor")
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [{"role": "assistant", "content": "Ask me anything about your finances or home goal!"}]
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    if user_prompt := st.chat_input("Ask a question..."):
        st.session_state.chat_messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)

# ==========================================
# 7. ASYNC POPULATE SUMMARY PLACEHOLDER
# ==========================================
unpaid_stmt_list = [f"{c['name']} (${c['stmt_due']:.2f})" for c in live_personal_cc if c.get('stmt_due', 0) > 0.01]
unpaid_stmt_str = ", ".join(unpaid_stmt_list)

ai_insight_text = fetch_ai_insights_cached(
    net_liquid_cash, total_cash, personal_cc_debt, biz_cc_debt, personal_utilization, azeo_card_name, unpaid_stmt_str
)
ai_placeholder.info(ai_insight_text)
