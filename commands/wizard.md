---
description: Guided entry point for all skillmaker workflows. Asks what you want to create and routes to the appropriate command.
argument-hint: ""
allowed-tools: ["SlashCommand", "Glob", "Read"]
---

# Skillmaker Wizard

Unified entry point that guides users to the right workflow through simple questions.

## Step 1: Determine Intent

Ask the user:

```
What would you like to do?

1. Create a skill (reusable knowledge or automation)
2. Create an agent (isolated context + skills)
3. Create a command (orchestrate agents)
4. Validate for deployment

Enter number (1-4):
```

**Route based on answer:**

| Choice | Next Step |
|--------|-----------|
| 1 | Go to Step 2 (Skill creation) |
| 2 | Go to Step 3 (Agent creation) |
| 3 | Go to Step 4 (Command creation) |
| 4 | Go to Step 5 (Validation) |

---

## Step 2: Skill Creation Branch

Ask:

```
How do you want to create the skill?

1. From scratch (new idea, guidelines, or automation)
2. From existing code (convert working code to reusable skill)

Enter number (1-2):
```

**Route:**

| Choice | Action |
|--------|--------|
| 1 | Use SlashCommand: `/skillmaker:skill-new` |
| 2 | Ask: "What code/functionality to convert?" then use SlashCommand: `/skillmaker:skillization [target]` |

---

## Step 3: Agent Creation Branch

First, check if skills exist:

```
Glob: .claude/skills/*/SKILL.md
```

**If no skills found:**
```
No skills found in .claude/skills/

You need skills before creating an agent.
Would you like to create a skill first? (yes/no)
```
- Yes → Go to Step 2
- No → End

**If skills exist:**
```
Found {n} skill(s). Ready to create an agent that uses them.

Describe what this agent should do:
```

Then use SlashCommand: `/skillmaker:skill-cover [user's description]`

---

## Step 4: Command Creation Branch

First, check if agents exist:

```
Glob: .claude/agents/*.md
```

**If no agents found:**
```
No agents found in .claude/agents/

You need agents before creating commands.
Would you like to create an agent first? (yes/no)
```
- Yes → Go to Step 3
- No → End

**If agents exist:**
```
Found {n} agent(s). Ready to create a command workflow.

Describe what workflow this command should execute:
```

Then use SlashCommand: `/skillmaker:command-maker [user's description]`

---

## Step 5: Validation Branch

Use SlashCommand: `/skillmaker:deploy-checker`

---

## Quick Reference

For users who know what they want:

| Direct Command | Purpose |
|----------------|---------|
| `/skillmaker:skill-new [desc]` | Create skill from scratch |
| `/skillmaker:skillization [code]` | Convert existing code |
| `/skillmaker:skill-cover [purpose]` | Create skill-using agent |
| `/skillmaker:command-maker [workflow]` | Create agent-orchestrating command |
| `/skillmaker:deploy-checker` | Validate before deployment |

---

## Flow Diagram

```
/skillmaker:wizard
       │
       ├─[1] Skill ─┬─[1] New ────→ /skillmaker:skill-new
       │            └─[2] Convert ─→ /skillmaker:skillization
       │
       ├─[2] Agent ─────────────────→ /skillmaker:skill-cover
       │     └─(needs skills first)
       │
       ├─[3] Command ───────────────→ /skillmaker:command-maker
       │     └─(needs agents first)
       │
       └─[4] Validate ──────────────→ /skillmaker:deploy-checker
```
