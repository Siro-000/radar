# RADAR-001: Skeleton + tipos del contrato

Crea la base del proyecto: el `pyproject.toml` con todas las dependencias, la estructura de carpetas (`engine/`, `adapters/`, `eval/`, `data/`, `tests/`, `artifacts/`) y los modelos pydantic que definen el contrato congelado (`Function`, `Match`, `QueryResult`). Todo el código posterior depende de los tipos definidos acá. También verifica que el modelo de embeddings levanta y corre en CPU.
