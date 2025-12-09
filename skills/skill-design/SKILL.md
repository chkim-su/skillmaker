---
name: skill-design
description: Best practices for skill structure, progressive disclosure, scripts, assets, and trigger phrases. Use when creating or designing skills. Covers knowledge skills, tool skills, and hybrid skills with appropriate degrees of freedom.
allowed-tools: ["Read", "Write", "Glob", "Grep", "Bash"]
---

# Skill Design Best Practices

This skill provides expert guidance on creating effective, production-ready skills.

## What Skills Provide

1. **Specialized workflows** - Multi-step procedures for specific domains
2. **Tool integrations** - Instructions for working with specific file formats or APIs
3. **Domain expertise** - Company-specific knowledge, schemas, business logic
4. **Bundled resources** - Scripts, references, and assets for complex tasks

## Skill Anatomy

Every skill consists of a required SKILL.md and optional bundled resources:

```
skill-name/
├── SKILL.md              # Required: Core instructions
├── scripts/              # Optional: Executable code (Python/Bash/JS)
├── references/           # Optional: Documentation loaded on-demand
└── assets/               # Optional: Templates, images, fonts for output
```

### When to Use Each Directory

| Directory | Purpose | When to Include |
|-----------|---------|-----------------|
| `scripts/` | Deterministic, reusable code | Same code rewritten repeatedly; reliability critical |
| `references/` | Domain knowledge, schemas | Claude should reference while working |
| `assets/` | Output resources | Files used in final output (templates, images) |

## Skill Types by Degrees of Freedom

Match specificity to task fragility and variability:

### High Freedom (Knowledge Skills)
**Use when**: Multiple approaches valid, decisions depend on context

```yaml
# Analysis, guidance, best practices
allowed-tools: Read, Grep, Glob
```

**Structure**:
```
code-review-patterns/
├── SKILL.md              # Guidelines, principles
└── references/
    └── patterns.md       # Detailed patterns
```

**Examples**: code-review, architecture-patterns, security-guidelines

### Medium Freedom (Hybrid Skills)
**Use when**: Preferred patterns exist, some variation acceptable

```yaml
# Guidance + helper scripts
allowed-tools: Read, Write, Grep, Glob, Bash
```

**Structure**:
```
api-generator/
├── SKILL.md              # Workflow + when to use scripts
├── scripts/
│   └── scaffold.py       # Generates boilerplate
├── references/
│   └── patterns.md       # API design patterns
└── assets/
    └── template/         # Starter template
```

**Examples**: api-generator, test-generator, migration-helper

### Low Freedom (Tool Skills)
**Use when**: Operations fragile, consistency critical, specific sequence required

```yaml
# Primarily script-driven
allowed-tools: Read, Write, Bash
```

**Structure**:
```
pdf-processor/
├── SKILL.md              # When/how to use scripts
├── scripts/
│   ├── extract_text.py   # Extract text from PDF
│   ├── merge_pdfs.py     # Merge multiple PDFs
│   ├── rotate_page.py    # Rotate PDF pages
│   └── fill_form.py      # Fill PDF forms
└── references/
    └── troubleshooting.md
```

**Examples**: pdf-processor, image-converter, simple-file-tools

### Expert Domain Skills (CRITICAL)
**Use when**: Complex domain knowledge required, hard to reimplement without skill

```yaml
# Comprehensive documentation + tested scripts
allowed-tools: Read, Write, Bash
```

**Characteristics**:
- ⚠️ **Without skill, Claude must rediscover through trial-and-error**
- ⚠️ File format internals (OOXML, PDF structure, binary formats)
- ⚠️ Undocumented APIs or behaviors
- ⚠️ Experience-based workarounds and edge cases
- ⚠️ Library-specific quirks and limitations

**Structure** (MUST be comprehensive):
```
pptx-builder/
├── SKILL.md                      # Core workflow + navigation
├── scripts/
│   ├── create_slide.py           # Tested, working scripts
│   ├── add_shape.py
│   ├── insert_image.py
│   ├── export_pdf.py
│   └── validation/
│       ├── validate_pptx.py      # Validation tools
│       └── repair_pptx.py
├── references/
│   ├── ooxml-structure.md        # Internal format documentation
│   ├── slide-layouts.md          # Layout types and usage
│   ├── shape-types.md            # All shape types and properties
│   ├── text-formatting.md        # Text/font handling quirks
│   ├── image-handling.md         # Image embedding gotchas
│   ├── troubleshooting.md        # Known issues and fixes
│   └── library-comparison.md     # Why we chose this library
└── assets/
    ├── templates/                # Working templates
    └── examples/                 # Example outputs
```

**Why Expert Skills Need Extensive Documentation**:

```
Without skill:
┌─────────────────────────────────────────────────┐
│ Claude attempts PPTX creation                   │
│ → Tries python-pptx basic API                   │
│ → Hits limitation (e.g., tables don't work)     │
│ → Searches for workaround                       │
│ → Tries multiple approaches (wastes tokens)     │
│ → May or may not find working solution          │
│ → No knowledge retained for next time           │
└─────────────────────────────────────────────────┘

With Expert Skill:
┌─────────────────────────────────────────────────┐
│ Claude loads pptx-builder skill                 │
│ → Sees: "For tables, use scripts/add_table.py" │
│ → Sees: "Known issue: use XML workaround"       │
│ → Executes tested script                        │
│ → Works first time                              │
└─────────────────────────────────────────────────┘
```

**Required Documentation for Expert Skills**:

