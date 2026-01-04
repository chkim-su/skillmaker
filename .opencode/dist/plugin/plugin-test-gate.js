import { existsSync } from 'fs';
import { join } from 'path';
import { findPluginRoot, printBox, readJsonFile, readTextFile } from '../lib/utils.js';
const PUBLISH_PATTERNS = ['publish', 'deploy', 'release', 'npm publish', 'gh release'];
function basicValidation(pluginDir) {
    const issues = [];
    const marketplaceJson = join(pluginDir, '.claude-plugin', 'marketplace.json');
    if (existsSync(marketplaceJson)) {
        const data = readJsonFile(marketplaceJson);
        if (!data) {
            issues.push('marketplace.json is invalid JSON');
        }
        else {
            if (!data.name)
                issues.push('marketplace.json missing \'name\'');
            if (!data.plugins)
                issues.push('marketplace.json missing \'plugins\'');
        }
    }
    const commandsDir = join(pluginDir, 'commands');
    if (existsSync(commandsDir)) {
        const { readdirSync } = require('fs');
        for (const file of readdirSync(commandsDir)) {
            if (file.endsWith('.md')) {
                const content = readTextFile(join(commandsDir, file));
                if (content && !content.startsWith('---')) {
                    issues.push(`Command ${file} missing frontmatter`);
                }
            }
        }
    }
    const skillsDir = join(pluginDir, 'skills');
    if (existsSync(skillsDir)) {
        const { readdirSync, statSync } = require('fs');
        for (const dir of readdirSync(skillsDir)) {
            const dirPath = join(skillsDir, dir);
            if (statSync(dirPath).isDirectory()) {
                if (!existsSync(join(dirPath, 'SKILL.md'))) {
                    issues.push(`Skill ${dir} missing SKILL.md`);
                }
            }
        }
    }
    return { passed: issues.length === 0, issues };
}
export const PluginTestGate = async ({ directory, $ }) => {
    const pluginRoot = findPluginRoot(directory);
    const hooks = {
        'tool.execute.before': async (input) => {
            const toolName = input.tool.toLowerCase();
            if (toolName !== 'bash')
                return;
            const command = String(input.args?.command || '').toLowerCase();
            const isPublishCommand = PUBLISH_PATTERNS.some(p => command.includes(p));
            if (!isPublishCommand)
                return;
            const { passed, issues } = basicValidation(pluginRoot);
            if (!passed) {
                printBox('DEPLOYMENT BLOCKED', [
                    `Plugin validation failed: ${pluginRoot}`,
                    '',
                    'Issues found:',
                    ...issues.map(i => `  \u2022 ${i}`),
                    '',
                    'Fix these issues before deploying.'
                ], '\uD83D\uDEAB');
                throw new Error(`Plugin validation failed: ${issues.join(', ')}`);
            }
            printBox('VALIDATION PASSED', [
                `Plugin: ${pluginRoot}`,
                'All checks passed. Proceeding with deployment.'
            ], '\u2705');
        }
    };
    return hooks;
};
export default PluginTestGate;
