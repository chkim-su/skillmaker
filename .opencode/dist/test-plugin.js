import { SkillActivation } from './plugin/skill-activation.js';
import { SkillAccessGuard } from './plugin/skill-access-guard.js';
import { PatternCompliance } from './plugin/pattern-compliance.js';
import { validateAll, printValidationResult } from './lib/validation.js';
const mockContext = {
    directory: process.cwd(),
    $: async () => ({ exitCode: 0, stdout: '', stderr: '' })
};
async function testSkillActivation() {
    console.log('\n=== Test: Skill Activation ===\n');
    const plugin = await SkillActivation(mockContext);
    await plugin['chat.params']?.({
        message: { text: 'skill 만들어줘' }
    }, undefined);
    await plugin['chat.params']?.({
        message: { text: 'advanced mcp gateway 설계' }
    }, undefined);
}
async function testSkillAccessGuard() {
    console.log('\n=== Test: Skill Access Guard ===\n');
    const plugin = await SkillAccessGuard(mockContext);
    await plugin['tool.execute.before']?.({
        tool: 'read',
        args: { filePath: '/path/to/skills/my-skill/SKILL.md' }
    }, undefined);
}
async function testPatternCompliance() {
    console.log('\n=== Test: Pattern Compliance ===\n');
    const plugin = await PatternCompliance(mockContext);
    await plugin['tool.execute.before']?.({
        tool: 'task',
        args: { subagent_type: 'skill-architect' }
    }, undefined);
}
async function testValidation() {
    console.log('\n=== Test: Validation ===\n');
    const result = validateAll(process.cwd().replace('/.opencode', ''));
    printValidationResult(result);
}
async function main() {
    console.log('Skillmaker OpenCode Plugin Test\n');
    console.log('Working directory:', process.cwd());
    await testSkillActivation();
    await testSkillAccessGuard();
    await testPatternCompliance();
    await testValidation();
    console.log('\n=== All tests completed ===\n');
}
main().catch(console.error);
