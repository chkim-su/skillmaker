import { printBox } from '../lib/utils.js'
import type { Plugin, PluginHooks, ToolExecuteInput, ToolExecuteOutput } from '../lib/types.js'

const ANALYZE_KEYWORDS = ['analyze', 'analysis', '분석', '고찰', 'review', '리뷰', '검토']

const SYNTHESIS_MARKERS = [
  '해결책 종합', 'Solution Synthesis', '해결책 직접 추출',
  '적극적 추출', '구현 단계', '구체적 방법', '즉시 실행 가능'
]

export const SolutionSynthesis: Plugin = async () => {
  const hooks: PluginHooks = {
    'tool.execute.after': async (input: ToolExecuteInput, output?: ToolExecuteOutput) => {
      const toolName = input.tool.toLowerCase()
      if (toolName !== 'task') return

      const prompt = String(input.args?.prompt || '').toLowerCase()
      const description = String(input.args?.description || '').toLowerCase()
      
      const isAnalyzeTask = ANALYZE_KEYWORDS.some(kw => 
        prompt.includes(kw) || description.includes(kw)
      )
      
      if (!isAnalyzeTask) return

      const result = String(output?.result || '')
      const hasSynthesis = SYNTHESIS_MARKERS.some(marker => result.includes(marker))
      
      if (!hasSynthesis) {
        printBox('SOLUTION SYNTHESIS WARNING (W035 Enforcement)', [
          'ANALYZE 라우트가 완료되었으나 Solution Synthesis 섹션이 감지되지 않았습니다.',
          '',
          'skillmaker 원칙에 따라:',
          '  1. 문제 발견 시 관련 스킬을 즉시 로드해야 합니다',
          '  2. 스킬의 references/에서 해결책을 추출해야 합니다',
          '  3. 사용자가 바로 실행 가능한 형태로 제시해야 합니다',
          '',
          '금지 행동:',
          '  \u274C \'이 스킬을 참고하세요\' (수동적)',
          '  \u274C \'패턴이 있습니다\' (구체성 부족)',
          '',
          '권장 행동:',
          '  \u2705 Skill(\'skillmaker:relevant-skill\') 로드',
          '  \u2705 Read(\'references/solution.md\') 수행',
          '  \u2705 구체적 명령/코드 추출하여 제시'
        ], '\u26A0\uFE0F')
      }
    }
  }

  return hooks
}

export default SolutionSynthesis
