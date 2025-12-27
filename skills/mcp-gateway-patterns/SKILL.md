---
name: mcp-gateway-patterns
description: MCP Gateway design patterns for both Agent Gateway and Subprocess isolation. Use when designing MCP integrations.
allowed-tools: ["Read", "Write", "Grep", "Glob"]
---

# MCP Gateway Patterns

Heavy MCP servers consume context tokens. Two isolation strategies exist.

## Quick Start

1. Choose strategy: Agent Gateway (frequent) or Subprocess (rare)
2. Define 2-layer protocol: Intent → Action
3. Create gateway agent or subprocess wrapper

## Strategy Selection

| Criteria | Agent Gateway | Subprocess |
|----------|---------------|------------|
| Usage | Frequent | Rare |
| State | Continuous | Stateless |
| Latency | Low | 5-15s startup |
| Token overhead | Acceptable | Zero |

## 2-Layer Protocol

**Layer 1 - Intent** (common across MCPs):
| Intent | Effect | Use |
|--------|--------|-----|
| QUERY | READ_ONLY | Search, lookup |
| ANALYZE | READ_ONLY | Interpret, impact |
| MODIFY | MUTATING | Change files |
| EXECUTE | EXTERNAL_EXEC | External calls |

**Layer 2 - Action**: MCP-specific tool names

## Gateway Template

```yaml
---
name: {mcp}-gateway
tools: [mcp__{mcp}__{tool1}, ...]
model: sonnet
---
```

Responsibilities:
1. Context activation
2. Pre-validation for MODIFY
3. Atomic JSON responses

## Best Practices

1. **One gateway per MCP**
2. **Intent drives policy** - timeout/retry based on intent
3. **Effect for safety** - MUTATING requires pre-validation
4. **Always JSON** - even on error

## References

- [Agent Gateway Template](references/agent-gateway-template.md)
- [Subprocess Gateway](references/subprocess-gateway.md)
- [Protocol Schema](references/protocol-schema.md)