| Document | Purpose | Example Content |
|----------|---------|-----------------|
| `ooxml-structure.md` | Internal format | XML namespaces, element hierarchy |
| `troubleshooting.md` | Known issues | "Error X → Do Y because Z" |
| `library-comparison.md` | Tool selection | "We use X not Y because..." |
| `edge-cases.md` | Gotchas | "Large images crash unless..." |
| `validation.md` | How to verify | "Check output with scripts/validate.py" |

**Examples**: pptx-builder, docx-editor, xlsx-processor, mcp-builder, algorithmic-art

## Deciding What to Include

### Scripts (`scripts/`)

Include scripts when:
- ✅ Same code rewritten repeatedly
- ✅ Deterministic reliability needed
- ✅ Complex logic that's error-prone to regenerate
- ✅ File format manipulation (PDF, XLSX, PPTX, images)
- ✅ External tool/API integration

**Script Benefits**:
- Token efficient (execute without loading into context)
- Deterministic (same input = same output)
- Testable and debuggable
- Version controlled

**Example Decision**:
```
Task: "Rotate a PDF 90 degrees"

Without script: Claude writes rotation code each time
  - May have bugs
  - Uses context tokens
  - Inconsistent implementations

With script: scripts/rotate_pdf.py
  - Run: python scripts/rotate_pdf.py input.pdf 90
  - Reliable, tested, fast
```

### References (`references/`)

Include references when:
- ✅ Domain knowledge Claude needs while working
- ✅ API documentation, schemas, specifications
- ✅ Company-specific guidelines or policies
- ✅ Detailed patterns too long for SKILL.md

**Keep SKILL.md lean**: If >500 lines, split into references.

**Example Structure**:
```
bigquery-skill/
├── SKILL.md              # Overview, navigation
└── references/
    ├── finance.md        # Finance table schemas
    ├── sales.md          # Sales metrics
    └── product.md        # Product analytics
```

### Assets (`assets/`)

Include assets when:
- ✅ Files used in final output (not loaded into context)
- ✅ Templates that get copied/modified
- ✅ Images, icons, fonts for generated content
- ✅ Boilerplate projects

**Examples**:
```
frontend-builder/
└── assets/
    ├── template/         # React starter project
    ├── logo.png          # Brand logo
    └── styles.css        # Base styles

pptx-skill/
└── assets/
    └── template.pptx     # Slide template
```

## SKILL.md Structure

### YAML Frontmatter (Required)

```yaml
---
name: skill-name                    # Kebab-case
description: |                      # CRITICAL: Triggers skill loading
  What this skill does. Use when [scenarios].
  Supports: [capability1], [capability2].
allowed-tools: ["Tool1", "Tool2"]   # Restrict appropriately
---
```

**Description is the trigger mechanism** - Include ALL "when to use" info here, not in body.

### Body Structure

```markdown
# Skill Name

[2-3 sentence overview]

## Quick Start

[Fastest path to using the skill]

## Core Workflow

1. **Step 1**: Action
2. **Step 2**: Action
3. **Step 3**: Action

## Available Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `scripts/tool.py` | Does X | `python scripts/tool.py input output` |

## Key Principles

- Principle 1
- Principle 2

---

For advanced usage: [references/advanced.md](references/advanced.md)
```

## Progressive Disclosure

Three-level loading for context efficiency:

1. **Metadata** (~100 words) - Always in context
2. **SKILL.md body** (<5k words) - When skill triggers
3. **Bundled resources** (unlimited) - As needed

### Pattern: High-level Guide with References

```markdown
## PDF Operations

**Quick**: Use scripts/extract_text.py for text extraction.

**Advanced features**:
- Form filling: See [references/forms.md](references/forms.md)
- OCR: See [references/ocr.md](references/ocr.md)
```

Claude loads references only when needed.

### Pattern: Domain Organization

```
cloud-deploy/
├── SKILL.md              # Workflow + provider selection
└── references/
    ├── aws.md            # AWS patterns
    ├── gcp.md            # GCP patterns
    └── azure.md          # Azure patterns
```

User chooses AWS → Claude reads only aws.md.

## Tool Restrictions

Match tools to skill purpose:

```yaml
# Knowledge skill (read-only analysis)
allowed-tools: ["Read", "Grep", "Glob"]

# Hybrid skill (guidance + code generation)
allowed-tools: ["Read", "Write", "Edit", "Grep", "Glob"]

# Tool skill (file manipulation + automation)
allowed-tools: ["Read", "Write", "Bash"]

# Full automation skill
allowed-tools: ["Read", "Write", "Edit", "Bash", "Task"]
```

## Trigger Phrases

Include 5-10 specific phrases in description:

**Good triggers**:
- ✅ "create a database migration"
- ✅ "optimize SQL query"
- ✅ "generate PDF report"
- ✅ "rotate image 90 degrees"

**Bad triggers**:
- ❌ "help me" (too generic)
- ❌ "write code" (too broad)

## Validation Checklist

Before finalizing:

- ✅ SKILL.md under 500 lines (use references for more)
- ✅ Description includes all trigger scenarios
- ✅ Appropriate skill type (knowledge/hybrid/tool)
- ✅ Scripts tested and working
- ✅ References linked from SKILL.md
- ✅ Assets organized by purpose
- ✅ allowed-tools matches skill needs
- ✅ No duplicate content (SKILL.md vs references)

## What NOT to Include

- ❌ README.md, INSTALLATION_GUIDE.md, CHANGELOG.md
- ❌ User-facing documentation (skills are for Claude)
- ❌ Duplicate content in SKILL.md and references
- ❌ Untested scripts

---

For advanced patterns: [references/advanced-patterns.md](references/advanced-patterns.md)
