import pandas as pd
import os
import sqlite3

os.makedirs('data', exist_ok=True)
DB_PATH = os.path.join('db', 'bank_exchange.db')
EXCEL_PATH = os.path.join('data', 'role_access.xlsx')

ROLES = ['Teller', 'Manager', 'Auditor', 'IT', 'Customer Service']

def get_tables_and_columns():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    table_cols = {}
    for (table_name,) in tables:
        if table_name.startswith('sqlite_'):
            continue
        columns = cursor.execute(f'PRAGMA table_info({table_name})').fetchall()
        table_cols[table_name] = [col[1] for col in columns]
    conn.close()
    return table_cols

def build_access_matrix(table_cols):
    # Define access per role (example realistic policy)
    access = {
        'Teller': {
            'cust_mast': 'cust_id,cust_name,phone',
            'acct_mast': 'acct_id,cust_id,acct_type,balance',
            'txn_hist': 'ALL',
            'emp_mast': '',
            'branch_mast': '',
            'dept_mast': '',
            'card_mast': 'acct_id,card_id,card_type,status',
            'loan_mast': '',
            'amc_mast': '',
            'amc_bank_dtl': '',
            'euin_mast': '',
        },
        'Manager': {t: 'ALL' for t in table_cols},
        'Auditor': {t: 'ALL' for t in table_cols},
        'IT': {t: 'ALL' for t in table_cols},
        'Customer Service': {
            'cust_mast': 'cust_id,cust_name,phone,address',
            'acct_mast': 'acct_id,cust_id,acct_type,balance',
            'txn_hist': '',
            'emp_mast': '',
            'branch_mast': '',
            'dept_mast': '',
            'card_mast': 'acct_id,card_id,card_type,status',
            'loan_mast': '',
            'amc_mast': '',
            'amc_bank_dtl': '',
            'euin_mast': '',
        },
    }
    # Fill missing tables for each role with ''
    for role in ROLES:
        for t in table_cols:
            if t not in access[role]:
                access[role][t] = ''
    # Build DataFrame
    df = pd.DataFrame.from_dict(access, orient='index')
    df = df[sorted(df.columns)]
    return df

def save_to_db(df):
    conn = sqlite3.connect(DB_PATH)
    # Create role_access table with proper column names
    df.reset_index(names=['role_name'], inplace=True)
    df.to_sql('role_access', conn, if_exists='replace', index=False)
    
    # Create a view for easy querying of allowed tables per role
    conn.execute('DROP VIEW IF EXISTS role_allowed_tables')
    conn.execute('''
    CREATE VIEW role_allowed_tables AS
    WITH RECURSIVE split(role_name, table_name, column_list, rest) AS (
        SELECT 
            role_name,
            table_name,
            access_value as column_list,
            substr(access_value, instr(access_value, ',') + 1) as rest
        FROM (
            SELECT 
                role_name,
                name as table_name,
                value as access_value
            FROM role_access
            CROSS JOIN pragma_table_info('role_access')
            WHERE name != 'role_name'
        )
        UNION ALL
        SELECT
            role_name,
            table_name,
            CASE 
                WHEN instr(rest, ',') = 0 THEN rest
                ELSE substr(rest, 1, instr(rest, ',') - 1)
            END as column_list,
            CASE 
                WHEN instr(rest, ',') = 0 THEN ''
                ELSE substr(rest, instr(rest, ',') + 1)
            END as rest
        FROM split
        WHERE rest != ''
    )
    SELECT DISTINCT
        role_name as role,
        table_name,
        CASE 
            WHEN column_list = 'ALL' THEN 'ALL'
            WHEN column_list = '' THEN NULL
            ELSE column_list
        END as allowed_columns
    FROM split
    WHERE column_list IS NOT NULL AND column_list != ''
    ''')
    conn.commit()
    conn.close()

def main():
    table_cols = get_tables_and_columns()
    df = build_access_matrix(table_cols)
    
    # Save to Excel (keep index for Excel)
    df.to_excel(EXCEL_PATH)
    print(f'Role access matrix written to {EXCEL_PATH}')
    
    # Save to DB
    save_to_db(df.copy())  # Use copy to not affect original df
    print(f'Role access matrix saved to {DB_PATH} in table role_access')
    
    print('\nRole-based access summary:')
    for role in ROLES:
        print(f'\n{role}:')
        role_data = df.loc[role]  # Use original df with index
        accessible_tables = [t for t, access in role_data.items() if str(access).strip()]
        for table in accessible_tables:
            access = role_data[table]
            if access == 'ALL':
                print(f'  ✓ {table} (all columns)')
            else:
                print(f'  ✓ {table} ({access})')

if __name__ == "__main__":
    main() 