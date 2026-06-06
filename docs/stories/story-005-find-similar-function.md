---
id: RADAR-005
title: Tool find_similar_function
status: todo
---

## Historia

Como agente de IA, necesito una tool `find_similar_function` que dado un fragmento de código o descripción de lo que quiero implementar me devuelva las funciones existentes en el repo que hacen lo mismo, para reutilizarlas en lugar de duplicarlas.

## Criterios de aceptación

- [ ] Acepta como input: código fuente de una función O descripción en lenguaje natural de su intención
- [ ] Devuelve una lista de hasta 5 candidatos, cada uno con: `name`, `file`, `start_line`, `source_code`, `similarity_score`
- [ ] Si no hay candidatos con similitud > 0.7, devuelve lista vacía (no fuerza resultados)
- [ ] El schema de la tool está correctamente tipado para que el LLM pueda llamarla sin ambigüedad
- [ ] Incluye ejemplos de uso en la descripción de la tool para guiar al agente
- [ ] Latencia < 150ms sobre índice cargado en memoria

## Tareas técnicas

1. Definir el schema JSON de la tool:
   ```json
   {
     "name": "find_similar_function",
     "description": "Busca funciones en el repo que hagan lo mismo que el código o descripción dado. Llamar antes de implementar cualquier función nueva.",
     "input_schema": {
       "query": "string  // código fuente o descripción en lenguaje natural",
       "k": "integer  // máximo de resultados (default: 5)"
     }
   }
   ```
2. Implementar el handler: embeddear el query → buscar en el índice → filtrar por score > 0.7 → retornar
3. Manejar el caso de índice vacío o no inicializado con error claro
4. Escribir tests de integración: query conocido → verificar que la función correcta aparece en top-3
5. Documentar ejemplos de uso para el agente en la descripción de la tool

## Dependencias

- RADAR-002 (embedding del query)
- RADAR-003 (búsqueda en el índice)
- RADAR-004 (registro en el servidor MCP)

## Stack

```
mcp  # registro y exposición de la tool
```
