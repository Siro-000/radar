# RADAR-005: engine/index.py — FAISS index + metadata store JSON

Construye, persiste y consulta el índice vectorial. Usa FAISS con similitud coseno para encontrar los métodos más cercanos a un vector de consulta. Junto al índice FAISS (`index.faiss`) guarda un archivo `metadata.json` que mapea cada posición FAISS al `Function` record completo, incluyendo `summary` e `import_statement` precomputados. Se eligió JSON sobre SQLite por ser simple, sin esquema y legible para debugging. Expone tres operaciones: `build`, `load` y `search`.
