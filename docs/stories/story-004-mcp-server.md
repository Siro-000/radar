---
id: RADAR-004
title: Servidor MCP
status: todo
---

## Historia

Como agente de IA (Claude Code, Cursor, etc.), necesito un servidor MCP que exponga el motor de Radar como una tool consultable, para poder integrarlo en mi flujo de trabajo sin infraestructura adicional.

## Criterios de aceptación

- [ ] El servidor implementa el protocolo MCP (Model Context Protocol)
- [ ] Se levanta localmente con un solo comando: `radar serve`
- [ ] Expone la tool `find_similar_function` (ver RADAR-005)
- [ ] Responde en < 200ms para queries sobre repos indexados
- [ ] El servidor puede ser configurado en `claude_desktop_config.json` / `.mcp.json`
- [ ] Incluye instrucciones de configuración para Claude Code y Cursor

## Tareas técnicas

1. Instalar y configurar el SDK oficial de MCP para Python (`mcp`)
2. Implementar `RadarMCPServer` que wrappea el motor (Parser + Embeddings + Index)
3. Registrar la tool `find_similar_function` con su schema JSON
4. Implementar el handler de la tool (delega a RADAR-005)
5. Agregar comando CLI: `radar serve [--port 8080] [--index-path ./radar-index]`
6. Escribir el archivo de configuración de ejemplo para Claude Code

## Dependencias

- RADAR-001, RADAR-002, RADAR-003 (el motor completo debe estar operativo)

## Stack

```
mcp  # SDK oficial de Model Context Protocol
fastapi  # para el transport HTTP/SSE
uvicorn
```
