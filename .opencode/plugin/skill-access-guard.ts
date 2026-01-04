import { printBox } from '../lib/utils.js'
import type { Plugin, PluginHooks, ToolExecuteInput } from '../lib/types.js'

const SKILL_PATTERNS = [
  /\/skills\/([^/]+)\/SKILL\.md/i,
  /\.claude\/skills\/([^/]+)\/SKILL\.md/i,
  /\.opencode\/skill\/([^/]+)\/SKILL\.md/i,
  /plugins\/.*\/skills\/([^/]+)\/SKILL\.md/i
]

export const SkillAccessGuard: Plugin = async () => {
  const hooks: PluginHooks = {
    'tool.execute.before': async (input: ToolExecuteInput) => {
      const toolName = input.tool.toLowerCase()
      if (!['read', 'grep', 'glob'].includes(toolName)) return

      const filePath = String(input.args?.filePath || input.args?.file_path || input.args?.path || input.args?.pattern || '')
      if (!filePath) return

      for (const pattern of SKILL_PATTERNS) {
        const match = pattern.exec(filePath)
        if (match) {
          const skillName = match[1] || 'unknown'
          printBox('SKILL FILE DIRECT ACCESS DETECTED', [
            `Path: ${filePath}`,
            '',
            '\u274C Reading skill files directly is discouraged',
            `\u2705 Use: Skill("plugin:${skillName}")`,
            '',
            'The Skill() tool loads skill content properly',
            'and ensures correct skill activation.'
          ], '\u26A0\uFE0F')
          break
        }
      }
    }
  }

  return hooks
}

export default SkillAccessGuard
