# RADAR-002: engine/extract.py — extractor de funciones

Usa tree-sitter para recorrer archivos Python y extraer todas las funciones con sus metadatos: nombre, archivo, líneas de inicio y fin, código fuente completo y signature (la línea `def ...`). Soporta funciones top-level y métodos de clase. Ignora funciones de menos de 4 líneas por ser demasiado triviales, y skipea archivos con errores de sintaxis sin crashear.
