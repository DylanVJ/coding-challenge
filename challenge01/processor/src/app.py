import json
import os
from pathlib import Path
from typing import List, Dict, Any

from elasticsearch import Elasticsearch
from sentence_splitter import SentenceSplitter
from sentence_transformers import SentenceTransformer

ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")
INPUT_DIR = os.getenv("INPUT_DIR", "/app/input")
INDEX_NAME = os.getenv("INDEX_NAME", "documents")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# Simple sentence embeddings model
model = SentenceTransformer(EMBEDDING_MODEL)

# Sentence Splitter
splitter = SentenceSplitter(language="en")


def create_index(es: Elasticsearch, index_name: str) -> None:
    # Create the index if it does not exist.
    if es.indices.exists(index=index_name):
        return

    mapping = {
        "mappings": {
            "properties": {
                "doc_id": {"type": "keyword"},
                "chunk_id": {"type": "keyword"},
                "title": {"type": "text"},
                "description": {"type": "text"},
                "authors": {"type": "keyword"},
                "first_publish_year": {"type": "integer"},
                "subjects": {"type": "keyword"},
                "language": {"type": "keyword"},
                "embedding": {
                    "type": "dense_vector",
                    "dims": 384
                }
            }
        }
    }

    es.indices.create(index=index_name, body=mapping)
    print(f"Created index: {index_name}")


def load_json_files(input_dir: str) -> List[Dict[str, Any]]:
    documents = []
    for path in Path(input_dir).glob("*.json"):
        with open(path, "r", encoding="utf-8") as f:
            documents.append(json.load(f))
    return documents


def split_into_chunks(text: str, max_sentences: int = 5) -> List[str]:
    # Split the text into small chunks.
    sentences = splitter.split(text)
    chunks = []

    for i in range(0, len(sentences), max_sentences):
        chunk = " ".join(sentences[i:i + max_sentences]).strip()
        if chunk:
            chunks.append(chunk)
    return chunks


def generate_embedding(text: str) -> List[float]:
    # result is converted to a plain Python list for Elasticsearch
    return model.encode(text).tolist()


def proccess_documents(document: Dict[str, Any]) -> List[Dict[str, Any]]:
    doc_id = document.get("id")
    title = document.get("title", "")
    description = document.get("description", "")
    authors = document.get("authors", [])
    first_publish_year = document.get("first_publish_year")
    language = document.get("language", [])

    # normalize subjects to a consistent casing before indexing
    subjects = []
    for subject in document.get("subjects", []):
        subjects.append(subject.capitalize())

    if not doc_id or not description:
        raise ValueError("Document must contain at least 'id' and 'description'")
    
    # remove non-ASCII characters to avoid issues during embedding and indexing
    title = title.encode("ascii", "ignore").decode("ascii")
    description = description.encode("ascii", "ignore").decode("ascii")

    chunks = split_into_chunks(description)
    result = []

    for idx, chunk in enumerate(chunks):
        embedding = generate_embedding(chunk)
        result.append({
            "doc_id": str(doc_id),
            "chunk_id": f"{doc_id}-{idx}",
            "title": title,
            "description": chunk,
            "authors": authors,
            "first_publish_year": first_publish_year,
            "subjects": subjects,
            "language": language,
            "embedding": embedding
        })

    return result


def index_documents(es: Elasticsearch, index_name: str, docs: List[Dict[str, Any]]) -> None:
    for doc in docs:
        es.index(index=index_name, id=doc["chunk_id"], document=doc)


def semantic_search(es: Elasticsearch, index_name: str, query_text: str, k: int = 3) -> Dict[str, Any]:
    # Query to perform semantic search
    query_vector = generate_embedding(query_text)

    return es.search(
        index=index_name,
        knn={
            "field": "embedding",
            "query_vector": query_vector,
            "k": k,
            "num_candidates": 10
        },
        source=["doc_id", "chunk_id", "title", "description"]
    )


def main() -> None:
    es = Elasticsearch(ELASTICSEARCH_URL)
    create_index(es, INDEX_NAME)
    documents = load_json_files(INPUT_DIR)

    if not documents:
        print("No JSON files found.")
        return

    for document in documents:
        built_docs = proccess_documents(document)
        index_documents(es, INDEX_NAME, built_docs)

    print("Semantic search: examples")

    queries = [
        "a hobbit leaves home on an unexpected journey with dwarves and a wizard",
        "children step through a magical portal into a world ruled by an evil witch",
        "a young orphan grows up to become the greatest wizard of his generation",
        "a fellowship embarks on a dangerous mission to destroy a ring of ultimate power",
        "a dragon rider fights to save her world from an ancient evil rising again",
    ]

    for query in queries:
        print(f"Query: {query}")
        results = semantic_search(es, INDEX_NAME, query)
        for hit in results["hits"]["hits"]:
            source = hit["_source"]
            print(f"  - {source.get('title')} (score: {hit['_score']:.4f})")
        print()

if __name__ == "__main__":
    main()