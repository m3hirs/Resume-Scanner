import streamlit as st
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


@st.cache_resource(show_spinner="Loading embedding model...")
def get_model() -> SentenceTransformer:
    """Load and cache the Sentence Transformer model."""
    return SentenceTransformer("all-MiniLM-L6-v2")


def compute_similarity(text1: str, text2: str) -> float:
    """Compute semantic similarity between two texts.

    Returns:
        A score between 0 and 100.
    """
    model = get_model()
    embeddings = model.encode([text1, text2], show_progress_bar=False)
    score = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    # Clamp to [0, 1] then scale to percentage
    return round(max(0.0, min(1.0, float(score))) * 100, 1)
