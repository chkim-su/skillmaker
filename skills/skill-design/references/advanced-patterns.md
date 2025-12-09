# Advanced Skill Design Patterns

This document provides advanced patterns for complex skill scenarios.

## Multi-Phase Skills

Skills that guide users through multi-step processes:

```yaml
---
name: deployment-orchestrator
description: Multi-phase deployment workflow
---

# Deployment Orchestrator

## Phase 1: Pre-Deployment Validation
- Check environment variables
- Validate configuration files
- Run test suite

## Phase 2: Build Process
- Compile assets
- Optimize bundles
- Generate deployment artifacts

## Phase 3: Deployment Execution
- Deploy to staging
- Run smoke tests
- Deploy to production

## Phase 4: Post-Deployment Verification
- Health checks
- Monitor error rates
- Verify feature flags
```

## Conditional Logic in Skills

Skills can include conditional guidance:

```markdown
## Based on Your Stack

### If using React:
- Use React hooks for state management
- Follow React naming conventions
- Apply React-specific optimizations

### If using Vue:
- Use Composition API
- Follow Vue style guide
- Apply Vue-specific patterns
```

## Skills with Fallback Strategies

```markdown
## Primary Approach

Try this first: [Best practice approach]

## If That Fails

Fallback to: [Alternative approach]

## Last Resort

Emergency fix: [Quick workaround with limitations]
```

## Tool Coordination Patterns

Skills can orchestrate multiple tools effectively:

```yaml
allowed-tools: Read, Grep, Glob, Write, Bash
```

```markdown
## Analysis Phase (Read, Grep, Glob)
1. Read configuration files
2. Grep for patterns
3. Glob for related files

## Generation Phase (Write)
4. Write new implementation

## Validation Phase (Bash)
5. Run tests
6. Check linting
```

## Progressive Enhancement

Skills can suggest progressive improvements:

```markdown
## Minimum Viable Implementation
[Quick, working solution]

## Enhanced Version
[Better performance, more features]

## Production-Grade Version
[Full error handling, monitoring, documentation]
```

## Skill Composition Patterns

While skills don't call other skills directly, they can suggest using orchestrator patterns:

```markdown
## For Complex Workflows

This skill handles [domain A].

For workflows involving [domain A + B + C], consider using:
- fullstack-orchestrator agent (combines frontend, backend, database skills)
```

## Context-Aware Skills

Skills can provide different guidance based on detected context:

```markdown
## Detection

First, check:
- Language: TypeScript vs JavaScript
- Framework: React vs Vue vs Angular
- Build tool: Webpack vs Vite

## Context-Specific Guidance

### TypeScript + React + Vite:
[Specific instructions for this stack]

### JavaScript + Vue + Webpack:
[Different instructions for this stack]
```

## Performance-Optimized Skills

For skills that might use many tokens:

```markdown
# Quick Start (100 words)
[Minimal instructions]

---

Need more details? Read:
- [Deep Dive](references/deep-dive.md) - Comprehensive guide
- [API Reference](references/api.md) - Full API documentation
- [Examples](references/examples.md) - 20+ examples

This keeps initial load minimal.
```

## Testing Skills

Skills should include self-testing guidance:

```markdown
## Verify This Skill Works

1. **Trigger Test**: Use trigger phrase "create deployment workflow"
2. **Expected**: Skill should activate and provide deployment steps
3. **Tool Test**: Verify allowed-tools restriction works
4. **Progressive Test**: Confirm references load on demand
```

## Versioning Skills

For skills that evolve:

```markdown
---
name: api-generator
description: Generate REST APIs (v2.0 - GraphQL support added)
version: 2.0
---

## What's New in v2.0
- GraphQL support
- OpenAPI 3.0 generation
- Webhook patterns

## Upgrading from v1.x
[Migration guide]
```

## Error Recovery Patterns

Skills should handle common errors:

```markdown
## Common Issues

### Issue: "Module not found"
**Cause**: Missing dependency
**Fix**:
```bash
npm install [package]
```

### Issue: "Permission denied"
**Cause**: Insufficient file permissions
**Fix**:
```bash
chmod +x [script]
```

## Diagnostic Mode

Add `--verbose` flag for debugging:
[Detailed diagnostic output]
```

## Security-Conscious Skills

Skills handling sensitive operations:

```markdown
## Security Checklist

Before proceeding:
- [ ] No credentials in code
- [ ] Use environment variables
- [ ] HTTPS only
- [ ] Input validation implemented
- [ ] Rate limiting configured

## Sensitive Data Detection

Warn if detected:
- Hardcoded passwords
- API keys in files
- Unencrypted secrets
```

## Skill Analytics

Track skill usage (optional):

```markdown
## Usage Patterns

This skill is most effective for:
- ✅ [Common use case 1] (80% success rate)
- ✅ [Common use case 2] (75% success rate)
- ⚠️ [Edge case] (requires manual adjustment)
```

These advanced patterns help create robust, production-grade skills.
