import os

def generate_sql_llm(question, allowed_tables, allowed_columns, data_dict, rag_context=None):
    """
    Generate a SQL query from a user question using SQLCoder.
    """
    try:
        from llama_cpp import Llama
        
        # Find SQLCoder model
        sqlcoder_path = None
        for f in os.listdir('models'):
            if f.lower().find('sqlcoder') != -1 and f.endswith('.gguf'):
                sqlcoder_path = os.path.join('models', f)
                break
        
        if not sqlcoder_path:
            # Fallback to any .gguf model
            for f in os.listdir('models'):
                if f.endswith('.gguf'):
                    sqlcoder_path = os.path.join('models', f)
                    break
        
        if not sqlcoder_path:
            raise Exception('No .gguf model found in models folder.')
        
        print(f"Using model: {os.path.basename(sqlcoder_path)}")
        
        llm = Llama(model_path=sqlcoder_path, n_ctx=4096, n_gpu_layers=-1, n_threads=4, verbose=False)
        
        # Create clear schema context with foreign keys
        schema_lines = []
        for table in allowed_tables:
            columns = allowed_columns.get(table, [])
            schema_lines.append(f"Table `{table}` has columns: `{', '.join(columns)}`.")
            
            # Add foreign key info from data dictionary if available
            if data_dict is not None and not data_dict.empty:
                fk_info = data_dict[(data_dict['Table'] == table) & (data_dict['Foreign Key Table'].notna())]
                if not fk_info.empty:
                    fks = []
                    for _, row in fk_info.iterrows():
                        fks.append(f"`{row['Column']}` -> `{row['Foreign Key Table']}`.`{row['Foreign Key Column']}`")
                    schema_lines.append(f"  - Foreign Keys: {'; '.join(fks)}")
            schema_lines.append("")

        schema_context = '\n'.join(schema_lines)
        
        # Enhanced prompt with more explicit instructions
        prompt = f"""You are an expert SQL query generator for SQLite. Your task is to write a valid SQLite query based on the user's question and the provided database schema.

### INSTRUCTIONS
1.  **Use ONLY the provided schema**: Do not guess or assume any table or column names that are not listed.
2.  **Join tables correctly**: Use the provided foreign key relationships for JOINS.
3.  **Use valid SQLite syntax**: The target database is SQLite. Ensure all functions, especially for date and time manipulation, are compatible with it. Avoid functions specific to other SQL dialects.
4.  **Output ONLY the SQL query**: Do not add any explanations or extra text.

### DATABASE SCHEMA
{schema_context}

### RAG CONTEXT (Additional relevant context)
{rag_context if rag_context else "No additional context."}

### USER QUESTION
{question}

### SQL QUERY
"""
        
        output = llm(prompt, max_tokens=512, stop=[";", "\n\n"], echo=False)
        sql = output['choices'][0]['text'].strip()
        if not sql.endswith(';'):
            sql += ';'
        return sql
    except Exception as e:
        print(f"LLM Error: {e}")
        if allowed_tables:
            table = allowed_tables[0]
            cols = allowed_columns.get(table, [])
            col_str = ', '.join(cols[:5]) if cols else '*'
            return f"SELECT {col_str} FROM {table} LIMIT 10;"
        return None 