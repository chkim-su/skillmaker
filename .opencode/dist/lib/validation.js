import { existsSync, readdirSync, statSync } from 'fs';
import { join } from 'path';
import { findPluginRoot, readJsonFile, readTextFile } from './utils.js';
import { parseFrontmatter } from './frontmatter.js';
const SKILL_REFERENCES = {
    W028: { skill: 'hook-templates', reference: 'references/full-examples.md', solution: 'PreToolUse/PostToolUse로 행동 강제' },
    W029: { skill: 'skill-design', reference: 'references/structure-rules.md', solution: 'YAML frontmatter: name, description, allowed-tools' },
    W030: { skill: 'orchestration-patterns', reference: 'references/context-isolation.md', solution: 'tools: [] = no MCP access' },
    W031: { skill: 'skill-design', reference: 'references/progressive-disclosure.md', solution: '핵심 <500words' },
    W032: { skill: 'skill-design', reference: 'references/progressive-disclosure.md', solution: 'references/ 디렉토리 생성' },
    W033: { skill: 'orchestration-patterns', reference: 'references/skill-loading-patterns.md', solution: 'Skill() 도구로 명시적 로딩' },
    W034: { skill: 'workflow-state-patterns', reference: 'references/complete-workflow-example.md', solution: '단계별 Skill() 로딩' },
    W035: { skill: 'hook-templates', reference: 'references/full-examples.md', solution: 'PreToolUse hook으로 강제' }
};
function getSkillHint(code) {
    const ref = SKILL_REFERENCES[code];
    if (ref) {
        return `\n       \u2192 skillmaker:${ref.skill} | ${ref.reference} | ${ref.solution}`;
    }
    return '';
}
function validateMarketplaceJson(pluginRoot) {
    const result = { errors: [], warnings: [], passed: [] };
    const marketplacePath = join(pluginRoot, '.claude-plugin', 'marketplace.json');
    if (!existsSync(marketplacePath)) {
        result.errors.push('[E001] marketplace.json not found in .claude-plugin/');
        return result;
    }
    const data = readJsonFile(marketplacePath);
    if (!data) {
        result.errors.push('[E002] marketplace.json is not valid JSON');
        return result;
    }
    if (!data.name)
        result.errors.push('[E003] marketplace.json missing "name" field');
    if (!data.owner?.name)
        result.warnings.push('[W001] marketplace.json missing "owner.name"');
    if (!data.plugins || data.plugins.length === 0) {
        result.errors.push('[E004] marketplace.json missing "plugins" array');
        return result;
    }
    for (const plugin of data.plugins) {
        if (!plugin.name)
            result.errors.push('[E005] Plugin missing "name"');
        const source = plugin.source;
        if (source && typeof source === 'object') {
            if ('type' in source) {
                result.errors.push(`[E006] Use "source" not "type" in source object`);
            }
        }
        for (const skillPath of plugin.skills || []) {
            const fullPath = join(pluginRoot, skillPath, 'SKILL.md');
            if (!existsSync(fullPath)) {
                result.errors.push(`[E007] Skill not found: ${skillPath}`);
            }
        }
        for (const agentPath of plugin.agents || []) {
            const fullPath = join(pluginRoot, agentPath);
            if (!existsSync(fullPath)) {
                result.errors.push(`[E008] Agent not found: ${agentPath}`);
            }
        }
        for (const cmdPath of plugin.commands || []) {
            const fullPath = join(pluginRoot, cmdPath);
            if (!existsSync(fullPath)) {
                result.errors.push(`[E009] Command not found: ${cmdPath}`);
            }
        }
    }
    if (result.errors.length === 0) {
        result.passed.push('[PASS] marketplace.json structure valid');
    }
    return result;
}
function validateSkills(pluginRoot) {
    const result = { errors: [], warnings: [], passed: [] };
    const skillsDir = join(pluginRoot, 'skills');
    if (!existsSync(skillsDir)) {
        result.passed.push('[PASS] No skills directory (optional)');
        return result;
    }
    for (const skillName of readdirSync(skillsDir)) {
        const skillDir = join(skillsDir, skillName);
        if (!statSync(skillDir).isDirectory())
            continue;
        const skillMdPath = join(skillDir, 'SKILL.md');
        if (!existsSync(skillMdPath)) {
            result.errors.push(`[E010] Skill "${skillName}" missing SKILL.md`);
            continue;
        }
        const content = readTextFile(skillMdPath);
        if (!content)
            continue;
        const { frontmatter, body } = parseFrontmatter(content);
        if (!frontmatter) {
            result.warnings.push(`[W029] Skill "${skillName}" missing frontmatter${getSkillHint('W029')}`);
        }
        else {
            if (!frontmatter.name)
                result.warnings.push(`[W029] Skill "${skillName}" frontmatter missing "name"${getSkillHint('W029')}`);
            if (!frontmatter.description)
                result.warnings.push(`[W029] Skill "${skillName}" frontmatter missing "description"${getSkillHint('W029')}`);
        }
        const wordCount = body.split(/\s+/).length;
        if (wordCount > 500) {
            // W031: Decision-first approach for content too long
            const refsDir = join(skillDir, 'references');
            const hasRefs = existsSync(refsDir);
            const w031Msg = [
                `[W031] Skill "${skillName}" exceeds 500 words (${wordCount}).`,
                '',
                '🔍 DECISION REQUIRED - 콘텐츠를 어떻게 처리할지 판단하세요:',
                '',
                '  📋 판단 후 조치:',
                '  ├─ OPTION 1 (권장): references/로 이동',
                '  │   1. references/ 디렉토리 생성',
                '  │   2. 상세 내용을 references/*.md로 이동',
                '  │   3. SKILL.md에는 핵심 내용만 유지 (<500 words)',
                '  │   정보 손실 없이 progressive disclosure 달성',
                '  │',
                '  └─ OPTION 2: 불필요한 내용 정리',
                '      중복/반복/불필요한 내용만 제거',
                '      의미 있는 정보는 반드시 보존',
                '',
                '⛔ 의미 있는 내용을 무작정 삭제하지 마세요 - 정보 손실이 발생합니다.',
                getSkillHint('W031')
            ];
            result.warnings.push(w031Msg.join('\n'));
            if (!hasRefs) {
                result.warnings.push(`[W032] Skill "${skillName}" is long but has no references/ directory${getSkillHint('W032')}`);
            }
        }
        result.passed.push(`[PASS] Skill "${skillName}" structure OK`);
    }
    return result;
}
function validateAgents(pluginRoot) {
    const result = { errors: [], warnings: [], passed: [] };
    const agentsDir = join(pluginRoot, 'agents');
    if (!existsSync(agentsDir)) {
        result.passed.push('[PASS] No agents directory (optional)');
        return result;
    }
    for (const agentFile of readdirSync(agentsDir)) {
        if (!agentFile.endsWith('.md'))
            continue;
        const agentPath = join(agentsDir, agentFile);
        const content = readTextFile(agentPath);
        if (!content)
            continue;
        const agentName = agentFile.replace('.md', '');
        const { frontmatter, body } = parseFrontmatter(content);
        if (!frontmatter) {
            result.warnings.push(`[W030] Agent "${agentName}" missing frontmatter${getSkillHint('W030')}`);
        }
        else {
            if (!frontmatter.name)
                result.warnings.push(`[W030] Agent "${agentName}" frontmatter missing "name"`);
            if (!frontmatter.description)
                result.warnings.push(`[W030] Agent "${agentName}" frontmatter missing "description"`);
            // W030: Check for missing tools field with decision guidance
            if (!('tools' in frontmatter)) {
                const w030Msg = [
                    `[W030] Agent "${agentName}": Missing 'tools' field.`,
                    '',
                    '🔍 DECISION REQUIRED - 이것이 의도적인지 판단하세요:',
                    '',
                    '  📋 판단 후 조치:',
                    '  ├─ YES (의도적, 모든 도구 사용) → 명시적으로 선언',
                    '  │   tools: ["*"]  # 또는 tools 생략 (all tools)',
                    '  │   주석: # Intentionally omitted for full access',
                    '  │',
                    '  └─ NO (실수, 제한 필요) → 필요한 도구만 명시',
                    '      tools: ["Read", "Grep", "Glob"]',
                    '      tools: []  # MCP 도구 없음',
                    '',
                    '⛔ tools 필드 누락을 무시하지 마세요 - 보안에 영향을 줄 수 있습니다.',
                    getSkillHint('W030')
                ];
                result.warnings.push(w030Msg.join('\n'));
            }
        }
        // W033: Check for skills declared but no Skill() usage with decision guidance
        if (frontmatter?.skills) {
            const hasSkillCall = /Skill\s*\(/i.test(body);
            if (!hasSkillCall) {
                const w033Msg = [
                    `[W033] Agent "${agentName}": skills를 선언했지만 Skill() 호출이 없습니다.`,
                    '',
                    '🔍 DECISION REQUIRED - skills 선언이 필요한지 판단하세요:',
                    '',
                    '  📋 판단 후 조치:',
                    '  ├─ YES (skills 사용 필요) → Skill() 호출 추가',
                    '  │   예: Skill("skillmaker:hook-templates")',
                    '  │   agent body에서 필요한 시점에 호출',
                    '  │',
                    '  └─ NO (skills 불필요) → skills 선언 제거',
                    '      frontmatter에서 skills: [...] 제거',
                    '',
                    '⛔ skills 선언만 삭제하고 실제 필요한 기능을 제거하지 마세요.',
                    getSkillHint('W033')
                ];
                result.warnings.push(w033Msg.join('\n'));
            }
        }
        result.passed.push(`[PASS] Agent "${agentName}" structure OK`);
    }
    return result;
}
function analyzeKeywordContext(content, keyword) {
    const pattern = new RegExp(`\\b${keyword}\\b`, 'gi');
    const results = [];
    let match;
    while ((match = pattern.exec(content)) !== null) {
        let likelyFP = false;
        let reason = '';
        // Check for template variable pattern: {keyword_something}
        const templateCheck = content.substring(Math.max(0, match.index - 1), match.index + keyword.length + 20);
        if (new RegExp(`\\{[^}]*${keyword}[^}]*\\}`, 'i').test(templateCheck)) {
            likelyFP = true;
            reason = '템플릿 변수 (e.g., {critical_analysis})';
        }
        // Check for table header pattern: | Keyword |
        const tableCheck = content.substring(Math.max(0, match.index - 3), match.index + keyword.length + 3);
        if (new RegExp(`\\|\\s*${keyword}\\s*\\|`, 'i').test(tableCheck)) {
            likelyFP = true;
            reason = '테이블 헤더';
        }
        // Check if inside code block
        const beforeContent = content.substring(0, match.index);
        const codeOpens = (beforeContent.match(/```/g) || []).length;
        if (codeOpens % 2 === 1) {
            likelyFP = true;
            reason = '코드 블록 내';
        }
        // Check for inline code
        const inlineCheck = content.substring(Math.max(0, match.index - 1), match.index + keyword.length + 1);
        if (new RegExp(`\`[^\`]*${keyword}`, 'i').test(inlineCheck)) {
            likelyFP = true;
            reason = '인라인 코드';
        }
        results.push({
            match: match[0],
            likelyFalsePositive: likelyFP,
            reason
        });
    }
    return results;
}
function validateHookify(pluginRoot) {
    const result = { errors: [], warnings: [], passed: [] };
    const hooksJson = join(pluginRoot, 'hooks', 'hooks.json');
    const hasHooks = existsSync(hooksJson);
    const enforcementKeywords = ['MUST', 'REQUIRED', 'CRITICAL', 'MANDATORY'];
    const dirsToCheck = ['skills', 'agents', 'commands'];
    const filesWithEnforcement = [];
    for (const dir of dirsToCheck) {
        const dirPath = join(pluginRoot, dir);
        if (!existsSync(dirPath))
            continue;
        for (const file of readdirSync(dirPath)) {
            const filePath = join(dirPath, file);
            const stat = statSync(filePath);
            let content = '';
            let relPath = file;
            if (stat.isDirectory()) {
                const skillMd = join(filePath, 'SKILL.md');
                if (existsSync(skillMd)) {
                    content = readTextFile(skillMd) || '';
                    relPath = `${file}/SKILL.md`;
                }
            }
            else if (file.endsWith('.md')) {
                content = readTextFile(filePath) || '';
            }
            if (!content)
                continue;
            const fileMatches = [];
            for (const keyword of enforcementKeywords) {
                const analysis = analyzeKeywordContext(content, keyword);
                fileMatches.push(...analysis);
            }
            if (fileMatches.length > 0) {
                filesWithEnforcement.push({ file: relPath, matches: fileMatches });
            }
        }
    }
    if (filesWithEnforcement.length > 0 && !hasHooks) {
        // Build decision-focused message
        const msgParts = [
            `[W028] ${filesWithEnforcement.length} file(s) contain enforcement keywords.`,
            '',
            '🔍 DECISION REQUIRED - 우회하지 말고 먼저 판단하세요:',
            ''
        ];
        // Show analysis per file (limit to 3)
        for (const { file, matches } of filesWithEnforcement.slice(0, 3)) {
            msgParts.push(`  📄 ${file}:`);
            for (const m of matches.slice(0, 2)) {
                if (m.likelyFalsePositive) {
                    msgParts.push(`     "${m.match}" → ⚠️ ${m.reason} (false positive 가능)`);
                }
                else {
                    msgParts.push(`     "${m.match}" → 🔴 규칙으로 보임 (hook 필요 가능)`);
                }
            }
        }
        msgParts.push('', '📋 판단 후 조치:', '  ├─ YES (진짜 규칙) → hook으로 강제 필요', '  │   경로: /skillmaker:hook-templates 또는 /hookify', '  │   참조: Skill("skillmaker:hook-sdk-integration")', '  │', '  └─ NO (false positive) → 정당한 용어 변경', '      - 테이블 헤더: Required → 필수', '      - 템플릿 변수: {critical_X} → {critique_X}', '      - 또는 hooks/hooks.json 빈 파일 생성 (규칙 없음을 명시)', '', '⛔ 키워드만 바꿔서 경고를 우회하는 것은 금지됩니다.');
        result.warnings.push(msgParts.join('\n'));
    }
    else if (hasHooks) {
        result.passed.push('[PASS] hooks.json present for enforcement');
    }
    else if (filesWithEnforcement.length === 0) {
        result.passed.push('[PASS] No enforcement keywords found (hooks optional)');
    }
    return result;
}
export function validateAll(pluginRoot) {
    const root = pluginRoot || findPluginRoot();
    const result = { errors: [], warnings: [], passed: [] };
    const marketplaceResult = validateMarketplaceJson(root);
    result.errors.push(...marketplaceResult.errors);
    result.warnings.push(...marketplaceResult.warnings);
    result.passed.push(...marketplaceResult.passed);
    const skillsResult = validateSkills(root);
    result.errors.push(...skillsResult.errors);
    result.warnings.push(...skillsResult.warnings);
    result.passed.push(...skillsResult.passed);
    const agentsResult = validateAgents(root);
    result.errors.push(...agentsResult.errors);
    result.warnings.push(...agentsResult.warnings);
    result.passed.push(...agentsResult.passed);
    const hookifyResult = validateHookify(root);
    result.errors.push(...hookifyResult.errors);
    result.warnings.push(...hookifyResult.warnings);
    result.passed.push(...hookifyResult.passed);
    return result;
}
export function printValidationResult(result) {
    console.log('='.repeat(60));
    console.log('PLUGIN VALIDATION');
    console.log('='.repeat(60));
    console.log(`\nSUMMARY:`);
    console.log(`  Errors:   ${result.errors.length}`);
    console.log(`  Warnings: ${result.warnings.length}`);
    console.log(`  Passed:   ${result.passed.length}`);
    if (result.errors.length > 0) {
        console.log('\nERRORS:');
        result.errors.forEach(e => console.log(`  ${e}`));
    }
    if (result.warnings.length > 0) {
        console.log('\nWARNINGS:');
        result.warnings.forEach(w => console.log(`  ${w}`));
    }
    const status = result.errors.length > 0 ? '\u274C ERRORS FOUND'
        : result.warnings.length > 0 ? '\u26A0\uFE0F  WARNINGS'
            : '\u2705 READY FOR DEPLOYMENT';
    console.log(`\nSTATUS: ${status}`);
}
