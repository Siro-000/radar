#!/usr/bin/env python3
"""Lee stream-json de claude desde stdin, muestra el output del agente
en tiempo real y al final imprime un resumen de tokens y costo."""

import json
import sys

turns = 0
input_tokens = cache_read = cache_creation = output_tokens = 0
cost_usd = 0.0
duration_ms = 0

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        obj = json.loads(line)
    except json.JSONDecodeError:
        print(line)
        continue

    t = obj.get("type", "")

    # Muestra el texto que escribe el agente
    if t == "assistant":
        for block in obj.get("message", {}).get("content", []):
            if block.get("type") == "text":
                print(block["text"], end="", flush=True)
            elif block.get("type") == "tool_use":
                print(f"\n[tool] {block.get('name')}({json.dumps(block.get('input', {}), ensure_ascii=False)})", flush=True)

    elif t == "tool_result":
        content = obj.get("content", "")
        if isinstance(content, list):
            for c in content:
                if c.get("type") == "text":
                    print(f"[result] {c['text'][:200]}", flush=True)
        elif isinstance(content, str):
            print(f"[result] {content[:200]}", flush=True)

    elif t == "result":
        u = obj.get("usage", {})
        turns = obj.get("num_turns", 0)
        duration_ms = obj.get("duration_ms", 0)
        input_tokens = u.get("input_tokens", 0)
        cache_read = u.get("cache_read_input_tokens", 0)
        cache_creation = u.get("cache_creation_input_tokens", 0)
        output_tokens = u.get("output_tokens", 0)
        cost_usd = obj.get("total_cost_usd", 0.0)

total = input_tokens + cache_read + cache_creation + output_tokens

print("\n")
print("=" * 50)
print("  TOKENS GASTADOS")
print("=" * 50)
print(f"  turns            : {turns:,}")
print(f"  input tokens     : {input_tokens:,}")
print(f"  cache read       : {cache_read:,}")
print(f"  output tokens    : {output_tokens:,}")
print(f"  total tokens     : {total:,}")
print(f"  costo (USD)      : ${cost_usd:.4f}")
print(f"  tiempo           : {duration_ms / 1000:.1f}s")
print("=" * 50)
