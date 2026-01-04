import { existsSync } from 'fs'
import { join } from 'path'
import { findPluginRoot, printBox, readTextFile } from '../lib/utils.js'
import { parseFrontmatter } from '../lib/frontmatter.js'
import type { Plugin, PluginHooks, ToolExecuteInput, PatternIssue } from '../lib/types.js'

function checkContentPatterns(content: string, fileType: string): PatternIssue[] {
  const issues: PatternIssue[] = []
  const { frontmatter, body } = parseFrontmatter(content)

  if (['agent', 'command'].includes(fileType)) {
    const skillPatterns = [/Skill\s*\(/i, /Skill\s+tool/i, /load.*skill/i, /use.*Skill/i]
    const hasSkillCall = skillPatterns.some(p => p.test(body))

    if (frontmatter?.skills && !hasSkillCall) {
      issues.push({
        code: 'W033',
        message: `Declares skills [${frontmatter.skills}] but no Skill() usage found`,
        action: 'Consider: Skill("plugin:skill-name") for explicit loading',
        reference: 'Skill("skillmaker:orchestration-patterns")'
      })
    }
  }

  const stagePatterns = [
    /#{1,3}\s*(Phase|Step|Stage)\s*\d/gi,
    /#{1,3}\s*\d+\.\s/g,
    /#{1,3}\s*(First|Second|Third|Fourth|Fifth)/gi
  ]
  const stageCount = stagePatterns.reduce((sum, p) => 
    sum + (content.match(p)?.length || 0), 0)

  if (stageCount >= 3) {
    const skillCalls = (content.match(/Skill\s*\(/g) || []).length
    if (skillCalls < stageCount / 2) {
      issues.push({
        code: 'W034',
        message: `Multi-stage workflow (${stageCount} stages) with only ${skillCalls} Skill() calls`,
        action: 'Consider: Per-stage skill loading for context isolation',
        reference: 'Skill("skillmaker:workflow-state-patterns")'
      })
    }
  }

  if (fileType === 'skill') {
    const required = ['name', 'description']
    const missing = required.filter(f => !frontmatter?.[f])
    if (missing.length > 0) {
      issues.push({
        code: 'W029',
        message: `Missing frontmatter: ${missing.join(', ')}`,
        action: 'Add frontmatter with name, description, allowed-tools',
        reference: 'Skill("skillmaker:skill-design")'
      })
    }
  }

  if (fileType === 'agent') {
    const required = ['name', 'description', 'tools']
    const missing = required.filter(f => !frontmatter?.[f])
    if (missing.length > 0) {
      issues.push({
        code: 'W030',
        message: `Missing frontmatter: ${missing.join(', ')}`,
        action: 'Add frontmatter with name, description, tools, skills',
        reference: 'Skill("skillmaker:orchestration-patterns")'
      })
    }
  }

  return issues
}

function detectFileType(filePath: string): { type: string | null; name: string } {
  if (filePath.includes('/agents/') || filePath.includes('\\agents\\')) {
    const parts = filePath.split(/[/\\]/)
    const filename = parts[parts.length - 1] || ''
    return { type: 'agent', name: filename.replace('.md', '') }
  }
  if (filePath.includes('/skills/') || filePath.includes('\\skills\\')) {
    if (filePath.endsWith('SKILL.md')) {
      const parts = filePath.split(/[/\\]/)
      return { type: 'skill', name: parts[parts.length - 2] || '' }
    }
    return { type: 'skill_ref', name: '' }
  }
  if (filePath.includes('/commands/') || filePath.includes('\\commands\\')) {
    const parts = filePath.split(/[/\\]/)
    const filename = parts[parts.length - 1] || ''
    return { type: 'command', name: filename.replace('.md', '') }
  }
  return { type: null, name: '' }
}

function printAlert(context: string, name: string, issues: PatternIssue[]): void {
  if (issues.length === 0) return

  const lines = [
    `Context: ${context}`,
    `Target: ${name}`,
    '',
    ...issues.flatMap(i => [
      `[${i.code}] ${i.message}`,
      `       \u2192 ${i.action}`,
      ...(i.reference ? [`       \uD83D\uDCDA ${i.reference}`] : []),
      ''
    ]),
    '\u2139\uFE0F  This is a notification to ensure awareness.',
    '   Load the referenced skill for detailed guidance.'
  ]
  printBox('PATTERN COMPLIANCE ALERT', lines, '\u26A0\uFE0F')
}

export const PatternCompliance: Plugin = async ({ directory }) => {
  const pluginRoot = findPluginRoot(directory)

  const hooks: PluginHooks = {
    'tool.execute.before': async (input: ToolExecuteInput) => {
      const toolName = input.tool.toLowerCase()

      if (toolName === 'task') {
        const subagentType = String(input.args?.subagent_type || '')
        if (!subagentType) return

        const agentName = subagentType.includes(':') 
          ? subagentType.split(':').pop() || ''
          : subagentType
        
        const agentPath = join(pluginRoot, 'agents', `${agentName}.md`)
        const content = readTextFile(agentPath)
        if (content) {
          const issues = checkContentPatterns(content, 'agent')
          printAlert('Launching agent via Task', agentName, issues)
        }
      }

      if (['write', 'edit'].includes(toolName)) {
        const filePath = String(input.args?.filePath || input.args?.file_path || '')
        const content = String(input.args?.content || input.args?.new_string || '')
        
        if (!filePath || !content) return

        const { type, name } = detectFileType(filePath)
        if (!type || type === 'skill_ref') return

        const issues = checkContentPatterns(content, type)
        if (issues.length > 0) {
          printAlert(`Writing ${type} file`, name, issues)
        }
      }
    },

    'tool.execute.after': async () => {}
  }

  return hooks
}

export default PatternCompliance
