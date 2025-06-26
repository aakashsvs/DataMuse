# Advanced Role-Based RAG SQL Chatbot

A sophisticated, offline-capable SQL chatbot system with role-based access control, dynamic schema loading, and multi-model LLM integration. Built with Streamlit, SQLite, and open-source LLMs.

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit UI  │    │   Query Agent   │    │   LLM Interface │
│   (enhanced_app)│◄──►│ (enhanced_query)│◄──►│ (enhanced_llm)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Role Access   │    │  Schema Embedder│    │   Local LLMs    │
│   (Excel File)  │    │ (enhanced_embed)│    │  (.gguf Files)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│   SQLite DB     │    │  Data Dictionary│
│ (bank_exchange) │    │   (Excel File)  │
└─────────────────┘    └─────────────────┘
```

## 📁 Project Structure

```
cursor app/
├── 📊 Data Generation Scripts
│   ├── create_bank_exchange_db.py      # Creates synthetic banking database
│   ├── create_data_dictionary.py       # Generates Excel data dictionary
│   ├── create_er_diagram.py           # Creates ER diagram visualization
│   ├── create_schema_pdf.py           # Generates PDF schema documentation
│   └── create_role_access.py          # Creates role-based access matrix
│
├── 🧠 Core Application Files
│   ├── enhanced_app.py                # Main Streamlit application
│   ├── enhanced_query_agent.py        # Query processing and validation
│   ├── enhanced_llm_interface.py      # LLM integration (SQLCoder/Mistral)
│   └── enhanced_embedding.py          # RAG with schema embeddings
│
├── 🗄️ Database & Data
│   ├── db/
│   │   └── bank_exchange.db           # SQLite database
│   └── data/
│       ├── data_dictionary.xlsx       # Schema documentation
│       ├── role_access.xlsx           # Role permissions matrix
│       ├── schema.pdf                 # Schema documentation
│       └── er_diagram.jpeg            # Entity relationship diagram
│
├── 🤖 AI Models
│   └── models/
│       ├── sqlcoder-7b-q5_k_m.gguf   # SQL generation model
│       ├── mistral-7b-instruct-v0.1.Q4_K_M.gguf  # Reasoning model
│       └── mpnet-embedding/           # Embedding model for RAG
│
├── 🛠️ Utilities
│   └── utils/
│       └── utils_auth.py             # Authentication utilities
│
└── 📋 Documentation
    └── README.md                     # This file
```

## 🔧 Core Components Explained

### 1. Data Generation Layer

#### `create_bank_exchange_db.py`
- **Purpose**: Creates a realistic synthetic banking database
- **Tables**: 10 tables including customers, accounts, transactions, employees, branches, loans, cards
- **Features**: 
  - Foreign key relationships
  - Realistic data distribution
  - 1000+ synthetic records
  - Proper SQLite schema design

#### `create_data_dictionary.py`
- **Purpose**: Generates comprehensive Excel data dictionary
- **Content**: Table descriptions, column definitions, data types, relationships
- **Usage**: Provides human-readable schema documentation for LLM context

#### `create_er_diagram.py`
- **Purpose**: Visualizes database relationships
- **Technology**: NetworkX + Matplotlib
- **Output**: JPEG diagram showing table relationships and foreign keys

#### `create_role_access.py`
- **Purpose**: Defines role-based access control matrix
- **Roles**: Teller, Manager, Auditor, IT, Customer Service
- **Permissions**: Granular column-level access control
- **Format**: Excel file with role-table-column permissions

### 2. Core Application Layer

#### `enhanced_app.py` (Main Application)
- **Framework**: Streamlit
- **Features**:
  - Role-based authentication
  - Dynamic schema loading
  - Real-time query processing
  - Results visualization
  - Error handling and validation

**Key Functions**:
```python
def get_allowed_tables(role, role_access)      # Role-based table access
def get_allowed_columns(role, table, role_access)  # Column-level permissions
def get_table_columns()                        # Dynamic schema discovery
```

#### `enhanced_query_agent.py` (Query Processing)
- **Purpose**: Orchestrates query generation and execution
- **Features**:
  - RAG-enhanced SQL generation
  - SQL validation and security
  - Role-based query filtering
  - Natural language response generation

**Key Functions**:
```python
def filter_sql_to_allowed()     # Security validation
def validate_sql()              # SQL syntax validation
def answer_query()              # Main query processing
```

#### `enhanced_llm_interface.py` (AI Integration)
- **Purpose**: Interfaces with local LLMs for SQL generation
- **Models**: SQLCoder (primary), Mistral (fallback)
- **Features**:
  - Schema-aware prompting
  - SQLite syntax enforcement
  - Error handling and fallbacks

**Key Functions**:
```python
def generate_sql_llm()          # Main SQL generation
```

#### `enhanced_embedding.py` (RAG System)
- **Purpose**: Provides context-aware schema retrieval
- **Technology**: SentenceTransformers (MPNet)
- **Features**:
  - Semantic schema search
  - Cached embeddings
  - Top-k relevant context retrieval

**Key Functions**:
```python
def search()                    # Semantic schema search
def get_embeddings()            # Generate embeddings
```

### 3. Data Layer

#### Database Schema (`bank_exchange.db`)
```
Tables:
├── cust_mast (Customers)
├── acct_mast (Accounts)
├── txn_hist (Transactions)
├── emp_mast (Employees)
├── branch_mast (Branches)
├── dept_mast (Departments)
├── loan_mast (Loans)
├── card_mast (Cards)
├── amc_mast (Asset Management)
└── euin_mast (Employee IDs)
```

#### Role Access Matrix (`role_access.xlsx`)
- **Teller**: Basic customer and transaction access
- **Manager**: Full access to most tables
- **Auditor**: Read-only access to all data
- **IT**: Technical table access
- **Customer Service**: Customer-focused access

## 🚀 How It Works

### 1. User Authentication & Authorization
```python
# User selects role
role = st.selectbox("Select Role", ["Teller", "Manager", "Auditor", "IT", "Customer Service"])

