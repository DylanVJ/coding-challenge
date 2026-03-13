import os
import streamlit as st
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer

ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")
INDEX_NAME = os.getenv("INDEX_NAME", "documents")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

@st.cache_resource
def load_model():
    return SentenceTransformer(EMBEDDING_MODEL)

@st.cache_resource
def get_es_client():
    return Elasticsearch(ELASTICSEARCH_URL)

es = get_es_client()
model = load_model()

st.title("Book Semantic Search")
st.write("Search through books using natural language.")

query = st.text_input("What kind of book are you looking for?")
k = st.slider("Number of results", min_value=1, max_value=10, value=5)

if query:
    query_vector = model.encode(query).tolist()

    results = es.search(
        index=INDEX_NAME,
        knn={
            "field": "embedding",
            "query_vector": query_vector,
            "k": k,
            "num_candidates": 50
        },
        source=["title", "description", "authors", "first_publish_year"]
    )

    hits = results["hits"]["hits"]

    if not hits:
        st.warning("No results found.")
    else:
        for hit in hits:
            source = hit["_source"]
            score = hit["_score"]
            with st.container(border=True):
                st.subheader(source.get("title", "Unknown"))
                authors = source.get("authors", [])
                year = source.get("first_publish_year")
                if authors:
                    st.caption(f"{', '.join(authors)} — {year or 'Unknown year'}")
                st.write(source.get("description", ""))
                st.caption(f"Relevance score: {score:.4f}")