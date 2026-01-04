/**
 * OpenCode Plugin Types for Skillmaker
 */
export interface PluginContext {
    project?: string;
    client?: unknown;
    $: (strings: TemplateStringsArray, ...values: unknown[]) => Promise<{
        exitCode: number;
        stdout: string;
        stderr: string;
    }>;
    directory: string;
    worktree?: string;
}
export interface ToolExecuteInput {
    tool: string;
    args: Record<string, unknown>;
}
export interface ToolExecuteOutput {
    result?: string;
    error?: string;
}
export interface SkillRule {
    type: string;
    enforcement: string;
    priority: 'critical' | 'high' | 'medium' | 'low';
    promptTriggers: {
        keywords: string[];
        intentPatterns: string[];
    };
}
export interface SkillRules {
    version: string;
    skills: Record<string, SkillRule>;
    complexity_levels: Record<string, {
        keywords: string[];
        auto_skills: string[];
    }>;
}
export interface PatternIssue {
    code: string;
    message: string;
    action: string;
    reference?: string;
}
export interface ValidationResult {
    errors: string[];
    warnings: string[];
    passed: string[];
}
export interface ChatParamsInput {
    message?: {
        text?: string;
    };
}
export interface PluginHooks {
    'chat.params'?: (input: ChatParamsInput, output?: unknown) => Promise<void>;
    'tool.execute.before'?: (input: ToolExecuteInput, output?: ToolExecuteOutput) => Promise<void>;
    'tool.execute.after'?: (input: ToolExecuteInput, output?: ToolExecuteOutput) => Promise<void>;
    event?: (ctx: {
        event: {
            type: string;
            properties?: Record<string, unknown>;
        };
    }) => Promise<void>;
}
export type Plugin = (ctx: PluginContext) => Promise<PluginHooks>;
