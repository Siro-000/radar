# Radar

Semantic recall layer that prevents AI agents from duplicating logic that already exists in your codebase.

## What it does

AI agents generate code without seeing the full codebase they're working on. The measurable result: they rewrite logic that already exists instead of reusing it, inflating repositories with duplication that then needs to be maintained.

Radar understands *what* each function in a repository does — not how it's written — and exposes that knowledge where code decisions are made.

## How it works

Funnel architecture (retrieve-then-rerank):

1. **Vector lookup** — reduces millions of functions to a handful of candidates in milliseconds, deterministically
2. **LLM rerank** (optional) — judges whether candidates are real duplicates

## Surfaces

- **CI gate** — blocks PRs with detected duplication
- **IDE / agent integration** — before generating a function, checks if the logic already exists

## Status

Work in progress.
