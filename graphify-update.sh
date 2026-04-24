#!/bin/bash
# graphify-update.sh — Rebuild the knowledge graph (AST-only, zero LLM cost)
# Run after making code changes to keep graphify-out/ current.

VENV="/Users/tp/Documents/Playground/graphify-venv/bin/graphify"

if [ ! -f "$VENV" ]; then
  echo "ERROR: graphify venv not found at $VENV"
  echo "Run: python3.12 -m venv /Users/tp/Documents/Playground/graphify-venv && /Users/tp/Documents/Playground/graphify-venv/bin/pip install /Users/tp/Documents/Playground/graphify"
  exit 1
fi

cd "$(dirname "$0")"
echo "Updating knowledge graph..."
"$VENV" update .
echo "Done. Open graphify-out/graph.html in a browser to explore."
