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
    # Load valid roles from role_access.xlsx
    if not os.path.exists(ROLE_ACCESS_PATH):
        return None

    try:
        roles_df = pd.read_excel(ROLE_ACCESS_PATH, index_col=0)
        valid_roles = [r.strip().lower() for r in roles_df.index.tolist()]
    except Exception as e:
        print(f"Error loading role access file: {e}")
        return None

    # Match case-insensitively
    username_clean = username.strip().lower()
    if username_clean in valid_roles and password == f"{username_clean}123":
        return username_clean.title()  # Normalize title case
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
    /* General Body and App Styling */
    body, .stApp {
        background-color: #343541; /* ChatGPT dark background */
        color: #ececec;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }

    /* Main content area */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 5rem; /* Space for the fixed input bar */
    }

    /* --- CHAT STYLES --- */
    .chat-message {
        display: flex;
        align-items: flex-start;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        width: 100%;
    }

    .chat-message.user-message {
        background-color: #343541; /* User message background */
    }

    .chat-message.assistant-message {
        background-color: #444654; /* Assistant message background */
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .chat-message .avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        margin-right: 1.5rem;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        color: white;
    }

    .chat-message.user-message .avatar {
        background-color: #19c37d; /* Green avatar for user */
    }

    .chat-message.assistant-message .avatar {
        background-color: #9b59b6; /* Purple avatar for assistant */
    }
    
    .chat-message .message-content {
        flex: 1;
        font-size: 1rem;
        line-height: 1.6;
    }

    /* --- SQL / DATAFRAME STYLES --- */
    .sql-code {
        background-color: #0e0e0e;
        color: #f8f8f2;
        border: 1px solid #555;
        border-radius: 5px;
        padding: 1rem;
        font-family: 'Fira Code', 'Courier New', monospace;
        font-size: 0.9rem;
    }

    .stDataFrame {
        border: 1px solid #555;
        border-radius: 5px;
    }
    .stDataFrame, .stTable {
        background: #2a2b32;
    }


    /* --- SIDEBAR STYLES --- */
    .stSidebar {
        background-color: #202123;
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    .stSidebar .stButton>button {
        background-color: transparent;
        border: 1px solid #555;
        color: #ececec;
        margin-bottom: 0.5rem;
    }
    .stSidebar .stButton>button:hover {
        background-color: #444654;
        border-color: #777;
    }
    .stSidebar h1, .stSidebar h2, .stSidebar h3, .stSidebar h4, .stSidebar p, .stSidebar li {
        color: #ececec;
    }

    /* --- CHAT INPUT STYLES --- */
    .chat-input-container {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        padding: 1rem 1rem;
        background: linear-gradient(to top, #343541 50%, transparent);
        display: flex;
        justify-content: center;
    }
    .chat-input-form {
        width: 60%;
        max-width: 768px;
    }
    .stTextInput>div>div>input {
        background-color: #40414f;
        color: #fff;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 0.5rem;
        padding: 0.75rem 1rem;
    }
    .stButton[kind="form_submit"]>button {
        background-color: #19c37d;
        color: white;
        border: none;
    }
    
    /* --- HIDE USELESS ELEMENTS --- */
    .main-header, footer {
        display: none;
    }
    
    /* Add new styles for the toggle button */
    .sidebar-toggle {
        position: fixed;
        top: 0.5rem;
        right: 1rem;
        z-index: 1000;
        padding: 0.5rem;
        background: #2e2d88;
        border-radius: 0.5rem;
        color: white;
        cursor: pointer;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }
    
    /* Adjust main content when sidebar is hidden */
    .main.sidebar-hidden .block-container {
        padding-left: 1rem !important;
        max-width: 100% !important;
    }
    
    /* Hide default Streamlit menu button */
    #MainMenu {visibility: hidden;}
    
    /* Adjust sidebar width */
    .css-1d391kg {
        width: 20rem;
    }
</style>
""", unsafe_allow_html=True)

# --- APP START ---
st.set_page_config(
    page_title="RAG SQL Chatbot",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🤖"
)

# Add this right after the CSS block
st.markdown("""
<style>
    /* Existing CSS remains unchanged */
    
    /* Add new styles for the toggle button */
    .sidebar-toggle {
        position: fixed;
        top: 0.5rem;
        right: 1rem;
        z-index: 1000;
        padding: 0.5rem;
        background: #2e2d88;
        border-radius: 0.5rem;
        color: white;
        cursor: pointer;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }
    
    /* Adjust main content when sidebar is hidden */
    .main.sidebar-hidden .block-container {
        padding-left: 1rem !important;
        max-width: 100% !important;
    }
    
    /* Hide default Streamlit menu button */
    #MainMenu {visibility: hidden;}
    
    /* Adjust sidebar width */
    .css-1d391kg {
        width: 20rem;
    }
</style>
""", unsafe_allow_html=True)

# Add this right after st.set_page_config
if 'sidebar_state' not in st.session_state:
    st.session_state.sidebar_state = 'expanded'

# Add toggle button
toggle_btn = """
<div class='sidebar-toggle' onclick='
    const icon = document.getElementById("toggle-icon");
    const sidebar = document.querySelector("section.css-1d391kg");
    const main = document.querySelector("section.main");
    if (sidebar.style.display === "none") {
        sidebar.style.display = "block";
        icon.innerHTML = "◀";
        main.classList.remove("sidebar-hidden");
    } else {
        sidebar.style.display = "none";
        icon.innerHTML = "▶";
        main.classList.add("sidebar-hidden");
    }
'>
    <span id="toggle-icon">◀</span>
</div>
"""
st.markdown(toggle_btn, unsafe_allow_html=True)

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
    st.title("🤖 RAG SQL Chatbot")
    st.subheader("Login to continue")
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

# --- SIDEBAR ---
with st.sidebar:
    st.title(f"👋 {st.session_state.username.title()}")
    st.write(f"**Role:** {st.session_state.role}")
    st.divider()

    # --- METRICS MOVED TO SIDEBAR ---
    st.subheader("📊 Metrics")
    st.info(f'DB Status: {"Connected" if st.session_state.db_connected else "Disconnected"}')
    allowed_tables = get_allowed_tables(st.session_state.role, st.session_state.role_access)
    st.info(f'Allowed Tables: {len(allowed_tables)}')
    st.info(f'Queries Made: {len(st.session_state.history)}')
    st.divider()

    st.subheader("📋 Allowed Tables")
    for table in allowed_tables:
        st.write(f"• {table}")
    st.divider()

    st.subheader("💡 Sample Queries")
    
    # Organize queries by category
    transaction_queries = {
        "Transactions": [
            "Show me total sales for this month",
            "Show recent transactions",
            "What is the average transaction amount?",
            "Show me transactions above $1000",
            "Show me daily transaction trends"
        ]
    }
    
    customer_queries = {
        "Customer Analysis": [
            "List top 10 customers by revenue",
            "Count all customers",
            "Show me customer distribution by region",
            "Which customers have multiple accounts?"
        ]
    }
    
    account_queries = {
        "Account Information": [
            "Show account balances by type",
            "List accounts opened in the last month",
            "Calculate total deposits by account type",
            "List inactive accounts",
            "What is the average balance by customer type?"
        ]
    }
    
    loan_queries = {
        "Loan Management": [
            "Show loan status summary",
            "List all pending loan applications",
            "Show me overdue loans"
        ]
    }
    
    branch_queries = {
        "Branch Performance": [
            "What are the top performing branches?",
            "Show branch-wise transaction volume",
            "List branches by customer count"
        ]
    }

    # Display queries in expandable sections
    for category, queries in {**transaction_queries, **customer_queries, **account_queries, **loan_queries, **branch_queries}.items():
        with st.expander(f"📋 {category}", expanded=False):
            for query in queries:
                if st.button(query, key=f"sample_{query}", use_container_width=True):
                    st.session_state.current_query = query
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

# --- MAIN CHAT INTERFACE ---
st.title("🤖 RAG SQL Chatbot")

# --- CHAT HISTORY ---
for i, message in enumerate(st.session_state.history):
    is_user = message["role"] == "user"
    avatar_content = st.session_state.username[0].upper() if is_user else "🤖"
    
    if is_user:
        st.markdown(f"""
        <div class="chat-message user-message">
            <div class="avatar">{avatar_content}</div>
            <div class="message-content">{message["content"]}</div>
        </div>
        """, unsafe_allow_html=True)
    else: # Assistant
        st.markdown(f"""
        <div class="chat-message assistant-message">
            <div class="avatar">{avatar_content}</div>
            <div class="message-content">{message["content"]}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Display SQL query and results in expanders, ChatGPT-style
        if "sql_query" in message and message["sql_query"]:
            with st.expander("🔍 View SQL Query"):
                st.markdown(f'<div class="sql-code">{message["sql_query"]}</div>', unsafe_allow_html=True)
        
        if "results" in message and message["results"] is not None and not message["results"].empty:
            with st.expander("📊 View Results", expanded=True):
                df = message["results"]
                st.dataframe(df, use_container_width=True)
                
                # --- Download and Charting options ---
                col1, col2 = st.columns(2)
                with col1:
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button("Download CSV", csv, f"query_results_{i}.csv", "text/csv", key=f"csv_{i}")
                with col2:
                    if len(df.columns) > 1:
                        try:
                            # Simple chart builder
                            st.write("📈 **Create a quick chart**")
                            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                            all_cols = df.columns.tolist()
                            if len(numeric_cols) >= 1:
                                x_axis = st.selectbox("X-Axis", all_cols, key=f"x_axis_{i}")
                                y_axis = st.selectbox("Y-Axis", numeric_cols, key=f"y_axis_{i}")
                                chart_type = st.selectbox("Chart Type", ["Bar", "Line"], key=f"chart_type_{i}")
                                if chart_type == "Bar":
                                    fig = px.bar(df, x=x_axis, y=y_axis)
                                    st.plotly_chart(fig, use_container_width=True)
                                elif chart_type == "Line":
                                    fig = px.line(df, x=x_axis, y=y_axis)
                                    st.plotly_chart(fig, use_container_width=True)
                        except Exception as e:
                            st.warning(f"Could not generate chart: {e}")


# --- FIXED CHAT INPUT FORM ---
st.markdown('<div class="chat-input-container">', unsafe_allow_html=True)
with st.form(key="chat_form", clear_on_submit=True):
    col1, col2 = st.columns([8, 1])
    with col1:
        query_input = st.text_input(
            "chat-input", # internal key
            value=st.session_state.get("current_query", ""), 
            placeholder="Ask me anything about your data...",
            label_visibility="collapsed"
        )
    with col2:
        submitted = st.form_submit_button("➤")

    if submitted and query_input:
        st.session_state.current_query = "" # Clear sample query
        st.session_state.history.append({"role": "user", "content": query_input})
        
        with st.spinner("Processing..."):
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
                st.session_state.history.append({"role": "assistant", "content": f"An error occurred: {e}"})
        
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# --- FOOTER ---
st.markdown("---")
st.markdown("**RAG SQL Chatbot** - Business-Grade Chatbot with Role-Based Access") 
