---
id: RADAR-002
title: Embeddings de intención algorítmica
status: todo
---

## Historia

Como motor de Radar, necesito convertir cada función extraída en un vector que capture qué hace algorítmicamente —no cómo está escrita—, para poder comparar funciones por similitud semántica independientemente de su sintaxis.

## Criterios de aceptación

- [ ] Dado un objeto `Function`, produce un vector de dimensión fija (ej. 1536)
- [ ] Dos funciones que hacen lo mismo pero están escritas diferente producen vectores con similitud coseno > 0.85
- [ ] Dos funciones que hacen cosas distintas producen similitud < 0.5
- [ ] Soporta procesamiento en batch para repos grandes (sin llamar la API función por función)
- [ ] El embedding se genera a partir del `source_code` + `name` como contexto
- [ ] Incluye tests con pares de funciones equivalentes y no equivalentes

## Tareas técnicas

1. Integrar modelo de embeddings (OpenAI `text-embedding-3-small` o `sentence-transformers/all-MiniLM-L6-v2` local)
2. Implementar `EmbeddingService.embed(function: Function) -> list[float]`
3. Implementar `EmbeddingService.embed_batch(functions: list[Function]) -> list[list[float]]`
4. Definir el template del input: `"Function {name}:\n{source_code}"` 
5. Cachear embeddings por hash del source_code para evitar re-embeddear lo que no cambió
6. Escribir tests de similitud con casos concretos

## Dependencias

- RADAR-001 (necesita el modelo `Function`)

## Stack

```
openai  # o sentence-transformers si se prefiere local
numpy
hashlib  # para el cache por hash
```
