# RADAR-011: Tests N0 / N2 / N3

Tres tests deterministas que validan el sistema sin pasar por el agente. **N0 (smoke)**: indexa el seed_repo, consulta con un duplicado conocido y verifica que aparece en los resultados. **N2 (determinism)**: llama a `find_similar_function` dos veces con el mismo input y verifica que los scores, el verdict y el orden son idénticos — este es el "determinism cherry" del pitch. **N3 (contract)**: verifica que el shape de la respuesta cumple exactamente el contrato congelado.
