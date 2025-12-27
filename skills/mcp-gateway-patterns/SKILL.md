---
name: mcp-gateway-patterns
description: MCP Gateway design patterns for both Agent Gateway and Subprocess isolation. Use when designing MCP integrations.
allowed-tools: ["Read", "Write", "Grep", "Glob"]
---

# MCP Gateway Patterns

## Problem

Heavy MCP servers (Serena, SAP2000, etc.) have large tool schemas that consume context tokens. Two isolation strategies exist:

1. **Agent Gateway**: Native Claude subagent as central MCP access point
2. **Subprocess Isolation**: Separate Claude CLI process loads MCP on-demand

## Strategy Selection

```
┌─────────────────────────────────────────────────────────┐
│ When to use Agent Gateway (serena-refactor style)       │
├─────────────────────────────────────────────────────────┤
│ • Frequently used MCP                                   │
│ • Need workflow state continuity                        │
│ • Complex multi-step operations                         │
│ • Token overhead acceptable                             │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ When to use Subprocess Isolation (enclave style)        │
├─────────────────────────────────────────────────────────┤
│ • Rarely used but very large MCP                        │
│ • Main session must have zero MCP token overhead        │
│ • Stateless operations preferred                        │
│ • Can tolerate session startup latency                  │
└─────────────────────────────────────────────────────────┘
```

---

## 2-Layer Protocol Architecture

### Layer 1: Intent (Common)

Orchestrator interprets uniformly across all MCPs:

| Intent | Description | Default Effect |
|--------|-------------|----------------|
| QUERY | Search/lookup/explore | READ_ONLY |
| ANALYZE | Interpret/summarize/impact analysis | READ_ONLY |
| GENERATE | Create artifacts (no file save) | READ_ONLY |
| MODIFY | Change files/code/state | MUTATING |
| EXECUTE | External system invocation | EXTERNAL_EXEC |

### Layer 2: Action (MCP-specific)

Each MCP defines its own actions. Examples:
- Serena: `find_symbol`, `rename_symbol`, `replace_symbol_body`
- SAP2000: `search_oapi`, `generate_py_wrapper`, `run_analysis`

### Auxiliary Fields

| Field | Values | Purpose |
|-------|--------|---------|
| effect | READ_ONLY, MUTATING, EXTERNAL_EXEC | Risk level for timeout/retry/permission |
| artifact | TEXT, JSON, CODE_PY, CODE_TS, PATCH, BINARY | Output format for post-processing |

---

## Request Schema

```json
{
  "intent": "QUERY|ANALYZE|GENERATE|MODIFY|EXECUTE",
  "action": "mcp_specific_action_name",
  "effect": "READ_ONLY|MUTATING|EXTERNAL_EXEC",
  "artifact": "TEXT|JSON|CODE_PY|CODE_TS|PATCH|BINARY",
  "params": { },
  "constraints": {
    "timeout_ms": 300000,
    "retry_count": 0,
    "isolation": "agent|subprocess"
  },
  "context": {
    "caller": "optional_caller_name",
    "project_root": "/path/to/project"
  }
}
```

## Response Schema

```json
{
  "ok": true,
  "request": { "intent": "...", "action": "...", "effect": "..." },
  "result": {
    "artifact_type": "JSON",
    "data": { },
    "affected_files": [],
    "affected_symbols": []
  },
  "meta": {
    "duration_ms": 1234,
    "mcp_name": "serena",
    "isolation_used": "agent"
  }
}
```

Error case:
```json
{
  "ok": false,
  "error": {
    "type": "TIMEOUT|MCP_ERROR|VALIDATION|PERMISSION|UNKNOWN",
    "message": "description",
    "recoverable": true,
    "suggestion": "recovery hint"
  }
}
```

---

## Agent Gateway Template

See `references/agent-gateway-template.md` for full implementation pattern.

Core structure:
```yaml
---
name: {mcp}-gateway
description: Central gateway for {MCP} tools
tools: [mcp__{mcp}__{tool1}, mcp__{mcp}__{tool2}, ...]
model: sonnet
---
```

Gateway responsibilities:
1. **Context activation** - Ensure MCP project is initialized
2. **Pre-validation** - Verify targets exist before modification
3. **Impact assessment** - Check reference counts for MODIFY operations
4. **Atomic response** - One complete structured response per request

---

## Subprocess Isolation Template

See `references/subprocess-gateway.md` for Python implementation.

Core pattern:
```bash
claude --mcp-config {mcp}.mcp.json -p "..." --output-format json
```

Key requirements:
1. **JSON forced** - Always output valid JSON even on failure
2. **Timeout** - Default 300s (5 minutes)
3. **Minimal context** - Pass only necessary info to subprocess
4. **Version pinning** - Pin MCP source for reproducibility

---

## Workflow State Integration

For multi-step operations, combine with `workflow-state-patterns`:

```
Intent: MODIFY
  ↓
[PRE-GATE] Check .analysis-done exists
  ↓
Gateway executes action
  ↓
[POST-GATE] Create .execution-done
```

---

## Best Practices

1. **One gateway per MCP** - Don't mix MCPs in single gateway
2. **Intent drives policy** - Timeout/retry based on intent, not action
3. **Effect for safety** - MUTATING requires pre-validation
4. **Artifact for parsing** - Output handler based on artifact type
5. **Always JSON** - Gateway output must be parseable even on error
