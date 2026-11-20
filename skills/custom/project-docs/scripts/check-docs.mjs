#!/usr/bin/env node
/**
 * project-docs check — deterministic checks on touched docs.
 * Usage: node check-docs.mjs <file.md> [more.md ...]
 * Exits 1 when a check fails; prints one line per problem.
 * Never run this on CHANGELOG.md (its format is owned by project-changelog).
 */
import { readFileSync, existsSync } from "node:fs"
import { resolve, dirname } from "node:path"

const files = process.argv.slice(2)
if (files.length === 0) {
  console.error("usage: node check-docs.mjs <file.md> [...]")
  process.exit(2)
}

const SECRET_HINT = /(api[_-]?key|secret|password|token|authorization)\s*[:=]\s*["']?[A-Za-z0-9._\-]{16,}/i
const PLACEHOLDER = /<(actual command|placeholder|TODO|TBD)>/i
let failed = 0

for (const arg of files) {
  const f = resolve(arg)
  const rel = arg.replaceAll("\\", "/")
  if (/CHANGELOG\.md$/i.test(f)) {
    console.log(`skip ${rel}: CHANGELOG.md is owned by project-changelog`)
    continue
  }
  if (!existsSync(f)) {
    console.log(`FAIL ${rel}: file does not exist`)
    failed++
    continue
  }
  const raw = readFileSync(f, "utf8")
  // Skills and agent docs may carry YAML frontmatter; checks apply to the body.
  const text = raw.replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n/, "")
  const relLinks = []
  const re = /\[([^\]]*)\]\(([^)#\s]+)(?:#[^)]*)?\)/g
  let m
  while ((m = re.exec(text))) {
    const href = m[2]
    if (/^(https?:|mailto:|#)/i.test(href)) continue
    if (!existsSync(resolve(dirname(f), decodeURIComponent(href)))) relLinks.push(href)
  }
  for (const href of relLinks) {
    console.log(`FAIL ${rel}: broken relative link -> ${href}`)
    failed++
  }
  if (PLACEHOLDER.test(text)) {
    console.log(`FAIL ${rel}: unfilled placeholder`)
    failed++
  }
  const secret = SECRET_HINT.exec(text)
  if (secret) {
    console.log(`FAIL ${rel}: possible secret (${secret[0].slice(0, 24)}…)`)
    failed++
  }
  const heading = /^#\s+\S/m.test(text)
  if (!heading) {
    console.log(`FAIL ${rel}: no top-level heading`)
    failed++
  }
}

if (failed === 0) console.log(`ok ${files.length} file(s) checked`)
process.exit(failed === 0 ? 0 : 1)
