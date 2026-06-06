---
id: RADAR-003
title: Índice vectorial
status: done
---

## Historia

Como motor de Radar, necesito indexar los vectores de todas las funciones del repo y exponer una búsqueda por similitud que devuelva candidatos en milisegundos, para que el paso de consulta sea determinístico y barato.

## Criterios de aceptación

- [ ] Dado un repo parseado y embeddeado, el índice almacena todos los vectores con su metadata asociada (`Function`)
- [ ] Una búsqueda por vector retorna los top-k candidatos más similares con su score de similitud coseno
- [ ] El índice persiste en disco y se puede recargar sin re-indexar todo
- [ ] Soporta actualización incremental: agregar nuevas funciones sin rebuilding completo
- [ ] La búsqueda de top-5 sobre un repo de 10.000 funciones tarda < 100ms
- [ ] Incluye tests de inserción, búsqueda y persistencia

## Tareas técnicas

1. Integrar `ChromaDB` como vector store (local, sin infraestructura externa)
2. Implementar `VectorIndex.add(function: Function, embedding: list[float])`
3. Implementar `VectorIndex.search(query_embedding: list[float], k: int) -> list[SearchResult]`
4. Definir `SearchResult(function: Function, score: float)`
5. Implementar persistencia: `VectorIndex.save(path)` / `VectorIndex.load(path)`
6. Implementar `VectorIndex.add_batch(...)` para la indexación inicial
7. Escribir tests de round-trip: indexar → buscar → verificar que los más similares aparecen primero

## Dependencias

- RADAR-001 (modelo `Function`)
- RADAR-002 (embeddings) — paralizable: el contrato de datos es suficiente para diseñar el índice

## Stack

```
chromadb
```
