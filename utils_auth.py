import hashlib
import pandas as pd
import os

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_user_role(username, role_access_path='data/role_access.xlsx'):
    # For demo: username is the role name (manager, auditor, it, intern)
    # Returns the role if it exists in role_access.xlsx, else None
    if not os.path.exists(role_access_path):
        return None
    df = pd.read_excel(role_access_path)
    username = username.lower()
    roles = [str(r).lower() for r in df['role']]
    if username in roles:
        return username
    return None

def get_allowed_tables_for_role(role, role_access_path='data/role_access.xlsx'):
    if not os.path.exists(role_access_path):
        return []
    df = pd.read_excel(role_access_path)
    row = df[df['role'].str.lower() == role.lower()]
    if not row.empty:
        allowed = row.iloc[0]['allowed_tables']
        if isinstance(allowed, str):
            return [t.strip() for t in allowed.split(',') if t.strip()]
    return [] 