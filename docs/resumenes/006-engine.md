# RADAR-006: engine/config.py + engine/engine.py — find_similar_function

Es el corazón del sistema: implementa `find_similar_function()` con el contrato completo. Toma el código de entrada, lo normaliza, lo embeddea, busca en el índice y aplica los thresholds definidos en `config.py` para decidir el `verdict` (`duplicate`, `similar` o `novel`). Construye la respuesta completa con `query_id`, `verdict` y todos los campos de cada `Match`. Es determinista: el mismo input siempre produce el mismo output.
