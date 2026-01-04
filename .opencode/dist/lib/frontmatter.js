export function parseFrontmatter(content) {
    if (!content.startsWith('---')) {
        return { frontmatter: null, body: content, error: 'No frontmatter found' };
    }
    const endIndex = content.indexOf('---', 3);
    if (endIndex === -1) {
        return { frontmatter: null, body: content, error: 'Unclosed frontmatter' };
    }
    const yamlContent = content.slice(3, endIndex).trim();
    const body = content.slice(endIndex + 3).trim();
    const frontmatter = {};
    for (const line of yamlContent.split('\n')) {
        const colonIndex = line.indexOf(':');
        if (colonIndex > 0) {
            const key = line.slice(0, colonIndex).trim();
            let value = line.slice(colonIndex + 1).trim();
            value = value.replace(/^["']|["']$/g, '');
            frontmatter[key] = value;
        }
    }
    return { frontmatter, body };
}
