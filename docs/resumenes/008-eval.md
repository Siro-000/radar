# RADAR-008: eval/eval.py — precision/recall + calibración

Script que corre el engine sobre el held-out set y reporta precision, recall y F1 al threshold configurado. Acepta `--threshold` para probar valores distintos y `--sweep` para barrer el rango completo y encontrar el óptimo. Es donde se calibra el threshold de detección — no a través del agente sino contra ground truth conocido. El output incluye un desglose por caso y un resumen con el threshold recomendado.
