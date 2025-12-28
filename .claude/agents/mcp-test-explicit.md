---
name: mcp-test-explicit
description: Test agent with explicit MCP tools
tools: ["Read", "Glob", "mcp__serena__get_current_config", "mcp__serena__list_dir", "ListMcpResourcesTool"]
model: sonnet
---

# MCP Access Test Agent

Your task: Test MCP tool access.

## Instructions

1. Try to call `mcp__serena__get_current_config`
2. Try to call `ListMcpResourcesTool`
3. Report which tools you can actually see in your available tools
4. Report the exact error messages if tools fail

BE EXPLICIT about what works and what doesn't. Return JSON format:
```json
{
  "mcp_serena_available": true/false,
  "mcp_serena_error": "error message if any",
  "list_mcp_available": true/false,
  "list_mcp_error": "error message if any",
  "available_tools": ["list of tools you can see"]
}
```
