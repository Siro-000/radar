# RADAR-002: engine/extract.py — extractor de funciones

Usa tree-sitter para recorrer archivos Java y extraer todos los métodos con sus metadatos: nombre, archivo, líneas de inicio y fin, código fuente completo y signature (la línea con visibilidad + tipo de retorno + nombre + parámetros). Soporta métodos de instancia, métodos estáticos y constructores. Ignora métodos de menos de 4 líneas por ser demasiado triviales, y skipea archivos con errores de sintaxis sin crashear.
