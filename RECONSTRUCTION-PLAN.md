# Reconstruction Plan

## First Principles

1. Chat UI IS the product
2. Conversation persistence = append to JSONL
3. System prompt = intellectual property
4. 70% of codebase is over-engineering

## Cut List (delete entirely)

| Target | Reason | Files |
|--------|--------|-------|
| `dify/` | Unused Dify fork, 1643 files | ~1643 |
| `assisent/mcp/` | MCP service registry, client, monitor, cache, rate limiter | 5 |
| `assisent/manage_service.py` | Service manager (start/stop/monitor) | 1 |
| `assisent/scripts/` | Windows autostart scheduled task | 1 |
| `assisent/web/console.html` | MCP admin console UI | 1 |
| `assisent/web/console.js` | MCP admin console logic | 1 |
| `assisent/web/console.css` | MCP admin console styles | 1 |
| `assisent/.claude/` | Claude skills + MCP config | ~8 |
| `assisent/config/mcp_services.json` | MCP service registry config | 1 |
| `assisent/config/service_config.json` | Service manager config | 1 |

## Modify List

| File | Change |
|------|--------|
| `assisent/server.py` | Remove MCP imports, routes, duplicate pydantic import. Keep: /health, /chat, /history, static mount |
| `README.md` | Rewrite to reflect minimal architecture |
| `.gitignore` | Add `conversations/` directory |

## Keep List (irreducible core)

| File | Purpose |
|------|---------|
| `assisent/server.py` | FastAPI: chat + history + static |
| `assisent/config/ai-persona.md` | System prompt (IP) |
| `assisent/web/index.html` | Chat UI |
| `assisent/web/app.js` | Chat logic |
| `assisent/web/styles.css` | Chat styles |
| `.github/workflows/ci.yml` | CI pipeline |
| `FIRST-PRINCIPLES-RECONSTRUCTION.md` | This document |

## Target: ~200 lines of code total
