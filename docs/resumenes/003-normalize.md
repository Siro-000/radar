# RADAR-003: engine/normalize.py — canonicalización

Transforma el código fuente antes de embeddearlo para mejorar el recall: elimina comentarios y docstrings, y renombra las variables locales a `var_0`, `var_1`, `var_2`... en orden de aparición. El objetivo es que dos funciones con la misma lógica pero nombres de variables distintos produzcan vectores similares. Preserva nombres de función y parámetros porque son parte de la semántica.
