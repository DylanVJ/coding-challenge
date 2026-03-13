# Challenge 01 — Decision Log

## TODO 1: Elasticsearch Index Mapping (`create_index`)

The mapping was incomplete — it only had `doc_id`, `chunk_id` and `embedding`.
I reviewed the JSON structure in `data/books` and added the missing fields with
the appropriate types:

- `title` and `description` as `text`, because Elasticsearch needs to tokenize
  them to support full-text search.
- `authors`, `subjects` and `language` as `keyword`, since they are exact values
  used for filtering, not for searching within the text.
- `first_publish_year` as `integer`, it's just a number.
- `embedding` was already there, with `dims: 384` which matches the output size
  of the `all-MiniLM-L6-v2` model.

## TODO 2: Embedding generation (`generate_embedding`)

The model was already initialized at the top of the file as a global variable `model`.
It was just a matter of using it: `model.encode(text)` generates the vector, and
`.tolist()` converts it from a numpy array to a plain Python list, which is what
Elasticsearch expects.

## TODO 3: Document processing (`proccess_documents`)

The function had the base structure but was missing several things:

- It only included `title` and `description` in each chunk, ignoring the rest of
  the document fields. Added `authors`, `first_publish_year`, `subjects` and
  `language` so every indexed document is complete.
- The Open Library JSONs contain many special characters (accents, Cyrillic,
  Chinese, etc.). Applied encode/decode ASCII to clean them up before processing,
  avoiding issues in the embedding pipeline.
- Subjects came in inconsistent casing. Applied `capitalize()` to each one to
  normalize them before indexing.

## TODO 4: Indexing documents (`index_documents`)

Straightforward loop over the list of processed chunks, calling `es.index()` for
each one. Used `chunk_id` as the document ID in Elasticsearch so each chunk has
a unique, deterministic identifier. This also means re-running the processor
won't create duplicates — it will just overwrite existing documents.

## TODO 5: Semantic search queries (`main`)

Added five queries inspired by classic fantasy stories I enjoy. Each query
describes a familiar plot in plain natural language rather than using the
actual book title, which is a good way to test whether the semantic search
is finding the right books based on meaning rather than keywords.
Results are printed with the book title and the relevance score to make it
easy to evaluate the quality of the results visually.