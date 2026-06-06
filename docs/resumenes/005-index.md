# RADAR-005: engine/index.py — FAISS index + metadata store

Construye, persiste y consulta el índice vectorial. Usa FAISS con similitud coseno para encontrar las funciones más cercanas a un vector de consulta. Junto al índice FAISS guarda un metadata store (SQLite o JSON) que mapea cada vector a su `Function` record completo, incluyendo `summary` e `import_statement` precomputados. Expone tres operaciones: `build`, `load` y `search`.
