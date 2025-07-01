import sqlite3
import pandas as pd
import os

# Ensure data directory exists
os.makedirs('data', exist_ok=True)

DB_PATH = os.path.join('db', 'bank_exchange.db')
DICT_PATH = os.path.join('data', 'data_dictionary.xlsx')

# Human-readable descriptions for tables and columns
TABLE_DESCRIPTIONS = {
    'cust_mast': 'Customer master table',
    'acct_mast': 'Account master table',
    'txn_hist': 'Transaction history',
    'emp_mast': 'Employee master table',
    'branch_mast': 'Branch master table',
    'dept_mast': 'Department master table',
    'card_mast': 'Card master table',
    'loan_mast': 'Loan master table',
    'amc_mast': 'Asset Management Company master',
    'amc_bank_dtl': 'AMC Bank Details',
    'euin_mast': 'Employee Unique Identification Number master',
}
COLUMN_DESCRIPTIONS = {
    'cust_id': 'Customer ID',
    'cust_name': 'Customer Name',
    'dob': 'Date of Birth',
    'address': 'Customer Address',
    'phone': 'Customer Phone Number',
    'acct_id': 'Account ID',
    'branch_id': 'Branch ID',
    'acct_type': 'Account Type',
    'open_date': 'Account Open Date',
    'balance': 'Account Balance',
    'txn_id': 'Transaction ID',
    'txn_date': 'Transaction Date',
    'amount': 'Transaction Amount',
    'txn_type': 'Transaction Type',
    'description': 'Transaction Description',
    'emp_id': 'Employee ID',
    'emp_name': 'Employee Name',
    'dept_id': 'Department ID',
    'dept_name': 'Department Name',
    'euin_no': 'Employee Unique Identification Number',
    'issue_date': 'Issue Date',
    'branch_name': 'Branch Name',
    'location': 'Branch Location',
    'card_id': 'Card ID',
    'card_type': 'Card Type',
    'expiry_date': 'Card Expiry Date',
    'status': 'Status',
    'loan_id': 'Loan ID',
    'amount': 'Loan Amount',
    'amc_id': 'AMC ID',
    'amc_name': 'AMC Name',
    'amc_bank_id': 'AMC Bank ID',
    'bank_name': 'Bank Name',
    'account_no': 'Bank Account Number',
    'ifsc_code': 'Bank IFSC Code',
}

def get_schema():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    schema = []
    
    # Get all foreign key relationships first
    all_fks = {}
    for (table_name,) in tables:
        fks = cursor.execute(f'PRAGMA foreign_key_list({table_name})').fetchall()
        for fk in fks:
            # fk[3] is the 'from' column, fk[2] is the 'to' table, fk[4] is the 'to' column
            all_fks[(table_name, fk[3])] = (fk[2], fk[4])

    for (table_name,) in tables:
        if table_name.startswith('sqlite_'):
            continue
        columns = cursor.execute(f'PRAGMA table_info({table_name})').fetchall()
        for col in columns:
            col_name = col[1]
            fk_info = all_fks.get((table_name, col_name))
            
            schema.append({
                'Table': table_name,
                'Table Description': TABLE_DESCRIPTIONS.get(table_name, ''),
                'Column': col_name,
                'Column Description': COLUMN_DESCRIPTIONS.get(col_name, col_name.replace('_', ' ').title()),
                'Type': col[2],
                'PK': '✔' if col[5] else '',
                'Foreign Key Table': fk_info[0] if fk_info else '',
                'Foreign Key Column': fk_info[1] if fk_info else ''
            })
    conn.close()
    return schema

def main():
    schema = get_schema()
    df = pd.DataFrame(schema)
    df.to_excel(DICT_PATH, index=False)
    print(f"Data dictionary written to {DICT_PATH}")

if __name__ == "__main__":
    main() 
