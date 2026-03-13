# Challenge 01 — Solution

## Overview

This solution implements a semantic search system over a dataset of 1,200+ books.
Each book description is split into sentence chunks, embedded with a
`sentence-transformers/all-MiniLM-L6-v2` model (384 dimensions), and indexed into
Elasticsearch using dense vector fields. A Streamlit UI allows querying the index
in natural language.

## Architecture

| Service         | Port  | Description                                           |
|-----------------|-------|-------------------------------------------------------|
| `elasticsearch` | 9200  | Stores book chunks with vector embeddings             |
| `kibana`        | 5601  | Dev-tools console for manual inspection               |
| `processor`     | —     | One-shot container: processes JSONs and indexes them  |
| `ui`            | 8501  | Streamlit interface for natural-language book search  |

## How to Run

```bash
docker compose up --build
```

- Processor logs will show `Indexed N chunks from M documents.`
- UI is available at [http://localhost:8501](http://localhost:8501)
- Kibana is available at [http://localhost:5601](http://localhost:5601)

## TODOs Completed

### TODO 1 — `create_index` mapping

Added all missing fields to the Elasticsearch mapping:

| Field               | Type           | Reason                                    |
|---------------------|----------------|-------------------------------------------|
| `title`             | `text`         | Full-text tokenization                    |
| `description`       | `text`         | Full-text tokenization                    |
| `authors`           | `keyword`      | Exact-match filtering                     |
| `subjects`          | `keyword`      | Exact-match filtering                     |
| `language`          | `keyword`      | Exact-match filtering                     |
| `first_publish_year`| `integer`      | Numeric range filtering                   |
| `embedding`         | `dense_vector` | 384-dim vector for cosine similarity kNN  |

### TODO 2 — `generate_embedding`

```python
return model.encode(text).tolist()
```

`model` is a globally initialized `SentenceTransformer`. `.tolist()` converts the
numpy array to a plain Python list, which is what Elasticsearch expects.

### TODO 3 — `proccess_documents`

- Extracted all fields: `authors`, `first_publish_year`, `subjects`, `language`.
- Applied ASCII normalization (`encode/decode`) to remove Cyrillic, accented, and
  other non-ASCII characters that could cause issues in the embedding pipeline.
- Applied `capitalize()` to each subject for consistent casing.
- Batch-encoded all chunks of a document in a single `model.encode(chunks)` call
  (see Optional 1).

### TODO 4 — `index_documents`

Used the `elasticsearch.helpers.bulk()` API to index all chunks in one request,
reducing HTTP overhead significantly compared to calling `es.index()` in a loop.

```python
actions = [{"_index": index_name, "_id": doc["chunk_id"], "_source": doc} for doc in docs]
bulk(es, actions)
```

Using `chunk_id` as `_id` makes re-runs idempotent — existing documents are
overwritten, not duplicated.

### TODO 5 — Semantic search queries

Five fantasy-themed queries that describe familiar plots without naming the book:

```
"a hobbit leaves home on an unexpected journey with dwarves and a wizard"
"children step through a magical portal into a world ruled by an evil witch"
"a young orphan grows up to become the greatest wizard of his generation"
"a fellowship embarks on a dangerous mission to destroy a ring of ultimate power"
"a dragon rider fights to save her world from an ancient evil rising again"
```

## Optional Improvements

### Optional 1 — Batching

Two performance improvements were made:

1. **Batch embedding**: replaced `generate_embedding(chunk)` per chunk with a
   single `model.encode(chunks)` call for all chunks of a document at once.
2. **Bulk indexing**: replaced per-document `es.index()` calls with a single
   `bulk(es, actions)` call after accumulating all chunks across all documents.

Both changes drastically reduce wall-clock time on large datasets.

### Optional 2 — Streamlit UI

A `ui/` service was added with:

- A text input for the natural-language query.
- A slider to choose the number of results (1–10).
- Result cards showing title, authors, year, matched description chunk and
  relevance score.
- `@st.cache_resource` on both the ES client and the model to avoid
  reloading them on every page interaction.

**Key fix**: pinned `elasticsearch==8.15.1` in `ui/requirements.txt` to match the
server version. The auto-installed v9 client sent incompatible headers and caused
a `BadRequestError(400, media_type_header_exception)`.

## Dataset

- **Source**: Open Library JSON exports
- **Books**: 1,200+
- **Chunks indexed**: ~3,600 (average ~3 chunks per book description)
- **Embedding model**: `sentence-transformers/all-MiniLM-L6-v2` (384 dims)
