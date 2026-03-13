# Challenge 01 — Decision Log

## TODO 1: Elasticsearch Index Mapping (`create_index`)

**Qué se hizo:**
Se completó el mapping del índice agregando los campos faltantes extraídos de la estructura de los archivos JSON de libros.

**Por qué:**
Elasticsearch requiere que los tipos de los campos estén definidos antes de indexar documentos. Se eligieron los tipos según el uso esperado de cada campo:
- `text` para `title` y `description`, ya que son campos de búsqueda full-text que requieren tokenización.
- `keyword` para `authors`, `subjects` y `language`, ya que se usan para filtros y agregaciones exactas.
- `integer` para `first_publish_year`, al ser un valor numérico.
- `dense_vector` con `dims: 384` para `embedding`, que corresponde a la dimensión de salida del modelo `all-MiniLM-L6-v2`.

---

## TODO 2: Generación de embeddings (`generate_embedding`)

**Qué se hizo:**
Se implementó la función utilizando el modelo `SentenceTransformer` ya inicializado globalmente (`model`). Se convierte el resultado a `List[float]` con `.tolist()`.

**Por qué:**
El modelo `all-MiniLM-L6-v2` es un modelo ligero y eficiente para generar embeddings semánticos de oraciones. `model.encode()` devuelve un `numpy.ndarray`, por lo que `.tolist()` es necesario para la compatibilidad con Elasticsearch.

---