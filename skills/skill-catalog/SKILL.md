---
name: skill-catalog
description: Categorizes and displays available skills with similarity grouping. Use when showing skill lists or selecting skills for orchestrators.
allowed-tools: ["Read", "Glob", "Grep"]
---

# Skill Catalog

This skill helps discover, categorize, and present available skills in an organized manner.

## When to Use

- Showing available skills to user
- Building multi-skill orchestrators
- Discovering skills by category
- Finding similar skills

## How to Catalog Skills

### Step 1: Discover All Skills

```bash
# Find all SKILL.md files
Glob: .claude/skills/*/SKILL.md
Glob: ~/.claude/skills/*/SKILL.md
```

### Step 2: Read and Categorize

For each skill:
1. Read SKILL.md
2. Extract name and description
3. Categorize by domain

### Step 3: Group by Category

Common categories:

| Category | Keywords | Examples |
|----------|----------|----------|
| 📊 **Data & Analysis** | data, sql, analysis, query, database | data-analysis, sql-helper |
| 🎨 **Design & Frontend** | ui, design, frontend, component, theme | frontend-design, theme-factory |
| 📝 **Documentation** | doc, documentation, writing, content | doc-coauthoring, content-writer |
| 🔧 **Development Tools** | build, deploy, test, ci, automation | deployment-tool, test-runner |
| 🔒 **Security** | security, auth, validation, sanitize | security-auditor, auth-helper |
| 🤖 **AI & Automation** | ai, automation, workflow, orchestration | workflow-orchestrator |
| 📦 **Code Generation** | generate, create, scaffold, template | component-generator, api-scaffold |
| 🔍 **Code Analysis** | analyze, review, refactor, quality | code-analyzer, refactor-helper |

### Step 4: Present Organized List

**Format for display:**

```markdown
## Available Skills

### 📊 Data & Analysis
- **data-analysis**: Analyze datasets and generate insights
- **sql-helper**: Write and optimize SQL queries

### 🎨 Design & Frontend
- **frontend-design**: Create polished UI components with modern patterns
- **theme-factory**: Apply consistent theming across artifacts

### 📝 Documentation
- **doc-coauthoring**: Collaborative documentation workflow
- **api-docs**: Generate API documentation from code

### 🔧 Development Tools
- **test-runner**: Execute and analyze test suites
- **deployment-tool**: Coordinate deployment workflows
```

## Similarity Detection

Group similar skills using these heuristics:

1. **Name similarity**: `sql-helper`, `sql-optimizer` → Same category
2. **Description keywords**: Both mention "database" → Related
3. **Tool overlap**: Both use same allowed-tools → Similar scope

## Categorization Algorithm

```python
# Pseudo-code for categorization

categories = {
    'data': ['data', 'sql', 'database', 'query', 'analysis'],
    'design': ['ui', 'frontend', 'component', 'design', 'theme'],
    'docs': ['doc', 'documentation', 'writing', 'content'],
    'dev': ['build', 'deploy', 'test', 'ci', 'automation'],
    'security': ['security', 'auth', 'validation', 'sanitize'],
    'ai': ['ai', 'automation', 'workflow', 'orchestration'],
    'generation': ['generate', 'create', 'scaffold', 'template'],
    'analysis': ['analyze', 'review', 'refactor', 'quality']
}

for skill in skills:
    description_lower = skill.description.lower()
    for category, keywords in categories.items():
        if any(keyword in description_lower for keyword in keywords):
            skill.category = category
            break
    else:
        skill.category = 'other'
```

## Interactive Selection

When building orchestrators:

```markdown
Which skills should this orchestrator use?

📊 Data & Analysis:
1. data-analysis
2. sql-helper

🎨 Design & Frontend:
3. frontend-design
4. theme-factory

Enter skill numbers (comma-separated) or names:
```

## Compact Display

For quick reference:

```
Skills (12 total):
📊 Data: data-analysis, sql-helper
🎨 Design: frontend-design, theme-factory
📝 Docs: doc-coauthoring, api-docs
🔧 Dev: test-runner, deployment-tool
🔒 Security: security-auditor, auth-helper
```

## Usage in skill-cover Command

When the skill-orchestrator-designer agent needs to show skills:

1. Use this skill's cataloging approach
2. Display categorized list
3. Allow user to select by name or number
4. Return selected skills for YAML frontmatter

## Key Principles

- **Category icons**: Use emoji for visual grouping
- **Concise descriptions**: One-line summaries only
- **Similarity grouping**: Related skills together
- **Interactive selection**: For orchestrator building
