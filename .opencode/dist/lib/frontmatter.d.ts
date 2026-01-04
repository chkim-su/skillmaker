export interface Frontmatter {
    [key: string]: string | string[] | undefined;
}
export interface ParseResult {
    frontmatter: Frontmatter | null;
    body: string;
    error?: string;
}
export declare function parseFrontmatter(content: string): ParseResult;
