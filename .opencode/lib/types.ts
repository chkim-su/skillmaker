/**
 * OpenCode Plugin Types for Skillmaker
 */

// Plugin context from OpenCode
export interface PluginContext {
  project?: string
  client?: unknown
  $: (strings: TemplateStringsArray, ...values: unknown[]) => Promise<{ exitCode: number; stdout: string; stderr: string }>
  directory: string
  worktree?: string
}

// Tool execution input
export interface ToolExecuteInput {
  tool: string
  args: Record<string, unknown>
}

// Tool execution output
export interface ToolExecuteOutput {
  result?: string
  error?: string
}

// Skill rule configuration
export interface SkillRule {
  type: string
  enforcement: string
  priority: 'critical' | 'high' | 'medium' | 'low'
  promptTriggers: {
    keywords: string[]
    intentPatterns: string[]
  }
}

// Skill rules JSON structure
export interface SkillRules {
  version: string
  skills: Record<string, SkillRule>
  complexity_levels: Record<string, {
    keywords: string[]
    auto_skills: string[]
  }>
}

// Pattern compliance issue
export interface PatternIssue {
  code: string
  message: string
  action: string
  reference?: string
}

// Validation result
export interface ValidationResult {
  errors: string[]
  warnings: string[]
  passed: string[]
}

// Chat params input
export interface ChatParamsInput {
  message?: {
    text?: string
  }
}

// Plugin hooks return type
export interface PluginHooks {
  'chat.params'?: (input: ChatParamsInput, output?: unknown) => Promise<void>
  'tool.execute.before'?: (input: ToolExecuteInput, output?: ToolExecuteOutput) => Promise<void>
  'tool.execute.after'?: (input: ToolExecuteInput, output?: ToolExecuteOutput) => Promise<void>
  event?: (ctx: { event: { type: string; properties?: Record<string, unknown> } }) => Promise<void>
}

// Plugin type
export type Plugin = (ctx: PluginContext) => Promise<PluginHooks>
