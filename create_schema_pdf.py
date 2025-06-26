import sqlite3
import os
from fpdf import FPDF

os.makedirs('data', exist_ok=True)
DB_PATH = os.path.join('db', 'bank_exchange.db')
PDF_PATH = os.path.join('data', 'schema.pdf')

def get_schema_details():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    schema = {}
    for (table_name,) in tables:
        if table_name.startswith('sqlite_'):
            continue
        columns = cursor.execute(f'PRAGMA table_info({table_name})').fetchall()
        fks = cursor.execute(f'PRAGMA foreign_key_list({table_name})').fetchall()
        schema[table_name] = {
            'columns': columns,
            'foreign_keys': fks
        }
    conn.close()
    return schema

def create_pdf(schema):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font('helvetica', 'B', 16)
    pdf.cell(0, 10, 'Database Schema', ln=True, align='C')
    pdf.ln(10)
    pdf.set_font('helvetica', '', 12)
    for table, details in schema.items():
        pdf.set_font('helvetica', 'B', 14)
        pdf.cell(0, 10, f'Table: {table}', ln=True)
        pdf.set_font('helvetica', 'B', 12)
        pdf.cell(40, 8, 'Column', 1)
        pdf.cell(30, 8, 'Type', 1)
        pdf.cell(20, 8, 'PK', 1)
        pdf.cell(30, 8, 'Default', 1)
        pdf.cell(70, 8, 'Other', 1)
        pdf.ln()
        pdf.set_font('helvetica', '', 12)
        for col in details['columns']:
            pdf.cell(40, 8, str(col[1]), 1)
            pdf.cell(30, 8, str(col[2]), 1)
            pdf.cell(20, 8, 'Yes' if col[5] else '', 1)
            pdf.cell(30, 8, str(col[4]) if col[4] else '', 1)
            pdf.cell(70, 8, '', 1)
            pdf.ln()
        if details['foreign_keys']:
            pdf.set_font('helvetica', 'I', 11)
            pdf.cell(0, 8, 'Foreign Keys:', ln=True)
            pdf.set_font('helvetica', '', 11)
            for fk in details['foreign_keys']:
                pdf.cell(0, 8, f"{fk[3]} -> {fk[2]}.{fk[4]}", ln=True)
        pdf.ln(5)
    try:
        pdf.output(PDF_PATH)
        print(f'Schema PDF written to {PDF_PATH}')
    except Exception as e:
        print(f'Error writing PDF: {e}')

def main():
    schema = get_schema_details()
    create_pdf(schema)

if __name__ == '__main__':
    main() 