# RADAR-004: engine/embed.py — wrapper del embedder

Es el único lugar del código que importa el modelo de embeddings (`jinaai/jina-embeddings-v2-base-code`). Expone dos funciones: `embed()` para una sola función y `embed_batch()` para procesar muchas a la vez de forma eficiente. Incluye cache en memoria por hash del código fuente para no re-embeddear el mismo contenido dos veces. Si en el futuro se quiere cambiar el modelo, este es el único archivo que se toca.
