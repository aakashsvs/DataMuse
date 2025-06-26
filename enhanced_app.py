import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import datetime
import os
from enhanced_query_agent import QueryAgent
from enhanced_db_loader import ensure_db_and_users
from utils.utils_auth import check_user_role

# --- CONFIG ---
DB_PATH = 'db/bank_exchange.db'
DATA_DICT_PATH = 'data/data_dictionary.xlsx'
ROLE_ACCESS_PATH = 'data/role_access.xlsx'

# --- UTILS ---
def load_data_dictionary():
    if os.path.exists(DATA_DICT_PATH):
        return pd.read_excel(DATA_DICT_PATH)
    return pd.DataFrame()

def load_role_access():
    if os.path.exists(ROLE_ACCESS_PATH):
        return pd.read_excel(ROLE_ACCESS_PATH, index_col=0)
    return pd.DataFrame()

def get_allowed_tables(role, role_access):
    if role_access is not None and role in role_access.index:
        allowed = role_access.loc[role]
        # Get tables with non-empty access
        return [table for table, access in allowed.items() if str(access).strip()]
    return []

def get_allowed_columns(role, table, role_access, table_cols):
    if role_access is not None and role in role_access.index:
        allowed = role_access.loc[role]
        val = allowed.get(table, '')
        if isinstance(val, str):
            if val.strip().upper() == 'ALL':
                return table_cols.get(table, [])
            elif val.strip():
                return [c.strip() for c in val.split(',') if c.strip()]
    return []

def get_table_columns():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';").fetchall()
    table_cols = {}
    for (table,) in tables:
        columns = cursor.execute(f'PRAGMA table_info({table})').fetchall()
        table_cols[table] = [col[1] for col in columns]
    conn.close()
    return table_cols

def get_db_status():
    if not os.path.exists(DB_PATH):
        return False, {}, 0
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [row[0] for row in cursor.fetchall()]
    table_info = {}
    total_rows = 0
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            table_info[table] = count
            total_rows += count
        except:
            table_info[table] = 0
    conn.close()
    return True, table_info, total_rows

def hash_password(password):
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate(username, password):
    # Simple authentication for demo
    if username.lower() in ['teller', 'manager', 'auditor', 'it', 'customer service']:
        if password == f"{username.lower()}123":
            return username.title()
    return None

