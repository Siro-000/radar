---
id: RADAR-001
title: Parser de funciones
status: todo
---

## Historia

Como motor de Radar, necesito recorrer un repositorio y extraer cada función como unidad atómica, para poder procesarlas individualmente en los pasos de embedding e indexación.

## Criterios de aceptación

- [ ] Dado un path de repositorio, el parser recorre todos los archivos del lenguaje soportado
- [ ] Por cada función encontrada extrae: `name`, `file`, `start_line`, `end_line`, `source_code`
- [ ] Soporta Python como lenguaje inicial (extensible a otros)
- [ ] Ignora funciones de menos de 3 líneas (getters triviales, lambdas)
- [ ] El output es una lista de objetos `Function` serializables a JSON
- [ ] Incluye tests con un repo de fixture pequeño

## Tareas técnicas

1. Instalar y configurar `tree-sitter` con la gramática de Python
2. Implementar `FunctionExtractor` que recorre el AST y extrae nodos de tipo `function_definition`
3. Definir el modelo de datos `Function(name, file, start_line, end_line, source_code)`
4. Implementar CLI mínima: `radar parse <repo_path>` → imprime JSON
5. Escribir tests unitarios con fixtures de código Python real

## Dependencias

Ninguna — es la historia base del motor.

## Stack

```
tree-sitter
tree-sitter-python
pydantic  # para el modelo Function
```
