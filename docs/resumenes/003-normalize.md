# RADAR-003: engine/normalize.py — canonicalización

Transforma el código Java antes de embeddearlo para mejorar el recall: elimina comentarios de línea (`//`), de bloque (`/* */`) y Javadoc (`/** */`), y renombra las variables locales a `var0`, `var1`, `var2`... en orden de aparición. El objetivo es que dos métodos con la misma lógica pero nombres de variables distintos produzcan vectores similares. Preserva nombres de método y parámetros porque son parte de la semántica. Usa tree-sitter-java para parsear, no regex.
