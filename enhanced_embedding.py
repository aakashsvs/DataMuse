from sentence_transformers import SentenceTransformer, util
import pandas as pd
import numpy as np
import os

# Try to use local embedding model, fallback to smaller model that can be cached
def get_embedding_model():
    # Check for local embedding models in models folder
    models_dir = 'models'
    if os.path.exists(models_dir):
        for f in os.listdir(models_dir):
            if f.lower().find('embedding') != -1 or f.lower().find('sentence') != -1:
                return os.path.join(models_dir, f)
    
    # Fallback to a smaller model that will be cached locally
    return 'all-MiniLM-L6-v2'  # This will be cached after first download

EMBED_MODEL = get_embedding_model()

class SchemaEmbedder:
    def __init__(self, data_dict_path='data/data_dictionary.xlsx'):
        try:
            self.model = SentenceTransformer(EMBED_MODEL)
            print(f"Using embedding model: {EMBED_MODEL}")
        except Exception as e:
            print(f"Warning: Could not load embedding model {EMBED_MODEL}: {e}")
            print("Falling back to basic text matching")
            self.model = None
        
        self.data_dict = pd.read_excel(data_dict_path) if os.path.exists(data_dict_path) else pd.DataFrame()
        self.embeddings = None
        self.texts = []
        # Compute embeddings once during initialization
        if not self.data_dict.empty and self.model is not None:
            self._embed_schema()

    def _embed_schema(self):
        """Compute embeddings once and cache them"""
        if self.model is None:
            return
        self.texts = [f"{row['Table']} {row['Column']} {row['Column Description']}" for _, row in self.data_dict.iterrows()]
        self.embeddings = self.model.encode(self.texts, convert_to_tensor=True)
        print(f"Embedded {len(self.texts)} schema items (cached for reuse)")

    def search(self, question, top_k=5):
        """Search using cached embeddings - no recomputation needed"""
        if self.embeddings is None or self.data_dict.empty:
            # Fallback to basic text matching if no embeddings
            return self._basic_search(question, top_k)
        q_emb = self.model.encode([question], convert_to_tensor=True)
        hits = util.semantic_search(q_emb, self.embeddings, top_k=top_k)[0]
        results = [self.data_dict.iloc[hit['corpus_id']] for hit in hits]
        return results
    
    def _basic_search(self, question, top_k=5):
        """Fallback search using basic text matching"""
        if self.data_dict.empty:
            return []
        question_lower = question.lower()
        scores = []
        for idx, row in self.data_dict.iterrows():
            text = f"{row['Table']} {row['Column']} {row['Column Description']}".lower()
            score = sum(1 for word in question_lower.split() if word in text)
            scores.append((score, idx))
        scores.sort(reverse=True)
        return [self.data_dict.iloc[idx] for score, idx in scores[:top_k] if score > 0] 