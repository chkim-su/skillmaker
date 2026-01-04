import { readFileSync, existsSync } from 'fs'
import { join, dirname } from 'path'

export function findPluginRoot(startPath: string = process.cwd()): string {
  let current = startPath
  const markers = ['.claude-plugin', '.opencode', 'opencode.json']
  
  for (let i = 0; i < 10; i++) {
    for (const marker of markers) {
      if (existsSync(join(current, marker))) {
        return current
      }
    }
    const parent = dirname(current)
    if (parent === current) break
    current = parent
  }
  return startPath
}

export function printBox(title: string, lines: string[], icon = ''): void {
  console.log('')
  console.log('\u2501'.repeat(55))
  console.log(`${icon} ${title}`)
  console.log('\u2501'.repeat(55))
  lines.forEach(line => console.log(`  ${line}`))
  console.log('\u2501'.repeat(55))
  console.log('')
}

export function readJsonFile<T>(path: string): T | null {
  if (!existsSync(path)) return null
  try {
    return JSON.parse(readFileSync(path, 'utf-8')) as T
  } catch {
    return null
  }
}

export function readTextFile(path: string): string | null {
  if (!existsSync(path)) return null
  try {
    return readFileSync(path, 'utf-8')
  } catch {
    return null
  }
}
