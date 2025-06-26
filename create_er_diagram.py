import sqlite3
import os
import networkx as nx
import matplotlib.pyplot as plt

os.makedirs('data', exist_ok=True)
DB_PATH = os.path.join('db', 'bank_exchange.db')
ER_PATH = os.path.join('data', 'er_diagram.jpeg')

def get_schema_and_fks():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    schema = {}
    fks = []
    for (table_name,) in tables:
        if table_name.startswith('sqlite_'):
            continue
        columns = cursor.execute(f'PRAGMA table_info({table_name})').fetchall()
        schema[table_name] = [col[1] for col in columns]
        fk_info = cursor.execute(f'PRAGMA foreign_key_list({table_name})').fetchall()
        for fk in fk_info:
            fks.append((table_name, fk[3], fk[2], fk[4]))  # (from_table, from_col, to_table, to_col)
    conn.close()
    return schema, fks

def plot_er_diagram(schema, fks, path):
    G = nx.DiGraph()
    # Add tables as nodes
    for table, columns in schema.items():
        G.add_node(table, label=f"{table}\n" + "\n".join(columns))
    # Add foreign key edges
    for from_table, from_col, to_table, to_col in fks:
        G.add_edge(from_table, to_table, label=f"{from_col}→{to_col}")
    pos = nx.spring_layout(G, k=1.5, seed=42)
    plt.figure(figsize=(14, 8))
    # Draw nodes
    nx.draw_networkx_nodes(G, pos, node_color='skyblue', node_size=2500)
    # Draw edges
    nx.draw_networkx_edges(G, pos, arrowstyle='-|>', arrowsize=20, edge_color='gray')
    # Draw labels
    labels = {n: f"{n}\n" + "\n".join(schema[n][:3]) + ("..." if len(schema[n]) > 3 else "") for n in G.nodes}
    nx.draw_networkx_labels(G, pos, labels, font_size=9)
    # Draw edge labels
    edge_labels = {(u, v): d['label'] for u, v, d in G.edges(data=True)}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)
    plt.title('ER Diagram')
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(path, format='jpeg')
    plt.close()
    print(f'ER diagram written to {path}')

def main():
    schema, fks = get_schema_and_fks()
    plot_er_diagram(schema, fks, ER_PATH)

if __name__ == '__main__':
    main() 