#!/usr/bin/env node
/**
 * project-docs audit — read-only inventory and validation of .agent-docs/.
 * Usage: node audit.mjs <repo-root>
 * Prints a JSON report; exits 0 always (audit reports, never fails builds).
 */
import { readdirSync, readFileSync, statSync, existsSync } from "node:fs"
import { join, relative, resolve, dirname, posix } from "node:path"

const root = resolve(process.argv[2] ?? process.cwd())
const docsDir = join(root, ".agent-docs")
const agentsFile = join(root, "AGENTS.md")

const SECRET_HINT = /(api[_-]?key|secret|password|token|authorization)\s*[:=]\s*["']?[A-Za-z0-9._\-]{16,}/i
const PLACEHOLDER = /<(actual command|placeholder|TODO|TBD)>|<[a-z-]+ command>/i
const STALE_MONTHS = 6

function listFiles(dir) {
  const out = []
  if (!existsSync(dir) || !statSync(dir).isDirectory()) return out
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (entry.name.startsWith(".") || entry.name === "node_modules") continue
    const p = join(dir, entry.name)
    if (statSync(p).isDirectory()) out.push(...listFiles(p))
    else out.push(p)
  }
  return out
}

function checkLinks(file, text) {
  const broken = []
  const re = /\[([^\]]*)\]\(([^)#\s]+)(?:#[^)]*)?\)/g
  let m
  while ((m = re.exec(text))) {
    const href = m[2]
    if (/^(https?:|mailto:|#)/i.test(href)) continue
    const target = resolve(dirname(file), decodeURIComponent(href))
    if (!existsSync(target)) broken.push(href)
  }
  return broken
}

const files = listFiles(docsDir)
if (existsSync(agentsFile)) files.push(agentsFile)

const docReports = []
for (const f of files) {
  const rel = relative(root, f).replaceAll("\\", "/")
  const isChangelog = /CHANGELOG\.md$/i.test(f)
  const text = readFileSync(f, "utf8")
  const report = { file: rel, lines: text.split(/\r\n|\r|\n/).length }
  if (!isChangelog) {
    report.brokenLinks = checkLinks(f, text)
    report.placeholders = PLACEHOLDER.test(text)
    const secret = SECRET_HINT.exec(text)
    if (secret) report.possibleSecret = secret[0].slice(0, 40) + "…"
  }
  const reviewed = /last reviewed:\s*(\d{4}-\d{2}-\d{2})/i.exec(text)
  if (reviewed) {
    const age = (Date.now() - new Date(reviewed[1]).getTime()) / 2_629_800_000
    report.lastReviewedMonthsAgo = Math.floor(age)
    if (age > STALE_MONTHS) report.stale = true
  }
  docReports.push(report)
}

const orphanChanges = docReports
  .filter((d) => /^\.agent-docs\/changes\//.test(d.file))
  .map((d) => d.file)

console.log(JSON.stringify(
  {
    root,
    hasDocsDir: existsSync(docsDir),
    hasChangelog: existsSync(join(docsDir, "CHANGELOG.md")),
    hasAgentsFile: existsSync(agentsFile),
    docs: docReports,
    orphans: { changePlans: orphanChanges },
    summary: {
      files: docReports.length,
      brokenLinks: docReports.reduce((n, d) => n + (d.brokenLinks?.length ?? 0), 0),
      placeholders: docReports.filter((d) => d.placeholders).length,
      stale: docReports.filter((d) => d.stale).length,
      possibleSecrets: docReports.filter((d) => d.possibleSecret).length,
    },
  },
  null,
  2,
))