# System loads role-specific permissions
allowed_tables = get_allowed_tables(role, role_access)
allowed_columns = get_allowed_columns(role, table, role_access)
```

### 2. Query Processing Pipeline
```
User Question → RAG Context Retrieval → LLM SQL Generation → Validation → Execution → Response
```

**Step-by-step**:
1. **Question Input**: User asks natural language question
2. **RAG Retrieval**: System finds relevant schema context
3. **SQL Generation**: LLM creates SQL using schema + RAG context
4. **Validation**: Security and syntax validation
5. **Execution**: Query runs against SQLite database
6. **Response**: Results formatted and displayed

### 3. LLM Integration
```python
# Schema context creation
schema_context = f"Table: {table}\nColumns: {columns}"

# LLM prompt
prompt = f"""You are SQLCoder, an expert SQL generator for SQLite databases.
Schema: {schema_context}
Question: {question}
Generate ONLY the SQL query:"""

# Model execution
llm = Llama(model_path=sqlcoder_path, n_ctx=2048, n_threads=4)
sql = llm(prompt, max_tokens=256, stop=[";", "\n"])
```

### 4. Security & Validation
- **Role-based filtering**: Only allowed tables/columns accessible
- **SQL validation**: Syntax and security checks
- **Query sanitization**: Prevents unauthorized access

## 🛠️ Setup Instructions

### Prerequisites
```bash
# Python 3.8+
# 8GB+ RAM (for LLM models)
# Windows/Linux/macOS
```

### Installation
```bash
# 1. Clone repository
git clone <repository-url>
cd cursor-app

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download models (if not already present)
# Place .gguf files in models/ directory
```

### Model Setup
```bash
# Required models in models/ directory:
├── sqlcoder-7b-q5_k_m.gguf          # Primary SQL generation
├── mistral-7b-instruct-v0.1.Q4_K_M.gguf  # Fallback model
└── mpnet-embedding/                  # Embedding model (auto-downloaded)
```

### Database Setup
```bash
# 1. Generate synthetic database
python create_bank_exchange_db.py

# 2. Create data dictionary
python create_data_dictionary.py

# 3. Generate ER diagram
python create_er_diagram.py

# 4. Create role access matrix
python create_role_access.py

# 5. Generate schema PDF
python create_schema_pdf.py
```

### Running the Application
```bash
# Start Streamlit app
streamlit run enhanced_app.py

