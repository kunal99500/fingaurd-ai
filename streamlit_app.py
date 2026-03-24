# frontend/streamlit_app.py
"""
FinGuard AI — Smart Personal Finance Manager
Full-featured Streamlit frontend for FastAPI backend
"""

import streamlit as st
import requests
import json
import os
import time
import pandas as pd
from datetime import datetime
from typing import Optional, Dict

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
TOKEN_FILE = "token.json"

st.set_page_config(page_title="💰 FinGuard AI", page_icon="💸", layout="wide")

# ─────────────────────────────────────────
# GLOBAL STYLING
# ─────────────────────────────────────────
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] > div:first-child {
    background: linear-gradient(-45deg, #0f0c29, #302b63, #24243e, #1a1a2e);
    background-size: 400% 400%;
    animation: gradientShift 14s ease infinite;
}
@keyframes gradientShift {
    0%{background-position:0% 50%} 50%{background-position:100% 50%} 100%{background-position:0% 50%}
}
.glass-box {
    background: rgba(255,255,255,0.07);
    backdrop-filter: blur(14px);
    border-radius: 18px;
    padding: 1.8rem;
    box-shadow: 0 6px 24px rgba(0,0,0,0.35);
    color: white;
    margin-bottom: 1rem;
}
.metric-card {
    background: rgba(255,255,255,0.1);
    border-radius: 14px;
    padding: 1.2rem;
    text-align: center;
    color: white;
}
.metric-card h2 { font-size: 2rem; margin: 0; }
.metric-card p  { font-size: 0.85rem; opacity: 0.75; margin: 0; }
.tip-card {
    background: rgba(0,198,255,0.1);
    border-left: 4px solid #00c6ff;
    border-radius: 8px;
    padding: 0.8rem 1rem;
    margin: 0.4rem 0;
    color: white;
    font-size: 0.9rem;
}
.news-card {
    background: rgba(255,255,255,0.06);
    border-radius: 10px;
    padding: 1rem;
    margin: 0.5rem 0;
    color: white;
}
.news-card a { color: #00c6ff; text-decoration: none; }
.stButton > button {
    background: linear-gradient(90deg, #00c6ff, #0072ff);
    color: white; border-radius: 10px; font-weight: 700;
    padding: 10px 28px; border: none; transition: all 0.3s;
}
.stButton > button:hover { transform: scale(1.05); box-shadow: 0 0 20px rgba(0,198,255,0.6); }
.stTextInput input, .stNumberInput input, .stSelectbox select {
    background: rgba(255,255,255,0.1) !important;
    color: white !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    border-radius: 8px !important;
}
label, .stRadio label, .stCheckbox label { color: white !important; }
[data-testid="stMetricValue"] { color: white !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# TOKEN HELPERS
# ─────────────────────────────────────────
def save_token(data): 
    with open(TOKEN_FILE, "w") as f: json.dump(data, f)

def load_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f: return json.load(f)
    return None

def clear_token():
    if os.path.exists(TOKEN_FILE): os.remove(TOKEN_FILE)


# ─────────────────────────────────────────
# API HELPER
# ─────────────────────────────────────────
def api(endpoint, payload=None, method="POST", params=None):
    token_data = load_token()
    headers = {}
    if token_data and "access_token" in token_data:
        headers["Authorization"] = f"Bearer {token_data['access_token']}"
    try:
        url = f"{BACKEND_URL}{endpoint}"
        if method == "POST":   return requests.post(url, json=payload or {}, headers=headers, timeout=8)
        elif method == "GET":  return requests.get(url, headers=headers, params=params or {}, timeout=8)
        elif method == "DELETE": return requests.delete(url, headers=headers, timeout=8)
    except Exception as e:
        st.error(f"❌ Backend not reachable: {e}")
        return None

def get_user_id():
    t = load_token()
    return t.get("user_id") if t else None


# ─────────────────────────────────────────
# AUTH PAGES
# ─────────────────────────────────────────
def landing_page():
    st.markdown("""
    <div style="text-align:center; margin-top:6%; color:white;">
        <h1 style="font-size:52px; font-weight:800;">💸 FinGuard AI</h1>
        <p style="font-size:1.2rem; opacity:0.8;">AI-powered budgeting • Daily limit control • Investment insights</p>
        <br>
    </div>
    """, unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔑 Sign In", use_container_width=True):
                st.session_state.page = "login"; st.rerun()
        with col2:
            if st.button("🆕 Sign Up", use_container_width=True):
                st.session_state.page = "choose_signup"; st.rerun()
    st.markdown("<div style='text-align:center;color:rgba(255,255,255,0.4);margin-top:50px'>© FinGuard AI — by Kunal Malik</div>", unsafe_allow_html=True)


def signup_choice_page():
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
        st.header("Choose Sign-Up Method")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📧 Email", use_container_width=True):
                st.session_state.signup_method = "Email"; st.session_state.page = "signup"; st.rerun()
        with c2:
            if st.button("📱 Phone", use_container_width=True):
                st.session_state.signup_method = "Phone"; st.session_state.page = "signup"; st.rerun()
        if st.button("⬅️ Back"): st.session_state.page = "welcome"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


def signup_page():
    method = st.session_state.get("signup_method", "Email")
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
        st.header(f"Create Account via {method}")
        email = st.text_input("Email") if method == "Email" else ""
        phone = st.text_input("Phone (+91...)") if method == "Phone" else ""
        password = st.text_input("Password", type="password")
        if st.button("Create Account", use_container_width=True):
            payload = {"email": email, "phone": phone, "password": password, "method": method.lower()}
            res = api("/auth/signup", payload)
            if res and res.status_code == 200:
                st.success("✅ OTP sent! Please verify.")
                st.session_state.pending_contact = email if method == "Email" else phone
                st.session_state.page = "verify"; st.rerun()
            else:
                st.error(f"❌ {res.json().get('detail', 'Signup failed') if res else 'No response'}")
        if st.button("⬅️ Back"): st.session_state.page = "choose_signup"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


def verify_otp_page():
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
        st.header("🔒 Verify OTP")
        contact = st.session_state.get("pending_contact", "")
        st.write(f"OTP sent to: **{contact}**")
        otp = st.text_input("Enter OTP")
        if st.button("Verify", use_container_width=True):
            res = api("/auth/verify-otp", {"contact": contact, "otp": otp})
            if res and res.status_code == 200:
                st.success("✅ Verified! You can now log in.")
                time.sleep(1); st.session_state.page = "login"; st.rerun()
            else:
                st.error("❌ Invalid or expired OTP.")
        if st.button("⬅️ Back"): st.session_state.page = "signup"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


def login_page():
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
        st.header("Sign In")
        login_method = st.radio("Login via", ["Email", "Phone"], horizontal=True)
        contact = st.text_input("Email" if login_method == "Email" else "Phone")
        password = st.text_input("Password", type="password")
        remember = st.checkbox("Remember Me")
        if st.button("Login", use_container_width=True):
            payload = {
                "email": contact if login_method == "Email" else "",
                "phone": contact if login_method == "Phone" else "",
                "password": password
            }
            res = api("/auth/login", payload)
            if res and res.status_code == 200:
                data = res.json()
                token_data = {"access_token": data["access_token"], "user_id": data["user_id"], "contact": contact}
                if remember: save_token(token_data)
                st.session_state.logged_in = True
                st.session_state.user_id = data["user_id"]
                st.session_state.token = data["access_token"]
                st.success("✅ Login successful!")
                time.sleep(0.5); st.rerun()
            else:
                st.error("❌ Invalid credentials or unverified account.")
        if st.button("⬅️ Back"): st.session_state.page = "welcome"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────
def dashboard_page():
    user_id = st.session_state.get("user_id") or get_user_id()

    # ── Sidebar Navigation ──
    with st.sidebar:
        st.markdown("<h2 style='color:white'>💸 FinGuard AI</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:rgba(255,255,255,0.6)'>User ID: {user_id}</p>", unsafe_allow_html=True)
        st.markdown("---")
        page = st.radio("Navigate", [
            "📊 Dashboard",
            "➕ Add Transaction",
            "📜 Transaction History",
            "⚙️ Budget Settings",
            "🤖 AI Insights",
            "💬 AI Chat Advisor",
            "📈 Investment Tips",
            "📰 Market News",
            "🚨 Anomaly Report",
            "📧 Gmail Settings",
        ])
        st.markdown("---")
        st.markdown("---")
        st.markdown("**📧 Gmail Auto-Sync**")
        gmail_status = api("/gmail/status", method="GET")
        if gmail_status and gmail_status.status_code == 200:
            gs = gmail_status.json()
            if gs.get("gmail_connected"):
                st.caption(f"✅ {gs.get('gmail_user')}")
                if gs.get("auto_sync_active"):
                    st.caption("🔁 Auto-sync active")
                if st.button("🔄 Sync Now", use_container_width=True):
                    res = api("/gmail/sync", method="POST")
                    if res and res.status_code == 200:
                        count = res.json().get("transactions_found", 0)
                        st.success(f"Found {count} new transaction(s)!" if count else "No new transactions.")
                    else:
                        err = res.json().get("detail", "Sync failed") if res else "No response"
                        st.error(f"❌ {err}")
            else:
                st.caption("⚠️ Gmail not connected")
                if st.button("🔗 Connect Gmail", use_container_width=True):
                    st.session_state.page_override = "gmail_connect"
                    st.rerun()

        st.markdown("---")
        if st.button("🚪 Logout"):
            clear_token()
            st.session_state.logged_in = False
            st.session_state.page = "welcome"
            st.rerun()

    # ════════════════════════════════════
    # PAGE: DASHBOARD OVERVIEW
    # ════════════════════════════════════
    if page == "📊 Dashboard":
        st.title("📊 Dashboard Overview")

        # Fetch budget report
        report_res = api("/budget/threshold_report", method="GET", params={"user_id": user_id})
        if report_res and report_res.status_code == 200:
            r = report_res.json()
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(f"<div class='metric-card'><p>Monthly Budget</p><h2>₹{r.get('Monthly_Limit', 0):,.0f}</h2></div>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"<div class='metric-card'><p>Spent This Month</p><h2>₹{r.get('Current_Spent', 0):,.0f}</h2></div>", unsafe_allow_html=True)
            with c3:
                remaining = r.get('Remaining_Balance', 0)
                color = "#ff4b4b" if remaining < 0 else "#00c6ff"
                st.markdown(f"<div class='metric-card'><p>Remaining</p><h2 style='color:{color}'>₹{remaining:,.0f}</h2></div>", unsafe_allow_html=True)
            with c4:
                daily_rem = r.get('Daily_Remaining')
                if daily_rem is not None:
                    st.markdown(f"<div class='metric-card'><p>Daily Remaining</p><h2>₹{daily_rem:,.0f}</h2></div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='metric-card'><p>Today Spent</p><h2>₹{r.get('Today_Spent', 0):,.0f}</h2></div>", unsafe_allow_html=True)

            if r.get("Limit_Exceeded"):
                st.error(f"🚨 {r.get('Suggested_Action')}")
            elif r.get("Daily_Limit_Exceeded"):
                st.warning(f"⚠️ {r.get('Suggested_Action')}")
            else:
                st.success(f"✅ {r.get('Suggested_Action')}")
        else:
            st.info("💡 Set your budget in **⚙️ Budget Settings** to unlock your spending overview.")

        # Recent transactions
        st.markdown("### 📜 Recent Transactions")
        txn_res = api("/transaction/", method="GET", params={"user_id": user_id})
        if txn_res and txn_res.status_code == 200:
            txns = txn_res.json().get("transactions", [])
            if txns:
                df = pd.DataFrame(txns[-10:])
                cols = ["Date", "Merchant", "Amount", "Category", "Type_of_Payment", "Notes"]
                df_show = df[[c for c in cols if c in df.columns]]
                st.dataframe(df_show, use_container_width=True)

                # Category bar chart
                if "Category" in df.columns and "Amount" in df.columns:
                    st.markdown("### 📈 Spending by Category")
                    cat_df = df[df["Amount"] < 0].copy()
                    cat_df["Amount"] = cat_df["Amount"].abs()
                    cat_summary = cat_df.groupby("Category")["Amount"].sum().reset_index()
                    st.bar_chart(cat_summary.set_index("Category"))
            else:
                st.info("No transactions yet. Add one in ➕ Add Transaction.")
        else:
            st.warning("Could not fetch transactions.")

    # ════════════════════════════════════
    # PAGE: ADD TRANSACTION
    # ════════════════════════════════════
    elif page == "➕ Add Transaction":
        st.title("➕ Add Transaction")
        st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            merchant = st.text_input("Merchant / Shop Name")
            amount = st.number_input("Amount (₹)", min_value=0.01, step=10.0)
            category = st.selectbox("Category", ["Food", "Shopping", "Bills", "Travel", "Entertainment", "Healthcare", "Education", "Others"])
        with col2:
            date = st.date_input("Date", datetime.now())
            payment_type = st.selectbox("Payment Type", ["UPI", "Card", "Cash", "NetBanking"])
            description = st.text_input("Description (optional)")

        if st.button("💾 Add Transaction", use_container_width=True):
            if merchant and amount > 0:
                payload = [{
                    "Id": datetime.now().timestamp(),
                    "User_Id": user_id,
                    "Date": str(date),
                    "Time": datetime.now().strftime("%H:%M:%S"),
                    "Description": description or merchant,
                    "Merchant": merchant,
                    "Amount": -abs(amount),
                    "Currency": "INR",
                    "Type_of_Payment": payment_type,
                    "Category": category,
                    "Status_of_Transaction": "Completed"
                }]
                res = api("/transaction/", payload)
                if res and res.status_code == 200:
                    result = res.json()
                    txns = result.get("transactions", [])
                    if txns and txns[0].get("Blocked"):
                        st.error(f"🚫 {txns[0].get('Notes', 'Transaction blocked — limit exceeded!')}")
                    elif txns and txns[0].get("Over_Threshold"):
                        st.warning(f"⚠️ Added with warning: {txns[0].get('Notes')}")
                    else:
                        st.success("✅ Transaction added!")
                else:
                    st.error("❌ Failed to add transaction.")
            else:
                st.warning("Please fill in Merchant and Amount.")

        st.markdown("</div>", unsafe_allow_html=True)

        # SMS/UPI Sync
        st.markdown("---")
        st.markdown("### 📱 Sync from UPI / SMS Message")
        st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
        sms_msg = st.text_area("Paste UPI/bank SMS here", placeholder="₹500 spent on Zomato via UPI txn ID 123456 on 15 Jan 2025")
        if st.button("🔄 Sync Transaction"):
            if sms_msg:
                res = api("/payment/sync", method="POST", payload=None)
                # Send as query param
                try:
                    token_data = load_token()
                    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
                    r = requests.post(f"{BACKEND_URL}/payment/sync", params={"message": sms_msg}, headers=headers, timeout=8)
                    if r.status_code == 200:
                        st.success(f"✅ {r.json().get('message')}")
                    elif r.status_code == 403:
                        st.error(f"🚫 {r.json().get('detail')}")
                    else:
                        st.error(f"❌ {r.json().get('detail', 'Failed')}")
                except Exception as e:
                    st.error(f"❌ {e}")
        st.markdown("</div>", unsafe_allow_html=True)

    # ════════════════════════════════════
    # PAGE: TRANSACTION HISTORY
    # ════════════════════════════════════
    elif page == "📜 Transaction History":
        st.title("📜 Transaction History")
        res = api("/transaction/", method="GET", params={"user_id": user_id})
        if res and res.status_code == 200:
            txns = res.json().get("transactions", [])
            if txns:
                df = pd.DataFrame(txns)
                # Filter
                categories = ["All"] + sorted(df["Category"].dropna().unique().tolist())
                selected_cat = st.selectbox("Filter by Category", categories)
                if selected_cat != "All":
                    df = df[df["Category"] == selected_cat]

                df_show = df[["Date", "Merchant", "Amount", "Category", "Sub_Category", "Type_of_Payment", "Notes", "Blocked"]].copy()
                df_show["Amount"] = df_show["Amount"].apply(lambda x: f"₹{abs(x):,.2f}")
                st.dataframe(df_show, use_container_width=True)
                st.markdown(f"**Total transactions: {len(df)}**")
            else:
                st.info("No transactions found.")
        else:
            st.warning("Could not fetch transactions.")

    # ════════════════════════════════════
    # PAGE: BUDGET SETTINGS
    # ════════════════════════════════════
    elif page == "⚙️ Budget Settings":
        st.title("⚙️ Budget & Limit Settings")
        st.markdown("<div class='glass-box'>", unsafe_allow_html=True)

        # Load existing settings
        existing = api("/budget/settings/" + str(user_id), method="GET")
        defaults = {}
        if existing and existing.status_code == 200:
            defaults = existing.json()
            st.success("✅ Current settings loaded")

        monthly = st.number_input("Monthly Budget (₹)", min_value=0.0, step=500.0,
                                   value=float(defaults.get("Monthly_Limit") or 0))
        daily = st.number_input("Daily Spending Limit (₹) — 0 = no limit", min_value=0.0, step=100.0,
                                 value=float(defaults.get("Daily_Limit") or 0))
        block = st.checkbox("🚫 Block transactions that exceed limits",
                             value=bool(defaults.get("Block_Transactions", False)))

        st.markdown("#### Category Limits (optional)")
        food_lim = st.number_input("Food limit/month (₹)", min_value=0.0, step=100.0)
        shop_lim = st.number_input("Shopping limit/month (₹)", min_value=0.0, step=100.0)
        ent_lim = st.number_input("Entertainment limit/month (₹)", min_value=0.0, step=100.0)

        if st.button("💾 Save Settings", use_container_width=True):
            cat_limits = {}
            if food_lim > 0: cat_limits["Food"] = food_lim
            if shop_lim > 0: cat_limits["Shopping"] = shop_lim
            if ent_lim > 0: cat_limits["Entertainment"] = ent_lim

            payload = {
                "User_id": user_id,
                "Monthly_Limit": monthly if monthly > 0 else None,
                "Daily_Limit": daily if daily > 0 else None,
                "Block_Transactions": block,
                "Category_Limits": cat_limits if cat_limits else None
            }
            res = api("/budget/set_settings", payload)
            if res and res.status_code == 200:
                st.success("✅ Settings saved! Your limits are now active.")
            else:
                st.error(f"❌ Failed to save settings.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ════════════════════════════════════
    # PAGE: AI INSIGHTS
    # ════════════════════════════════════
    elif page == "🤖 AI Insights":
        st.title("🤖 AI Spending Insights")

        res = api("/insights/ai_insights", method="GET", params={"user_id": user_id})
        if res and res.status_code == 200:
            data = res.json()

            # Recommendations
            st.markdown("### 💡 Recommendations")
            for rec in data.get("recommendations", []):
                st.markdown(f"<div class='tip-card'>{rec}</div>", unsafe_allow_html=True)

            # Daily prediction
            st.markdown("### 📅 Budget Breakdown")
            dp = data.get("daily_prediction", {})
            if "error" not in dp:
                c1, c2, c3 = st.columns(3)
                c1.metric("Days Left in Month", dp.get("Days_Left_In_Month", "—"))
                c2.metric("Suggested Daily Allowance", f"₹{dp.get('Suggested_Daily_Allowance', 0):,.0f}")
                c3.metric("Today Spent", f"₹{dp.get('Today_Spent', 0):,.0f}")

                if dp.get("Daily_Limit"):
                    c4, c5 = st.columns(2)
                    c4.metric("Daily Limit", f"₹{dp['Daily_Limit']:,.0f}")
                    c5.metric("Daily Remaining", f"₹{dp.get('Daily_Remaining', 0):,.0f}")

            # Trend analysis
            st.markdown("### 📈 Spending Trend Forecast")
            ta = data.get("trend_analysis", {})
            if "predicted_next_week" in ta:
                st.info(ta.get("message", ""))
                forecast_df = pd.DataFrame(ta["predicted_next_week"])
                st.line_chart(forecast_df.set_index("date"))
            else:
                st.info(ta.get("message", "Not enough data yet for trend analysis."))

        else:
            st.warning("Could not fetch AI insights. Make sure you have transactions and budget set.")

    # ════════════════════════════════════
    # PAGE: INVESTMENT TIPS
    # ════════════════════════════════════
    elif page == "📈 Investment Tips":
        st.title("📈 Personalized Investment Tips")

        res = api("/insights/investment_tips", method="GET", params={"user_id": user_id})
        if res and res.status_code == 200:
            data = res.json()
            savings = data.get("monthly_savings", 0)

            if savings > 0:
                st.success(f"🎉 You've saved **₹{savings:,.2f}** this month! Here's how to grow it:")
            elif savings == 0:
                st.info("Start tracking expenses to get personalized investment advice.")
            else:
                st.error(f"⚠️ You're ₹{abs(savings):,.2f} over budget. Focus on saving first.")

            st.markdown("### 💡 Your Investment Recommendations")
            for tip in data.get("tips", []):
                st.markdown(f"<div class='tip-card'>{tip}</div>", unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("### 🔗 Quick Start Resources")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**📱 Invest via Apps**\n- [Groww](https://groww.in)\n- [Zerodha](https://zerodha.com)\n- [INDMoney](https://indmoney.com)")
            with col2:
                st.markdown("**📚 Learn Basics**\n- [NSE India](https://nseindia.com)\n- [SEBI Investor](https://investor.sebi.gov.in)\n- [ET Money](https://etmoney.com)")
            with col3:
                st.markdown("**🏦 Safe Options**\n- PPF Account (7.1% p.a.)\n- FD in Small Finance Banks\n- Sovereign Gold Bonds")
        else:
            st.warning("Could not load investment tips.")

    # ════════════════════════════════════
    # PAGE: MARKET NEWS
    # ════════════════════════════════════
    elif page == "📰 Market News":
        st.title("📰 Market & Finance News")

        query = st.text_input("Search topic", value="Indian stock market NSE BSE Nifty")
        if st.button("🔍 Fetch Latest News") or True:
            with st.spinner("Fetching latest market news..."):
                res = api("/insights/market_news", method="GET", params={"query": query})
                if res and res.status_code == 200:
                    data = res.json()
                    if data.get("status") == "mock":
                        st.info(f"ℹ️ {data.get('note')}")
                    articles = data.get("articles", [])
                    if articles:
                        for article in articles:
                            st.markdown(f"""
                            <div class='news-card'>
                                <b>{article.get('title', 'No title')}</b><br>
                                <small>📰 {article.get('source', '')} &nbsp;|&nbsp; 📅 {article.get('published', '')}</small><br>
                                <p style='opacity:0.8;font-size:0.88rem'>{article.get('summary') or ''}</p>
                                <a href='{article.get('url', '#')}' target='_blank'>Read more →</a>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("No news articles found for this query.")
                else:
                    st.warning("Could not fetch news.")

    # ════════════════════════════════════
    # PAGE: AI CHAT ADVISOR
    # ════════════════════════════════════
    elif page == "💬 AI Chat Advisor":
        st.title("💬 FinGuard AI Agent")
        st.markdown("Powered by **LangGraph + Groq** — Ask anything, add transactions, check budget, get investment tips!")

        # Init session state
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        if "agent_session_id" not in st.session_state:
            import uuid
            st.session_state.agent_session_id = f"session-{user_id}-{uuid.uuid4().hex[:8]}"

        session_id = st.session_state.agent_session_id
        st.caption(f"Session: `{session_id}` — memory persists across logins")

        # Display conversation
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("intent"):
                    st.caption(f"🧠 Intent: `{msg['intent']}`")

        # Quick starter prompts
        if not st.session_state.chat_history:
            st.markdown("**💡 Try asking:**")
            cols = st.columns(2)
            starters = [
                "How am I doing this month?",
                "I spent ₹250 on Zomato via UPI",
                "Can I afford to spend ₹500 today?",
                "Give me investment tips",
                "Show market news",
                "Where am I spending the most?",
            ]
            for i, starter in enumerate(starters):
                with cols[i % 2]:
                    if st.button(starter, key=f"starter_{i}"):
                        st.session_state.pending_chat = starter
                        st.rerun()

        def call_agent(message):
            payload = {"message": message, "session_id": session_id}
            res = api("/agent/run", payload)
            if res and res.status_code == 200:
                data = res.json()
                return data.get("response", "No response"), data.get("intent", ""), data.get("blocked", False)
            return "❌ Could not reach the agent. Make sure the backend is running.", "", False

        # Handle starter button clicks
        if "pending_chat" in st.session_state:
            user_msg = st.session_state.pop("pending_chat")
            with st.chat_message("user"):
                st.markdown(user_msg)
            with st.chat_message("assistant"):
                with st.spinner("Agent thinking..."):
                    reply, intent, blocked = call_agent(user_msg)
                    st.markdown(reply)
                    if intent: st.caption(f"🧠 Intent: `{intent}`")
                    if blocked: st.error("🚫 Transaction was blocked by budget guard!")
            st.session_state.chat_history.append({"role": "user", "content": user_msg})
            st.session_state.chat_history.append({"role": "assistant", "content": reply, "intent": intent})
            st.rerun()

        # Chat input
        user_input = st.chat_input("Ask the agent — add a transaction, check budget, get tips...")
        if user_input:
            with st.chat_message("user"):
                st.markdown(user_input)
            with st.chat_message("assistant"):
                with st.spinner("Agent thinking..."):
                    reply, intent, blocked = call_agent(user_input)
                    res = None  # suppress old code below
                    if res and res.status_code == 200:
                        pass
                    if res and res.status_code == 200:
                        reply = res.json().get("reply", "Sorry, I couldn't get a response.")
                    else:
                        reply = "❌ Could not reach AI advisor. Make sure the backend is running."
                    st.markdown(reply)

            st.session_state.chat_history.append({"role": "user", "content": user_input})
            st.session_state.chat_history.append({"role": "assistant", "content": reply})

        if st.session_state.chat_history:
            if st.button("🗑️ Clear Chat"):
                st.session_state.chat_history = []
                st.rerun()

    # ════════════════════════════════════
    # PAGE: ANOMALY REPORT
    # ════════════════════════════════════
    elif page == "🚨 Anomaly Report":
        st.title("🚨 Spending Anomaly Detection")
        res = api("/anomaly/report", method="GET")
        if res and res.status_code == 200:
            report = res.json()
            c1, c2 = st.columns(2)
            c1.metric("Total Transactions", report.get("Total_Transaction", 0))
            c2.metric("Anomalies Found", report.get("Anomalies_found", 0))

            anomalies = report.get("Anomalies", [])
            if anomalies:
                st.markdown("### ⚠️ Flagged Transactions")
                for a in anomalies:
                    severity = a.get("Severity_Level", "Medium")
                    color = "#ff4b4b" if severity == "High" else "#ffaa00"
                    st.markdown(f"""
                    <div class='glass-box' style='border-left: 4px solid {color}'>
                        <b>🔴 {a.get('Anomaly_Type')}</b> — Severity: {severity}<br>
                        <small>{a.get('Reason')}</small><br>
                        <i>💡 {a.get('Suggested_Action')}</i>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("✅ No anomalies detected. Your spending looks normal!")
        else:
            st.warning("Could not fetch anomaly report.")

    # ════════════════════════════════════
    # PAGE: GMAIL SETTINGS
    # ════════════════════════════════════
    elif page == "📧 Gmail Settings" or st.session_state.get("page_override") == "gmail_connect":
        st.session_state.pop("page_override", None)
        st.title("📧 Connect Your Gmail")
        st.markdown("Connect your Gmail to **automatically detect bank and UPI transactions** from your emails.")

        st.info("FinGuard reads only transaction emails from your bank. Your emails stay private.")

        st.markdown("### Step 1 — Enable Gmail App Password")
        st.markdown("""
1. Go to [myaccount.google.com/security](https://myaccount.google.com/security)
2. Enable **2-Step Verification**
3. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
4. Select **Mail** → **Windows** → **Generate**
5. Copy the 16-character password
        """)

        st.markdown("### Step 2 — Enter your credentials")
        st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
        gmail_user = st.text_input("Gmail address", placeholder="yourname@gmail.com")
        gmail_pass = st.text_input("Gmail App Password (16 chars)", type="password", placeholder="xxxx xxxx xxxx xxxx")

        if st.button("🔗 Connect Gmail", use_container_width=True):
            if gmail_user and gmail_pass:
                res = api("/gmail/connect", {"gmail_user": gmail_user, "gmail_app_password": gmail_pass})
                if res and res.status_code == 200:
                    st.success(f"✅ Gmail connected! Your transactions will now be auto-detected.")
                    # Trigger first sync
                    sync_res = api("/gmail/sync", method="POST")
                    if sync_res and sync_res.status_code == 200:
                        count = sync_res.json().get("transactions_found", 0)
                        if count:
                            st.success(f"🎉 Found {count} transaction(s) from your emails!")
                else:
                    st.error(f"❌ {res.json().get('detail', 'Connection failed') if res else 'No response'}")
            else:
                st.warning("Please fill in both fields.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("### Supported banks & apps")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("✅ SBI")
            st.markdown("✅ HDFC")
            st.markdown("✅ ICICI")
        with col2:
            st.markdown("✅ Axis")
            st.markdown("✅ Kotak")
            st.markdown("✅ PhonePe")
        with col3:
            st.markdown("✅ Google Pay")
            st.markdown("✅ Paytm")
            st.markdown("✅ Amazon Pay")

        st.markdown("<div style='text-align:center;margin-top:30px;color:rgba(255,255,255,0.4)'>© FinGuard AI — by Kunal Malik</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────
# APP ROUTER
# ─────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    token = load_token()
    if token and "access_token" in token:
        st.session_state.logged_in = True
        st.session_state.user_id = token.get("user_id")

if "page" not in st.session_state:
    st.session_state.page = "welcome"

if st.session_state.logged_in:
    dashboard_page()
else:
    page = st.session_state.page
    if page == "welcome":       landing_page()
    elif page == "choose_signup": signup_choice_page()
    elif page == "signup":      signup_page()
    elif page == "verify":      verify_otp_page()
    elif page == "login":       login_page()
    else:                       landing_page()