---
name: skill-catalog
description: Categorize and display available skills. Use when listing or selecting skills.
allowed-tools: ["Read", "Glob", "Grep"]
---

# Discovery

```bash
Glob: .claude/skills/*/SKILL.md
```

Read each SKILL.md, extract name and description.

---

# Categories

| Icon | Category | Keywords |
|------|----------|----------|
| 📊 | Data & Analysis | data, sql, database, query |
| 🎨 | Design & Frontend | ui, frontend, component, design |
| 📝 | Documentation | doc, writing, content |
| 🔧 | Development Tools | build, deploy, test, ci |
| 🔒 | Security | security, auth, validation |
| 🤖 | AI & Automation | ai, workflow, orchestration |
| 📦 | Code Generation | generate, scaffold, template |
| 🔍 | Code Analysis | analyze, review, refactor |

---

# Categorization

Match description keywords to categories:

```
for skill in skills:
  for category, keywords in categories:
    if any(keyword in description):
      assign category
```

---

# Display Format

```markdown
## Available Skills

### 📊 Data & Analysis
- **sql-helper**: Write and optimize SQL queries

### 🎨 Design & Frontend
- **frontend-design**: Create polished UI components
```

---

# Selection (for orchestrators)

```
Which skills to use?

📊 Data: 1. sql-helper
🎨 Design: 2. frontend-design

Enter numbers or names:
```