# Access at: http://localhost:8501
```

## 📊 Usage Examples

### Basic Queries
```
"Show me all customers"
"List accounts with balance over 50000"
"Find transactions from last month"
```

### Complex Queries
```
"Find customers who have both savings and checking accounts"
"Show total revenue by branch for last month"
"List employees who processed more than 100 transactions"
```

### Role-Specific Access
- **Teller**: Basic customer and transaction queries
- **Manager**: Full access to business analytics
- **Auditor**: Read-only access to all data
- **IT**: Technical and system queries
- **Customer Service**: Customer-focused queries

## 🔒 Security Features

### Role-Based Access Control
- **Granular permissions**: Table and column-level access
- **Dynamic filtering**: Queries automatically filtered by role
- **Audit trail**: All queries logged and validated

### SQL Injection Prevention
- **Parameterized queries**: Safe query execution
- **Input validation**: User input sanitization
- **Schema validation**: Only allowed tables/columns accessible

### Data Privacy
- **Column-level security**: Sensitive data protected
- **Role isolation**: Users only see permitted data
- **Query logging**: Audit trail for compliance

## 🎯 Key Features

### ✅ Implemented
- [x] Offline-capable LLM integration
- [x] Role-based access control
- [x] Dynamic schema loading
- [x] RAG-enhanced query generation
- [x] SQL validation and security
- [x] Natural language responses
- [x] Real-time query processing
- [x] Error handling and fallbacks
- [x] Comprehensive documentation
- [x] Synthetic data generation

### 🔄 Advanced Features
- [x] Multi-model LLM support
- [x] Embedding-based RAG
- [x] Schema-aware prompting
- [x] SQLite syntax enforcement
- [x] Cached embeddings
- [x] Visual ER diagrams
- [x] PDF schema documentation

## 🐛 Troubleshooting

### Common Issues

**1. Model Loading Errors**
```bash
# Check model files exist
ls models/*.gguf

# Verify model compatibility
# Use compatible .gguf models
```

**2. Database Connection Issues**
```bash
# Regenerate database
python create_bank_exchange_db.py

# Check file permissions
# Ensure db/ directory exists
```

**3. Memory Issues**
```bash
# Reduce model context size
# Use smaller .gguf models
# Increase system RAM
```

**4. Permission Errors**
```bash
# Check role access file
# Verify Excel file format
# Ensure proper file paths
```

## 📈 Performance Optimization

### LLM Performance
- **Context size**: Optimized for 2048 tokens
- **Threading**: 4 threads for parallel processing
- **Caching**: Embeddings cached for faster RAG

### Database Performance
- **Indexing**: Proper foreign key relationships
- **Query optimization**: Efficient SQL generation
- **Connection pooling**: Optimized database connections

### UI Performance
- **Streamlit caching**: Results cached for repeated queries
- **Lazy loading**: Models loaded on demand
- **Async processing**: Non-blocking query execution

## 🔮 Future Enhancements

### Planned Features
- [ ] Multi-database support (PostgreSQL, MySQL)
- [ ] Advanced analytics and reporting
- [ ] Natural language query optimization
- [ ] Real-time data streaming
- [ ] Advanced visualization options
- [ ] API endpoints for integration
- [ ] Cloud deployment support
- [ ] Advanced security features

### Technical Improvements
- [ ] Model fine-tuning capabilities
- [ ] Advanced RAG techniques
- [ ] Query performance optimization
- [ ] Enhanced error handling
- [ ] Better documentation generation
- [ ] Automated testing suite

## 📚 Technical Details

### Dependencies
```
streamlit>=1.46.0
pandas>=2.3.0
sqlite3
llama-cpp-python>=0.3.9
sentence-transformers>=4.1.0
plotly>=6.1.2
openpyxl>=3.1.5
networkx>=3.5
matplotlib>=3.10.3
fpdf>=1.7.2
```

### Architecture Patterns
- **MVC Pattern**: Separation of UI, logic, and data
- **Repository Pattern**: Data access abstraction
- **Strategy Pattern**: Multiple LLM model support
- **Observer Pattern**: Real-time UI updates
- **Factory Pattern**: Dynamic component creation

### Security Patterns
- **Principle of Least Privilege**: Minimal required access
- **Defense in Depth**: Multiple security layers
- **Input Validation**: Comprehensive sanitization
- **Audit Logging**: Complete activity tracking

## 🤝 Contributing

### Development Setup
```bash
# Fork repository
# Create feature branch
git checkout -b feature/new-feature

# Make changes
# Add tests
# Submit pull request
```

### Code Standards
- **PEP 8**: Python code style
- **Type hints**: Function signatures
- **Docstrings**: Comprehensive documentation
- **Error handling**: Graceful error management
- **Testing**: Unit and integration tests

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **SQLCoder**: For excellent SQL generation capabilities
- **Mistral AI**: For powerful reasoning models
- **Streamlit**: For rapid web app development
- **SentenceTransformers**: For embedding capabilities
- **SQLite**: For lightweight database solution

---

**Built with ❤️ for secure, efficient, and intelligent data querying** 