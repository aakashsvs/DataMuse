import os
import sys

def check_offline_requirements():
    """Check if all requirements for offline operation are met"""
    print("🔍 Checking offline requirements...")
    
    # Check database
    if os.path.exists('db/bank_exchange.db'):
        print("✅ Database: db/bank_exchange.db")
    else:
        print("❌ Database missing: db/bank_exchange.db")
        print("   Run: python create_bank_exchange_db.py")
    
    # Check data files
    data_files = [
        'data/data_dictionary.xlsx',
        'data/role_access.xlsx',
        'data/schema.pdf',
        'data/er_diagram.jpeg'
    ]
    for file in data_files:
        if os.path.exists(file):
            print(f"✅ Data: {file}")
        else:
            print(f"❌ Data missing: {file}")
            print(f"   Run the appropriate create_*.py script")
    
    # Check models
    models_dir = 'models'
    if os.path.exists(models_dir):
        models = os.listdir(models_dir)
        if any(f.lower().find('sqlcoder') != -1 and f.endswith('.gguf') for f in models):
            print("✅ SQLCoder model found")
        elif any(f.endswith('.gguf') for f in models):
            print("⚠️  .gguf model found (not SQLCoder)")
        else:
            print("❌ No .gguf models found")
            print("   Download SQLCoder.gguf to models/ folder")
    else:
        print("❌ Models directory missing")
        print("   Create models/ folder and add SQLCoder.gguf")
    
    # Check Python packages
    required_packages = [
        'streamlit', 'pandas', 'plotly', 'fpdf', 
        'sentence_transformers', 'llama_cpp', 'openpyxl'
    ]
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ Package: {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ Package missing: {package}")
    
    if missing_packages:
        print(f"\n📦 Install missing packages:")
        print(f"pip install {' '.join(missing_packages)}")
    
    print("\n🎯 Offline Setup Summary:")
    print("1. All data files should be in data/ folder")
    print("2. SQLCoder.gguf should be in models/ folder")
    print("3. All Python packages should be installed")
    print("4. Run: streamlit run enhanced_app.py")

if __name__ == "__main__":
    check_offline_requirements() 