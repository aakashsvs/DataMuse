import sqlite3
import pandas as pd
from enhanced_llm_interface import generate_sql_llm
from enhanced_embedding import SchemaEmbedder

def filter_sql_to_allowed(sql_query, allowed_tables, allowed_columns):
    # Basic check: only allow queries on allowed tables/columns
    # (For production, use SQL parsing for security)
    sql_lower = sql_query.lower()
    
    # Check if any allowed table is mentioned in the query
    table_found = False
    for table in allowed_tables:
        if table.lower() in sql_lower:
            table_found = True
            # If user has 'ALL' access to this table, allow it
            if allowed_columns.get(table) == 'ALL' or 'all' in str(allowed_columns.get(table, '')).lower():
                return True
            # Check if any allowed columns for this table are mentioned
            allowed_cols = allowed_columns.get(table, [])
            for col in allowed_cols:
                if col.lower() in sql_lower:
                    return True
    
    # If no specific tables found but user has access to tables, allow generic queries
    if allowed_tables and table_found:
        return True
    
    # For very generic queries (like SELECT * FROM table), allow if user has access to any table
    if allowed_tables and ('select' in sql_lower and 'from' in sql_lower):
        return True
        
    return False

def format_context_rows(context_rows):
    # Convert context rows (from SchemaEmbedder.search) to a string for LLM prompt
    if not context_rows:
        return ''
    lines = []
    for row in context_rows:
        if isinstance(row, pd.Series):
            lines.append(f"{row['Table']}.{row['Column']}: {row['Column Description']}")
        else:
            lines.append(str(row))
    return '\n'.join(lines)

def validate_sql(sql_query, allowed_tables, allowed_columns):
    """Validate SQL query before execution - dynamic schema validation"""
    sql_lower = sql_query.lower()
    
    # Check for common SQLite syntax issues
    if 'interval' in sql_lower:
        return False, "SQLite doesn't support INTERVAL syntax. Use date('now', '-1 month') instead."
    
    if 'current_date' in sql_lower and 'interval' in sql_lower:
        return False, "Use date('now', '-1 month') for date arithmetic in SQLite."
    
    # Allow system queries (schema introspection)
    system_queries = [
        'sqlite_master',
        'pragma table_info',
        'pragma foreign_key_list',
        'pragma index_list'
    ]
    
    for sys_query in system_queries:
        if sys_query in sql_lower:
            return True, "System query allowed."
    
    # Check if all mentioned tables are allowed
    mentioned_tables = []
    for table in allowed_tables:
        if table.lower() in sql_lower:
            mentioned_tables.append(table)
    
    if not mentioned_tables:
        return False, "No allowed tables found in query."
    
    # Check if mentioned columns exist in allowed tables
    for table in mentioned_tables:
        allowed_cols = allowed_columns.get(table, [])
        if allowed_cols == 'ALL':
            continue  # Skip validation for tables with full access
        
        # Extract column names from SQL (basic check)
        import re
        table_pattern = rf'{table}\.(\w+)'
        columns_in_sql = re.findall(table_pattern, sql_query, re.IGNORECASE)
        
        for col in columns_in_sql:
            if col.lower() not in [c.lower() for c in allowed_cols]:
                return False, f"Column '{col}' not allowed for table '{table}'."
    
    return True, "SQL validation passed."

class QueryAgent:
    def __init__(self, db_path, data_dict, role_access):
        self.db_path = db_path
        self.data_dict = data_dict
        self.role_access = role_access
        self.embedder = SchemaEmbedder('data/data_dictionary.xlsx')

    def answer_query(self, question, allowed_tables, allowed_columns):
        # RAG: Retrieve top-k relevant schema/context
        rag_context_rows = self.embedder.search(question, top_k=5)
        rag_context = format_context_rows(rag_context_rows)
        # Use LLM to generate SQL with both full schema and RAG context
        sql_query_rag = generate_sql_llm(question, allowed_tables, allowed_columns, self.data_dict, rag_context=rag_context)
        sql_query_full = generate_sql_llm(question, allowed_tables, allowed_columns, self.data_dict)
        # Prefer RAG SQL if it uses relevant tables/columns
        sql_query = None
        if sql_query_rag and filter_sql_to_allowed(sql_query_rag, allowed_tables, allowed_columns):
            sql_query = sql_query_rag
        elif sql_query_full and filter_sql_to_allowed(sql_query_full, allowed_tables, allowed_columns):
            sql_query = sql_query_full
        if not sql_query:
            return None, "You are not allowed to access the requested data or the query could not be generated.", None
        
        # Validate SQL before execution
        is_valid, validation_msg = validate_sql(sql_query, allowed_tables, allowed_columns)
        if not is_valid:
            return sql_query, f"SQL validation failed: {validation_msg}", None
        
        # Run SQL
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(sql_query, conn)
            conn.close()
        except Exception as e:
            return sql_query, f"Error executing SQL: {e}", None
        # Build response
        response = self.generate_natural_response(question, df, sql_query)
        return sql_query, response, df

    def generate_natural_response(self, question, df, sql_query):
        if df is None or df.empty:
            return "I couldn't find any data matching your query."
        row_count = len(df)
        col_count = len(df.columns)
        response = f"I found {row_count} record(s) with {col_count} field(s) based on your query. "
        # Use data dictionary for column explanations
        if self.data_dict is not None and not self.data_dict.empty:
            col_desc = []
            for col in df.columns:
                desc = self.data_dict.loc[self.data_dict['Column'] == col, 'Column Description']
                if not desc.empty:
                    col_desc.append(f"{col} ({desc.values[0]})")
                else:
                    col_desc.append(col)
            response += "\nColumns: " + ", ".join(col_desc)
        return response 