# --- SESSION STATE ---
def init_session_state():
    defaults = {
        "authenticated": False,
        "username": None,
        "role": None,
        "history": [],
        "db_connected": False,
        "system_ready": False,
        "data_dict": None,
        "role_access": None,
        "table_cols": None,
        "query_agent": None,
        "metrics": {},
        "current_query": ""
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# --- CSS ---
st.markdown("""
<style>
    .main-header {background: linear-gradient(90deg, #1e3c72, #2a5298); padding: 1rem; border-radius: 10px; color: white; text-align: center; margin-bottom: 2rem;}
    .chat-message {padding: 1rem; border-radius: 10px; margin: 0.5rem 0;}
    .user-message {background-color: #e3f2fd; border-left: 4px solid #2196f3;}
    .assistant-message {background-color: #f3e5f5; border-left: 4px solid #9c27b0;}
    .sql-code {background-color: #f8f8f8; border: 1px solid #ddd; border-radius: 5px; padding: 1rem; font-family: 'Courier New', monospace;}
    .metric-card {background: linear-gradient(90deg, #2193b0, #6dd5ed); color: #fff; border-radius: 10px; padding: 1rem; text-align: center; margin-bottom: 1rem;}
    .sidebar-section {margin-bottom: 2rem;}
    .stButton>button {width: 100%;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- APP START ---
st.set_page_config(page_title="RAG SQL Chatbot", layout="wide", initial_sidebar_state="expanded", page_icon="🤖")
init_session_state()

# --- SYSTEM INIT ---
if not st.session_state.system_ready:
    ensure_db_and_users(DB_PATH)
    st.session_state.data_dict = load_data_dictionary()
    st.session_state.role_access = load_role_access()
    st.session_state.table_cols = get_table_columns()
    st.session_state.query_agent = QueryAgent(DB_PATH, st.session_state.data_dict, st.session_state.role_access)
    st.session_state.system_ready = True
    st.session_state.db_connected, st.session_state.metrics['table_info'], st.session_state.metrics['total_rows'] = get_db_status()

# --- LOGIN ---
if not st.session_state.authenticated:
    st.markdown('<div class="main-header"><h1>🤖 RAG SQL Chatbot</h1><p>Business-Grade Chatbot with Role-Based Access</p></div>', unsafe_allow_html=True)
    with st.form("login_form", clear_on_submit=True):
        st.subheader("🔐 Login")
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submitted = st.form_submit_button("Login")
        if submitted:
            role = authenticate(username, password)
            if role:
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.role = role
                st.success(f"Welcome, {username}!")
                st.rerun()
            else:
                st.error("Invalid credentials!")
    st.info("Demo: Use roles as username (teller, manager, auditor, it, customer service) and password as role123 (e.g., teller123)")
    st.stop()

# --- METRICS CARDS ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f'<div class="metric-card">DB: <b>{"Connected" if st.session_state.db_connected else "Disconnected"}</b></div>', unsafe_allow_html=True)
with col2:
    allowed_tables = get_allowed_tables(st.session_state.role, st.session_state.role_access)
    st.markdown(f'<div class="metric-card">Allowed Tables: <b>{len(allowed_tables)}</b></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-card">Queries: <b>{len(st.session_state.history)}</b></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="metric-card">Role: <b>{st.session_state.role}</b></div>', unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header(f"👋 {st.session_state.username.title()}")
    st.write(f"**Role:** {st.session_state.role}")
    st.write(f"**DB:** {'Connected' if st.session_state.db_connected else 'Disconnected'}")
    st.divider()
    st.subheader("📋 Tables")
    allowed_tables = get_allowed_tables(st.session_state.role, st.session_state.role_access)
    for table in allowed_tables:
        st.write(f"• {table}")
    st.divider()
    st.subheader("💡 Sample Queries")
    for q in ["Show me total sales for this month", "List top 10 customers by revenue", "Count all customers", "Show account balances by type", "Show recent transactions", "Show loan status summary"]:
        if st.button(q, key=f"sample_{q}"):
            st.session_state.current_query = q
            st.rerun()
    st.divider()
    st.subheader("🕑 History")
    for msg in st.session_state.history[-5:]:
        st.write(f"{msg['role'].title()}: {msg['content'][:40]}{'...' if len(msg['content'])>40 else ''}")
    if st.button("Clear History"):
        st.session_state.history = []
        st.rerun()
    if st.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# --- CHAT INTERFACE ---
st.markdown('<div class="main-header"><h2>💬 Chat with Your Database</h2></div>', unsafe_allow_html=True)

# --- CHAT HISTORY ---
for i, message in enumerate(st.session_state.history):
    if message["role"] == "user":
        st.markdown(f'<div class="chat-message user-message"><strong>You:</strong> {message["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-message assistant-message"><strong>Assistant:</strong> {message["content"]}</div>', unsafe_allow_html=True)
        if "sql_query" in message:
            with st.expander("🔍 View SQL Query"):
                st.markdown(f'<div class="sql-code">{message["sql_query"]}</div>', unsafe_allow_html=True)
        if "results" in message and message["results"] is not None:
            with st.expander("📊 View Results", expanded=True):
                df = message["results"]
                st.dataframe(df, use_container_width=True)
                # --- Download options ---
                col1, col2 = st.columns(2)
                with col1:
                    csv = df.to_csv(index=False)
                    st.download_button("Download CSV", csv, f"query_results_{i}.csv", "text/csv")
                with col2:
                    if len(df) > 0 and len(df.columns) > 1:
                        chart_type = st.selectbox("Chart Type", ["Bar", "Line", "Pie", "Scatter", "Histogram"], key=f"chart_type_{i}")
                        x_axis = st.selectbox("X Axis", df.columns, key=f"x_axis_{i}")
                        y_axis = st.selectbox("Y Axis", df.select_dtypes(include=['number']).columns, key=f"y_axis_{i}")
                        if st.button("📈 Create Chart", key=f"chart_{i}"):
                            if chart_type == "Bar":
                                fig = px.bar(df, x=x_axis, y=y_axis)
                            elif chart_type == "Line":
                                fig = px.line(df, x=x_axis, y=y_axis)
                            elif chart_type == "Pie":
                                fig = px.pie(df, names=x_axis, values=y_axis)
                            elif chart_type == "Scatter":
                                fig = px.scatter(df, x=x_axis, y=y_axis)
                            elif chart_type == "Histogram":
                                fig = px.histogram(df, x=x_axis, y=y_axis)
                            st.plotly_chart(fig, use_container_width=True)

# --- CHAT FORM ---
with st.form("chat_form", clear_on_submit=True):
    query_input = st.text_input("Ask me anything about your data:", value=st.session_state.get("current_query", ""), placeholder="e.g., Show me total sales for this month")
    submitted = st.form_submit_button("Send")
    if submitted and query_input:
        st.session_state.current_query = ""
        st.session_state.history.append({"role": "user", "content": query_input})
        with st.spinner("Processing your query..."):
            try:
                allowed_tables = get_allowed_tables(st.session_state.role, st.session_state.role_access)
                allowed_columns = {t: get_allowed_columns(st.session_state.role, t, st.session_state.role_access, st.session_state.table_cols) for t in allowed_tables}
                sql_query, response, df = st.session_state.query_agent.answer_query(query_input, allowed_tables, allowed_columns)
                st.session_state.history.append({
                    "role": "assistant",
                    "content": response,
                    "sql_query": sql_query,
                    "results": df
                })
            except Exception as e:
                st.session_state.history.append({"role": "assistant", "content": f"Error: {e}"})
        st.rerun()

# --- FOOTER ---
st.markdown("---")
st.markdown("**RAG SQL Chatbot** - Business-Grade Chatbot with Role-Based Access") 