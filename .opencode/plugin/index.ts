import type { Plugin, Hooks } from '@opencode-ai/plugin'
import { existsSync, readFileSync } from 'fs'
import { join, dirname } from 'path'

interface SkillRule {
  type: string
  priority: string
  promptTriggers: {
    keywords: string[]
    intentPatterns: string[]
  }
}

interface SkillRules {
  skills: Record<string, SkillRule>
  complexity_levels: Record<string, {
    keywords: string[]
    auto_skills: string[]
  }>
}

function findPluginRoot(startPath: string): string {
  let current = startPath
  const markers = ['.claude-plugin', '.opencode', 'opencode.json']
  for (let i = 0; i < 10; i++) {
    for (const marker of markers) {
      if (existsSync(join(current, marker))) return current
    }
    const parent = dirname(current)
    if (parent === current) break
    current = parent
  }
  return startPath
}

function printBox(title: string, lines: string[], icon = ''): void {
  console.log('')
  console.log('\u2501'.repeat(55))
  console.log(`${icon} ${title}`)
  console.log('\u2501'.repeat(55))
  lines.forEach(line => console.log(`  ${line}`))
  console.log('\u2501'.repeat(55))
  console.log('')
}

function loadSkillRules(dir: string): SkillRules | null {
  const paths = [
    join(dir, '.opencode', 'skill', 'skill-rules.json'),
    join(dir, '.claude', 'skills', 'skill-rules.json'),
    join(__dirname, '..', 'skill', 'skill-rules.json')
  ]
  for (const path of paths) {
    if (existsSync(path)) {
      try {
        return JSON.parse(readFileSync(path, 'utf-8'))
      } catch { continue }
    }
  }
  return null
}

const SkillmakerPlugin: Plugin = async ({ directory }) => {
  const pluginRoot = findPluginRoot(directory)
  const rules = loadSkillRules(pluginRoot)

  const hooks: Hooks = {
    'chat.params': async (input, output) => {
      if (!rules) return
      const prompt = (input.message as any)?.parts?.[0]?.text || ''
      if (!prompt) return

      const lower = prompt.toLowerCase()
      const matched: Array<{ name: string; priority: string }> = []

      for (const [name, config] of Object.entries(rules.skills)) {
        const { keywords, intentPatterns } = config.promptTriggers
        const keywordMatch = keywords.some(k => lower.includes(k.toLowerCase()))
        const patternMatch = intentPatterns.some(p => {
          try { return new RegExp(p, 'i').test(lower) }
          catch { return false }
        })
        if (keywordMatch || patternMatch) {
          matched.push({ name, priority: config.priority })
        }
      }

      let complexity: string | null = null
      for (const level of ['advanced', 'standard', 'simple']) {
        const cfg = rules.complexity_levels[level]
        if (cfg?.keywords.some(k => lower.includes(k.toLowerCase()))) {
          complexity = level
          for (const s of cfg.auto_skills) {
            if (!matched.some(m => m.name === s)) {
              matched.push({ name: s, priority: 'medium' })
            }
          }
          break
        }
      }

      if (matched.length > 0) {
        const icons: Record<string, string> = { high: '\u26A1', medium: '\uD83D\uDCA1', low: '\uD83D\uDCCC' }
        const order: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 }
        matched.sort((a, b) => (order[a.priority] ?? 99) - (order[b.priority] ?? 99))
        
        printBox('RECOMMENDED SKILLS', [
          ...(complexity ? [`Complexity: ${complexity.toUpperCase()}`, ''] : []),
          ...matched.slice(0, 5).map(s => `${icons[s.priority] || '\u2022'} skillmaker:${s.name}`),
          '',
          'Use: Skill("skillmaker:{name}") to load'
        ], '\uD83D\uDCDA')
      }
    },

    'tool.execute.before': async (input, output) => {
      const tool = input.tool.toLowerCase()

      if (['read', 'grep', 'glob'].includes(tool)) {
        const filePath = String(output.args?.filePath || output.args?.path || '')
        const skillPattern = /\/skills\/([^/]+)\/SKILL\.md/i
        const match = skillPattern.exec(filePath)
        if (match) {
          printBox('SKILL FILE DIRECT ACCESS DETECTED', [
            `Path: ${filePath}`,
            '',
            '\u274C Reading skill files directly is discouraged',
            `\u2705 Use: Skill("plugin:${match[1]}")`,
            '',
            'The Skill() tool loads skill content properly.'
          ], '\u26A0\uFE0F')
        }
      }

      if (tool === 'task') {
        const subagent = String(output.args?.subagent_type || '')
        if (subagent) {
          const agentName = subagent.includes(':') ? subagent.split(':').pop() : subagent
          const agentPath = join(pluginRoot, 'agents', `${agentName}.md`)
          if (existsSync(agentPath)) {
            const content = readFileSync(agentPath, 'utf-8')
            const issues: string[] = []
            
            if (content.includes('skills:') && !/Skill\s*\(/i.test(content)) {
              issues.push('[W033] Declares skills but no Skill() usage found')
            }
            
            const stages = (content.match(/#{1,3}\s*(Phase|Step|Stage)\s*\d/gi) || []).length
            const skillCalls = (content.match(/Skill\s*\(/g) || []).length
            if (stages >= 3 && skillCalls < stages / 2) {
              issues.push(`[W034] Multi-stage (${stages}) with only ${skillCalls} Skill() calls`)
            }

            if (issues.length > 0) {
              printBox('PATTERN COMPLIANCE ALERT', [
                `Agent: ${agentName}`,
                '',
                ...issues,
                '',
                '\u2139\uFE0F Load referenced skill for guidance.'
              ], '\u26A0\uFE0F')
            }
          }
        }
      }
    },

    'tool.execute.after': async (input, output) => {
      if (input.tool.toLowerCase() !== 'task') return

      const result = output.output || ''
      const analyzeKw = ['analyze', 'analysis', '분석', 'review']
      const isAnalyze = analyzeKw.some(k => result.toLowerCase().includes(k))
      
      if (isAnalyze) {
        const synthMarkers = ['Solution Synthesis', '해결책 종합', '구현 단계']
        const hasSynth = synthMarkers.some(m => result.includes(m))
        
        if (!hasSynth) {
          printBox('SOLUTION SYNTHESIS WARNING (W035)', [
            'ANALYZE completed without Solution Synthesis section.',
            '',
            'Required actions:',
            '  1. Load relevant skill immediately',
            '  2. Extract solutions from references/',
            '  3. Present actionable steps',
            '',
            '\u274C Avoid: "See this skill for details"',
            '\u2705 Do: Extract and present concrete solutions'
          ], '\u26A0\uFE0F')
        }
      }
    }
  }

  return hooks
}

export default SkillmakerPlugin
