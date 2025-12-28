---
name: mcp-gateway-patterns
description: MCP Gateway design patterns for both Agent Gateway and Subprocess isolation. Use when designing MCP integrations.
allowed-tools: ["Read", "Write", "Bash", "Grep", "Glob"]
---

# MCP Gateway Patterns

Heavy MCP servers consume context tokens. Two isolation strategies exist.

## Critical Knowledge

### MCP Registration Methods

| Method | File Location | Correct? |
|--------|---------------|----------|
| `claude mcp add --scope user` | `~/.claude.json` | ✅ |
| `claude mcp add --scope project` | `.mcp.json` | ✅ |
| Manual `~/.claude/mcp_servers.json` | Legacy file | ❌ NOT READ |

**Correct Registration:**
```bash
claude mcp add --transport stdio --scope user <name> -- <command> [args...]
```

---

### Agent MCP Access Rules

| `tools:` Setting | MCP Access | Example |
|------------------|------------|---------|
| Empty/Omitted | ✅ All tools | `tools:` |
| Explicit list (no MCP) | ❌ NO access | `tools: ["Read", "Write"]` |
| Explicit list (with MCP) | ✅ Listed only | `tools: ["Read", "mcp__serena__*"]` |

---

### MCP Tool Naming Convention

| Registration Type | Tool Name Pattern |
|-------------------|-------------------|
| Plugin MCP | `mcp__plugin_<server>_<server>__<tool>` |
| User MCP | `mcp__<server>__<tool>` |

---

## Strategy Selection (Empirically Verified)

| Criteria | Agent Gateway | Subprocess Bridge |
|----------|---------------|-------------------|
| Startup latency | ~1s | **30-60s** (measured) |
| Token overhead | ~350 tokens/tool | **Zero** in main session |
| State | Continuous | Stateless (per-call) |
| Best for | > 10 calls/session | < 3 calls/session |

### Token Savings by MCP (Measured)

| MCP | Tools | Overhead | Subprocess Benefit |
|-----|-------|----------|-------------------|
| Serena | 29 | ~10,150 | ✅ High |
| Playwright | 25 | ~6,250 | ✅ High |
| Greptile | 12 | ~3,600 | ⚠️ Medium |
| Context7 | 2 | ~400 | ❌ Not worth it |

**Rule**: If `tools × 350 > 5,000`, consider subprocess isolation.

---

## 2-Layer Protocol

**Layer 1 - Intent** (common across MCPs):
| Intent | Effect | Use |
|--------|--------|-----|
| QUERY | READ_ONLY | Search, lookup |
| ANALYZE | READ_ONLY | Interpret, impact |
| MODIFY | MUTATING | Change files |
| EXECUTE | EXTERNAL_EXEC | External calls |

**Layer 2 - Action**: MCP-specific tool names

---

## Gateway Template

```yaml
---
name: {mcp}-gateway
tools:  # Empty = all tools including MCP
model: sonnet
---
```

Responsibilities:
1. Context activation
2. Pre-validation for MODIFY
3. Atomic JSON responses

---

## Common Issues

### "MCP tools not visible"
- **Cause:** Session not restarted after `claude mcp add`
- **Fix:** Restart Claude Code

### "Tool not found in subagent"
- **Cause:** Agent has explicit `tools:` list without MCP
- **Fix:** Empty `tools:` or add MCP tools to list

### "Wrong tool name format"
- **Cause:** Mixing plugin (`mcp__plugin_x_x__`) and user (`mcp__x__`) formats
- **Fix:** Check `claude mcp list` for actual server name prefix

---

## References

- [Agent Gateway Template](references/agent-gateway-template.md)
- [Subprocess Gateway](references/subprocess-gateway.md)
- [**Subprocess Research Report**](references/subprocess-research-report.md) - Empirical findings
- [Protocol Schema](references/protocol-schema.md)
- [Setup Automation](references/setup-automation.md)
- [Validation Patterns](references/validation-patterns.md)
