import { existsSync } from 'fs'
import { join } from 'path'
import { findPluginRoot, printBox, readJsonFile } from '../lib/utils.js'
import type { Plugin, PluginHooks, SkillRules, ChatParamsInput } from '../lib/types.js'

interface MatchedSkill {
  name: string
  priority: string
  type: string
}

function matchKeywords(prompt: string, keywords: string[]): boolean {
  const lower = prompt.toLowerCase()
  return keywords.some(kw => lower.includes(kw.toLowerCase()))
}

function matchPatterns(prompt: string, patterns: string[]): boolean {
  const lower = prompt.toLowerCase()
  return patterns.some(p => {
    try {
      return new RegExp(p, 'i').test(lower)
    } catch {
      return false
    }
  })
}

function findMatchingSkills(prompt: string, rules: SkillRules): MatchedSkill[] {
  const matched: MatchedSkill[] = []
  
  for (const [skillName, config] of Object.entries(rules.skills)) {
    const triggers = config.promptTriggers
    if (matchKeywords(prompt, triggers.keywords) || 
        matchPatterns(prompt, triggers.intentPatterns)) {
      matched.push({
        name: skillName,
        priority: config.priority,
        type: config.type
      })
    }
  }

  const order: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 }
  matched.sort((a, b) => (order[a.priority] ?? 99) - (order[b.priority] ?? 99))
  
  return matched
}

function detectComplexity(prompt: string, levels: SkillRules['complexity_levels']): string | null {
  const lower = prompt.toLowerCase()
  for (const level of ['advanced', 'standard', 'simple']) {
    const config = levels[level]
    if (config?.keywords.some(kw => lower.includes(kw.toLowerCase()))) {
      return level
    }
  }
  return null
}

export const SkillActivation: Plugin = async ({ directory }) => {
  const pluginRoot = findPluginRoot(directory)
  
  function loadSkillRules(): SkillRules | null {
    const paths = [
      join(pluginRoot, '.opencode', 'skill', 'skill-rules.json'),
      join(pluginRoot, '.claude', 'skills', 'skill-rules.json')
    ]
    
    for (const path of paths) {
      if (existsSync(path)) {
        return readJsonFile<SkillRules>(path)
      }
    }
    return null
  }

  const hooks: PluginHooks = {
    'chat.params': async (input: ChatParamsInput) => {
      const prompt = input.message?.text || ''
      if (!prompt) return

      const rules = loadSkillRules()
      if (!rules) return

      const complexity = detectComplexity(prompt, rules.complexity_levels)
      const matched = findMatchingSkills(prompt, rules)

      if (complexity) {
        const autoSkills = rules.complexity_levels[complexity]?.auto_skills || []
        for (const skillName of autoSkills) {
          if (!matched.some(m => m.name === skillName)) {
            matched.push({ name: skillName, priority: 'medium', type: 'complexity-based' })
          }
        }
      }

      if (matched.length > 0) {
        const icons: Record<string, string> = { high: '\u26A1', medium: '\uD83D\uDCA1', low: '\uD83D\uDCCC' }
        const lines = [
          ...(complexity ? [`Complexity: ${complexity.toUpperCase()}`, ''] : []),
          ...matched.slice(0, 5).map(s => 
            `${icons[s.priority] || '\u2022'} skillmaker:${s.name}`
          ),
          '',
          'Use: Skill("skillmaker:{name}") to load'
        ]
        printBox('RECOMMENDED SKILLS', lines, '\uD83D\uDCDA')
      }
    }
  }

  return hooks
}

export default SkillActivation
