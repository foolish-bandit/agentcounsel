/**
 * AgentCounsel static site generator.
 *
 * Reads the repository's skills/ directory and emits a plain, static HTML
 * catalog into site/public/. No runtime dependencies — Node standard library
 * only. Run with: npm run build
 */

import {
  readFileSync, writeFileSync, readdirSync, mkdirSync,
  rmSync, existsSync, statSync, copyFileSync,
} from 'node:fs';
import { join, dirname, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const SITE_DIR = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = dirname(SITE_DIR);
const SKILLS_DIR = join(REPO_ROOT, 'skills');
const EXAMPLES_DIR = join(REPO_ROOT, 'examples');
const ASSETS = join(SITE_DIR, 'assets');
const OUT = join(SITE_DIR, 'public');

// Flagship example files at examples/<name>-example.md map back to skills
// that pre-date the per-skill examples/<area>/<slug>/ layout.
const FLAGSHIP_EXAMPLES = {
  'contracts/contract-risk-review': 'contract-review-example.md',
  'privacy/dpa-review': 'dpa-review-example.md',
  'litigation/litigation-chronology': 'litigation-chronology-example.md',
  'product-legal/launch-review': 'product-launch-review-example.md',
  'legal-methodology/red-team-verifier': 'red-team-verifier-example.md',
};

const SECTION_ORDER = [
  'Purpose', 'Use When', 'Required Inputs', 'Do Not Use When',
  'Legal Safety Rules', 'Workflow', 'Output Format',
  'Attorney Verification Checklist',
];

const AREA_META = {
  'legal-research': { name: 'Legal Research', blurb: 'Turning research questions into structured, verifiable memos.' },
  'litigation': { name: 'Litigation', blurb: 'Matter intake, chronologies, demand letters, subpoena triage, depositions, legal holds, privilege logs, claim charts, and brief drafting.' },
  'contracts': { name: 'Contracts', blurb: 'NDAs, commercial contracts, redlines, and statements of work.' },
  'corporate': { name: 'Corporate', blurb: 'Board minutes, written consents, closing checklists, due-diligence review, and entity compliance.' },
  'employment': { name: 'Employment', blurb: 'Terminations, worker classification, hiring, internal investigations, protected leave, severance, and workplace policies.' },
  'privacy': { name: 'Privacy', blurb: 'Data processing agreements, impact assessments, data subject requests, and policy gaps.' },
  'product-legal': { name: 'Product Legal', blurb: 'Launch review, marketing claims, terms of service, and AI features.' },
  'regulatory': { name: 'Regulatory', blurb: 'Enforcement risk, rule-change summaries, and compliance gaps.' },
  'ai-governance': { name: 'AI Governance', blurb: 'AI use-case intake, vendor terms, model risk, and AI policies.' },
  'ip': { name: 'Intellectual Property', blurb: 'Trademark triage, infringement triage, cease-and-desist response, patent and invention triage, DMCA, and open-source licensing.' },
  'financial-crime': { name: 'Financial Crime / AML', blurb: 'KYC onboarding review and sanctions / PEP / adverse-media screening review.' },
  'real-estate': { name: 'Real Estate', blurb: 'Commercial lease abstraction and review, amendment reconciliation, purchase and sale agreement review, title and survey objections, diligence and closing checklists, estoppel and SNDA review, and zoning issue-spotting.' },
  'm-and-a': { name: 'Mergers & Acquisitions', blurb: 'LOI and term-sheet review, acquisition diligence, purchase-agreement and disclosure-schedule review, indemnity and escrow analysis, third-party consents, and closing and post-closing tracking.' },
  'antitrust-competition': { name: 'Antitrust / Competition', blurb: 'Antitrust risk intake, competitor-collaboration and information-sharing review, pricing-algorithm and distribution-restraint review, merger issue-spotting, gun-jumping checklists, and compliance-policy review.' },
  'securities-capital-markets': { name: 'Securities / Capital Markets', blurb: 'Private and public offerings, exemption issue-spotting, offering-document and risk-factor review, SEC filing consistency, Form D and blue-sky tracking, investor-rights and insider-trading review, beneficial-ownership triage, and capital-markets closings.' },
  'tax': { name: 'Tax', blurb: 'Tax issue intake, entity classification facts, transaction tax diligence, sales/use tax nexus triage, employment-tax intake, contract tax-provision review, document organization, international tax issue-spotting, and crypto tax intake.' },
  'bankruptcy-restructuring': { name: 'Bankruptcy / Restructuring', blurb: 'Bankruptcy and creditor-claim intake, proof-of-claim checklists, automatic-stay and preference issue-spotting, executory-contract review, distressed-M&A diligence and asset-sale checklists, restructuring term-sheet review, plan and disclosure-statement issue-spotting, and DIP financing issue-spotting.' },
  'insurance': { name: 'Insurance', blurb: 'Insurance policy summaries, coverage issue-spotting, claim chronologies, reservation of rights and tender review, coverage-position outlines, bad-faith risk triage, certificate of insurance and contract insurance-requirements review, subrogation and recovery tracking, and renewal and placement diligence checklists.' },
  'trusts-estates': { name: 'Trusts & Estates', blurb: 'Estate-planning intake, estate-document summaries, probate document checklists, trust administration and post-death task tracking, fiduciary-duty issue-spotting, beneficiary-designation review, asset and liability inventories, capacity and undue-influence facts organization, estate-litigation chronologies, trust-funding checklists, and estate-tax issue intake.' },
  'family-law': { name: 'Family Law', blurb: 'Family-law matter and divorce intake, custody and parenting facts chronologies and schedule organization, custody-order review, child-support and spousal-support facts intake, asset/debt schedules, settlement-agreement issue-spotting, discovery tracking, hearing preparation, and domestic-violence safety referral.' },
  'legal-methodology': { name: 'Legal Methodology', blurb: 'Cross-cutting analytical disciplines: source validation, citation integrity, assumption audit, hallucination red-team, attorney-review gating, privilege/confidentiality, legal prose, and format compliance.' },
  'legal-ops': { name: 'Legal Operations', blurb: 'Templated legal responses, meeting briefings, and signature-routing checks.' },
  'setup': { name: 'Setup', blurb: 'Cold-start interviews that configure AgentCounsel for a practice group.' },
};

const AREA_ORDER = [
  'legal-research', 'litigation', 'contracts', 'corporate', 'employment',
  'privacy', 'product-legal', 'regulatory', 'ai-governance', 'ip',
  'financial-crime', 'real-estate', 'm-and-a', 'antitrust-competition',
  'securities-capital-markets', 'tax', 'bankruptcy-restructuring', 'insurance',
  'trusts-estates', 'family-law', 'legal-methodology', 'legal-ops', 'setup',
];

// --- small helpers ---------------------------------------------------------

function esc(s) {
  return String(s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function attr(s) {
  return esc(s).replace(/"/g, '&quot;');
}

function slugify(s) {
  return String(s).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
}

function areaName(area) {
  return (AREA_META[area] && AREA_META[area].name) || area;
}

function areaBlurb(area) {
  return (AREA_META[area] && AREA_META[area].blurb) || '';
}

// --- minimal Markdown rendering -------------------------------------------

function inline(text) {
  const codes = [];
  let s = String(text).replace(/`([^`]+)`/g, (m, c) => {
    codes.push(c);
    return '\u0000' + (codes.length - 1) + '\u0000';
  });
  s = esc(s);
  s = s.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g,
    (m, t, u) => '<a href="' + attr(u) + '">' + t + '</a>');
  s = s.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  s = s.replace(/\u0000(\d+)\u0000/g,
    (m, n) => '<code>' + esc(codes[+n]) + '</code>');
  return s;
}

function splitRow(line) {
  let s = line.trim();
  if (s.startsWith('|')) s = s.slice(1);
  if (s.endsWith('|')) s = s.slice(0, -1);
  return s.split('|').map((c) => c.trim());
}

function emitList(items) {
  if (!items.length) return '';
  const tag = items[0].ordered ? 'ol' : 'ul';
  let html = '<' + tag + '>';
  for (const it of items) {
    html += '<li>' + inline(it.text) + emitList(it.children) + '</li>';
  }
  return html + '</' + tag + '>';
}

function renderList(lines) {
  const items = [];
  for (const ln of lines) {
    const m = ln.match(/^(\s*)(\d+\.|[-*+])\s+(.*)$/);
    if (m) {
      items.push({
        indent: m[1].length,
        ordered: /\d/.test(m[2]),
        text: m[3],
        children: [],
      });
    } else if (items.length) {
      items[items.length - 1].text += ' ' + ln.trim();
    }
  }
  const root = [];
  const stack = [{ indent: -1, children: root }];
  for (const it of items) {
    while (stack.length > 1 && it.indent <= stack[stack.length - 1].indent) {
      stack.pop();
    }
    stack[stack.length - 1].children.push(it);
    stack.push(it);
  }
  return emitList(root);
}

function mdToHtml(md) {
  const lines = String(md).replace(/\r\n/g, '\n').split('\n');
  const out = [];
  let i = 0;
  const isSep = (s) => /^[\s|:-]+$/.test(s) && s.includes('-') && s.includes('|');

  while (i < lines.length) {
    const line = lines[i];

    if (/^\s*$/.test(line)) { i++; continue; }

    if (/^\s*```/.test(line)) {
      const buf = [];
      i++;
      while (i < lines.length && !/^\s*```/.test(lines[i])) { buf.push(lines[i]); i++; }
      i++;
      out.push('<pre class="code"><code>' + esc(buf.join('\n')) + '</code></pre>');
      continue;
    }

    const h = line.match(/^(#{1,6})\s+(.*)$/);
    if (h) {
      const lvl = Math.min(h[1].length + 2, 6);
      out.push('<h' + lvl + '>' + inline(h[2].trim()) + '</h' + lvl + '>');
      i++;
      continue;
    }

    if (/^\s*([-*_])\1\1+\s*$/.test(line)) { out.push('<hr>'); i++; continue; }

    if (/^\s*>/.test(line)) {
      const buf = [];
      while (i < lines.length && /^\s*>/.test(lines[i])) {
        buf.push(lines[i].replace(/^\s*>\s?/, ''));
        i++;
      }
      out.push('<blockquote>' + mdToHtml(buf.join('\n')) + '</blockquote>');
      continue;
    }

    if (line.includes('|') && i + 1 < lines.length && isSep(lines[i + 1])) {
      const header = splitRow(line);
      i += 2;
      const rows = [];
      while (i < lines.length && lines[i].includes('|') && lines[i].trim() !== '') {
        rows.push(splitRow(lines[i]));
        i++;
      }
      let t = '<table><thead><tr>';
      for (const c of header) t += '<th>' + inline(c) + '</th>';
      t += '</tr></thead><tbody>';
      for (const r of rows) {
        t += '<tr>';
        for (const c of r) t += '<td>' + inline(c) + '</td>';
        t += '</tr>';
      }
      out.push(t + '</tbody></table>');
      continue;
    }

    if (/^\s*(\d+\.|[-*+])\s+/.test(line)) {
      const buf = [];
      while (i < lines.length &&
        (/^\s*(\d+\.|[-*+])\s+/.test(lines[i]) ||
          (/^\s+\S/.test(lines[i]) && lines[i].trim() !== ''))) {
        buf.push(lines[i]);
        i++;
      }
      out.push(renderList(buf));
      continue;
    }

    const buf = [];
    while (i < lines.length && lines[i].trim() !== '' &&
      !/^\s*(#{1,6}\s|>|```)/.test(lines[i]) &&
      !/^\s*([-*_])\1\1+\s*$/.test(lines[i]) &&
      !/^\s*(\d+\.|[-*+])\s+/.test(lines[i])) {
      buf.push(lines[i]);
      i++;
    }
    if (buf.length) out.push('<p>' + inline(buf.join(' ').trim()) + '</p>');
  }
  return out.join('\n');
}

// --- skill loading ---------------------------------------------------------

function stripQuotes(s) {
  if (s.length >= 2) {
    const first = s[0], last = s[s.length - 1];
    if ((first === '"' && last === '"') || (first === "'" && last === "'")) {
      return s.slice(1, -1);
    }
  }
  return s;
}

function parseListField(fmLines, field) {
  const out = [];
  for (let i = 0; i < fmLines.length; i++) {
    if (fmLines[i].match(new RegExp('^' + field + '\\s*:\\s*$'))) {
      for (let j = i + 1; j < fmLines.length; j++) {
        const m = fmLines[j].match(/^\s+-\s+(.+)$/);
        if (m) { out.push(stripQuotes(m[1].trim())); continue; }
        if (/^\S/.test(fmLines[j])) break;
      }
      break;
    }
  }
  return out;
}

function parseSkill(text) {
  const lines = text.split('\n');
  let name = '';
  let description = '';
  let inputs = [];
  let outputs = [];
  let bodyStart = 0;
  if (lines[0] && lines[0].trim() === '---') {
    let fmEnd = -1;
    for (let i = 1; i < lines.length; i++) {
      if (lines[i].trim() === '---') { fmEnd = i; break; }
    }
    if (fmEnd > 0) {
      const fmLines = lines.slice(1, fmEnd);
      const fm = fmLines.join('\n');
      const nm = fm.match(/^name:\s*(.+)$/m);
      if (nm) name = stripQuotes(nm[1].trim());
      const dm = fm.match(/^description:\s*(.+)$/m);
      if (dm) description = stripQuotes(dm[1].trim());
      inputs = parseListField(fmLines, 'inputs');
      outputs = parseListField(fmLines, 'outputs');
      bodyStart = fmEnd + 1;
    }
  }
  const body = lines.slice(bodyStart).join('\n');
  const h1m = body.match(/^#\s+(.+)$/m);
  const h1 = h1m ? h1m[1].trim() : name;
  const sections = {};
  const marks = [];
  const re = /^##\s+(.+)$/gm;
  let m;
  while ((m = re.exec(body))) {
    marks.push({ name: m[1].trim(), start: m.index, contentStart: m.index + m[0].length });
  }
  for (let j = 0; j < marks.length; j++) {
    const end = j + 1 < marks.length ? marks[j + 1].start : body.length;
    sections[marks[j].name] = body.slice(marks[j].contentStart, end).trim();
  }
  return { name: name || h1, description, inputs, outputs, h1, sections };
}

function firstUseWhenBullet(skill) {
  const bullets = useWhenBullets(skill);
  return bullets.length ? bullets[0] : '';
}

function loadSkills() {
  const skills = [];
  const repoPrefix = resolve(REPO_ROOT) + sep;
  for (const area of readdirSync(SKILLS_DIR)) {
    const areaDir = join(SKILLS_DIR, area);
    if (!statSync(areaDir).isDirectory()) continue;
    for (const slug of readdirSync(areaDir)) {
      const sd = join(areaDir, slug);
      if (slug === 'references' || !statSync(sd).isDirectory()) continue;
      const mdPath = join(sd, 'SKILL.md');
      if (!existsSync(mdPath)) continue;
      const raw = readFileSync(mdPath, 'utf8');
      const parsed = parseSkill(raw);
      const specFile = join(sd, 'SPEC.json');
      let specPath = '';
      let specRaw = '';
      let spec = null;
      const specResources = [];
      if (existsSync(specFile)) {
        specPath = 'skills/' + area + '/' + slug + '/SPEC.json';
        specRaw = readFileSync(specFile, 'utf8');
        try {
          spec = JSON.parse(specRaw);
        } catch (err) {
          throw new Error('Invalid JSON in ' + specPath + ': ' + err.message);
        }
        if (!spec || Array.isArray(spec) || typeof spec !== 'object') {
          throw new Error(specPath + ' must contain a JSON object');
        }
        for (const module of spec.modules || []) {
          if (!module || typeof module !== 'object' || Array.isArray(module)) {
            throw new Error(specPath + ' contains a non-object module record');
          }
          if (!module.id || typeof module.id !== 'string') {
            throw new Error(specPath + ' contains a module without an id');
          }
          if (!module.path || typeof module.path !== 'string') {
            throw new Error(specPath + ' module ' + module.id + ' has no path');
          }
          const resourceFile = resolve(REPO_ROOT, module.path);
          if (!resourceFile.startsWith(repoPrefix)) {
            throw new Error(specPath + ' module ' + module.id + ' escapes the repository root');
          }
          if (!existsSync(resourceFile) || !statSync(resourceFile).isFile()) {
            throw new Error(specPath + ' module ' + module.id + ' is missing: ' + module.path);
          }
          specResources.push({ ...module, content: readFileSync(resourceFile, 'utf8') });
        }
      }
      skills.push({
        area, slug, raw,
        path: 'skills/' + area + '/' + slug + '/SKILL.md',
        specPath, specRaw, spec, specResources,
        ...parsed,
      });
    }
  }
  return skills;
}

function loadSkillMeta() {
  const indexPath = join(REPO_ROOT, 'metadata', 'index.json');
  if (!existsSync(indexPath)) return {};
  const meta = JSON.parse(readFileSync(indexPath, 'utf8'));
  const byPath = {};
  for (const s of meta.skills || []) {
    if (s.path) byPath[s.path] = s;
  }
  return byPath;
}

const EVAL_STATUS_LABELS = {
  'scored': 'Scored eval',
  'automated-static': 'Automated (static) eval',
  'manual-ready': 'Manual eval ready',
  'manual-eval-ready': 'Manual eval ready',
  'unrun': 'Eval not yet run',
};

function skillFactsPanel(m) {
  if (!m) return '';
  const rows = [];
  const row = (label, value) => {
    if (value) rows.push(`<tr><th scope="row">${esc(label)}</th><td>${value}</td></tr>`);
  };
  row('Practice area', esc(areaName(m.practice_area || '')));
  row('Category', esc(m.category || ''));
  row('Risk level', m.risk_level ? `<span class="risk risk-${esc(m.risk_level)}">${esc(m.risk_level)}</span>` : '');
  const qc = (m.recommended_quality_checks || []).map((q) => `<code>${esc(q)}</code>`).join(' ');
  row('Recommended quality checks', qc);
  row('Eval coverage', esc(EVAL_STATUS_LABELS[m.eval_status] || m.eval_status || ''));
  row('Compatible platforms', esc((m.compatible_platforms || []).join(', ')));
  const rel = (m.related_skills || [])
    .map((p) => {
      const mm = p.match(/^skills\/([^/]+)\/([^/]+)\/SKILL\.md$/);
      return mm ? `<a href="../../skills/${mm[1]}/${mm[2]}.html">${esc(mm[2].replace(/-/g, ' '))}</a>` : esc(p);
    })
    .join(', ');
  row('Related skills', rel);
  if (!rows.length) return '';
  return `<div class="skill-facts">
<h2>At a glance</h2>
<table class="facts-table"><tbody>
${rows.join('\n')}
</tbody></table>
</div>
`;
}

function useWhenBullets(skill) {
  const sec = skill.sections['Use When'] || '';
  return sec.split('\n')
    .filter((l) => /^\s*[-*]\s+/.test(l))
    .map((l) => l.replace(/^\s*[-*]\s+/, '').replace(/\*\*/g, '').replace(/`/g, '').trim());
}

// --- HTML layout -----------------------------------------------------------

function page({ title, depth, desc, body, search }) {
  const r = depth === 0 ? '' : '../'.repeat(depth);
  const searchHead = search
    ? `<link rel="stylesheet" href="${r}pagefind/pagefind-ui.css">\n`
    : '';
  const searchScripts = search
    ? `<script src="${r}pagefind/pagefind-ui.js"></script>
<script>
(function () {
  var box = document.getElementById('search');
  var fallback = document.getElementById('search-fallback');
  if (typeof PagefindUI !== 'undefined') {
    new PagefindUI({ element: '#search', showSubResults: true });
  } else if (fallback) {
    fallback.hidden = false;
    if (box) box.hidden = true;
  }
})();
</script>
`
    : '';
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(title)} — AgentCounsel</title>
<meta name="description" content="${attr(desc || 'AgentCounsel legal skills catalog.')}">
<link rel="stylesheet" href="${r}style.css">
${searchHead}</head>
<body>
<a class="skip-link" href="#main-content">Skip to content</a>
<header class="site-header">
  <a class="brand" href="${r}index.html">AgentCounsel</a>
  <nav class="site-nav">
    <a href="${r}concepts/index.html">How it works</a>
    <a href="${r}skill-index.html">Skill index</a>
    <a href="${r}index.html#practice-areas">Practice areas</a>
    <a href="${r}packs/index.html">Packs</a>
    <a href="${r}platforms/index.html">Platform setup</a>
    <a href="${r}llms.txt">llms.txt</a>
  </nav>
</header>
<main id="main-content" data-pagefind-body>
${body}
</main>
<footer class="site-footer">
  <div class="site-footer-inner">
    <div>
      <p class="site-footer-title">AgentCounsel</p>
      <p>AgentCounsel is an open, Markdown-native legal skills library. Every output is
      <strong>draft legal work product for review by a licensed attorney</strong> — not legal advice,
      and not a substitute for a qualified lawyer.</p>
    </div>
    <div>
      <p class="site-footer-heading">Catalog</p>
      <ul class="site-footer-links">
        <li><a href="${r}index.html">Home</a></li>
        <li><a href="${r}skill-index.html">Skill index</a></li>
        <li><a href="${r}index.html#practice-areas">Practice areas</a></li>
      </ul>
    </div>
    <div>
      <p class="site-footer-heading">Reference</p>
      <ul class="site-footer-links">
        <li><a href="${r}concepts/index.html">How it works</a></li>
        <li><a href="${r}packs/index.html">Packs</a></li>
        <li><a href="${r}platforms/index.html">Platform setup</a></li>
        <li><a href="${r}llms.txt">llms.txt</a></li>
      </ul>
    </div>
  </div>
</footer>
<script src="${r}app.js"></script>
${searchScripts}</body>
</html>
`;
}

function searchSection() {
  return `<section class="site-search" id="site-search">
<h2>Search the catalog</h2>
<div id="search"></div>
<p class="search-fallback" id="search-fallback" hidden>Full-text search isn't available in this
local preview — it's built by the CI deploy step (Pagefind indexes the published site). Meanwhile,
use the filter box below or browse by practice area.</p>
</section>
`;
}

const REVIEW_NOTICE = `<div class="notice">
<strong>Every output is draft legal work product for review by a licensed attorney.</strong>
AgentCounsel does not provide legal advice and is not a substitute for a qualified lawyer.
A licensed legal professional must review and adopt every output before it is relied upon.
</div>`;

// --- page builders ---------------------------------------------------------

function buildHome(skills, byArea) {
  let cards = '';
  for (const area of AREA_ORDER) {
    const list = byArea[area] || [];
    if (!list.length) continue;
    cards += `<a class="card" href="practice-areas/${area}.html">
<h3>${esc(areaName(area))}</h3>
<p class="count">${list.length} skill${list.length === 1 ? '' : 's'}</p>
<p>${esc(areaBlurb(area))}</p>
</a>\n`;
  }
  const body = `<section class="hero">
<h1>AgentCounsel</h1>
<p class="lead">An open, Markdown-native library of legal skills for AI agents — and the legal professionals who supervise them.</p>
</section>

${searchSection()}

<section>
<h2>What this is</h2>
<p>AgentCounsel is a <strong>platform-agnostic legal AI skills library</strong>. Each skill is a
structured workflow that tells an AI agent — or a lawyer — how to scope a task, what inputs to
gather, how to organize the work, and what a supervising attorney must verify.</p>
<p>It is not tied to any one AI product, and it carries no build system or runtime. The skills are
plain Markdown that works wherever an agent or person can read text. The library supplies process
and structure, not the law itself, and is jurisdiction-agnostic.</p>
${REVIEW_NOTICE}
</section>

<section>
<h2>Start here</h2>
<ul class="quicklinks">
<li><a href="skill-index.html">Browse the full skill index</a> — every skill in the library, in one list.</li>
<li><a href="#practice-areas">Jump to a practice area</a> — skills grouped by area of law.</li>
<li><a href="platforms/index.html">Platform setup</a> — how to use AgentCounsel in ChatGPT, Claude, Gemini, repo agents, or a one-off prompt.</li>
</ul>
</section>

<section>
<h2>Beyond a single skill</h2>
<p>Most tasks are one skill. When the work is larger, four surfaces organize it — all plain Markdown, no backend:</p>
<ul class="quicklinks">
<li><strong>Matter workspaces</strong> — a scaffold for one matter (parties, facts, sources, deadlines, outputs, attorney review). Choose a workspace over a single skill when the work is multi-step, document-heavy, high-risk, ongoing, jurisdiction- or deadline-sensitive, or source/citation-heavy. Initialize with <code>py scripts/init_matter_workspace.py "&lt;matter name&gt;" --practice-area &lt;area&gt;</code> from the canonical template at <code>matter-workspaces/_template/</code>.</li>
<li><strong>Playbooks</strong> — repeatable recipes for a recurring task type (NDA review, demand letter, DPA review), adding default client-position questions, risk-tolerance settings, required sources, and required quality checks on top of a skill.</li>
<li><strong>Review panels</strong> — a supervised multi-pass review of a draft (issue spotter, source/citation, client-position, privilege, business-risk), ending with the attorney gatekeeper. The passes are structured review passes, not autonomous agents and not lawyers; the output stays attorney-supervised draft work product.</li>
<li><strong>Matter packs</strong> — ordered sequences of skills for a recurring matter type.</li>
</ul>
<p>See <code>WORKFLOW_ROUTER.md</code>, <code>docs/MATTER_WORKSPACES.md</code>, <code>docs/PLAYBOOKS.md</code>, and <code>docs/REVIEW_PANELS.md</code> for when to choose each.</p>
</section>

<section id="practice-areas">
<h2>Practice areas</h2>
<div class="grid">
${cards}</div>
</section>`;
  return page({
    title: 'AgentCounsel — Legal skills catalog',
    depth: 0,
    desc: 'An open, platform-agnostic legal AI skills library. Every output is draft legal work product for review by a licensed attorney.',
    body,
    search: true,
  });
}

function buildSkillIndex(skills, byArea) {
  let body = `<nav class="breadcrumb"><a href="index.html">Home</a> / <span>Skill index</span></nav>
<h1>Skill index</h1>
<p class="lead">All ${skills.length} skills in the library, grouped by practice area. Each skill produces draft legal work product for review by a licensed attorney.</p>

${searchSection()}

<input type="search" class="skill-filter" id="skill-filter" placeholder="Filter skills (try 'nda', 'privacy', 'antitrust')...">`;
  for (const area of AREA_ORDER) {
    const list = byArea[area] || [];
    if (!list.length) continue;
    let rows = '';
    for (const s of list) {
      const ft = attr(areaName(area) + ' ' + s.name + ' ' + s.description);
      rows += `<tr data-filter-row data-filter-text="${ft}">
<td><a href="skills/${area}/${s.slug}.html">${esc(s.name)}</a></td>
<td>${inline(s.description)}</td>
</tr>\n`;
    }
    body += `\n<section>
<h2><a href="practice-areas/${area}.html">${esc(areaName(area))}</a></h2>
<table class="index-table">
<thead><tr><th>Skill</th><th>Agent trigger description</th></tr></thead>
<tbody>
${rows}</tbody>
</table>
</section>`;
  }
  return page({ title: 'Skill index', depth: 0, desc: 'The full AgentCounsel skill index.', body, search: true });
}

function buildAreaPage(area, list) {
  let cards = '';
  for (const s of list) {
    const useWhen = s.sections['Use When'] || '';
    const inputs = s.sections['Required Inputs'] || '';
    const ft = attr(s.name + ' ' + s.description);
    cards += `<article class="skill-card" data-filter-row data-filter-text="${ft}">
<h2><a href="../skills/${area}/${s.slug}.html">${esc(s.name)}</a></h2>
<p class="desc">${inline(s.description)}</p>
<details><summary>When to use</summary>${mdToHtml(useWhen)}</details>
<details><summary>Required inputs</summary>${mdToHtml(inputs)}</details>
<p class="more"><a href="../skills/${area}/${s.slug}.html">Open full skill &rarr;</a></p>
</article>\n`;
  }
  const body = `<nav class="breadcrumb"><a href="../index.html">Home</a> / <a href="../skill-index.html">Skill index</a> / <span>${esc(areaName(area))}</span></nav>
<h1>${esc(areaName(area))}</h1>
<p class="lead">${esc(areaBlurb(area))}</p>
<p class="muted">${list.length} skill${list.length === 1 ? '' : 's'} in this practice area. Every skill produces draft legal work product for review by a licensed attorney.</p>
<input type="search" class="skill-filter" id="skill-filter" placeholder="Filter ${esc(areaName(area))} skills...">
${cards}`;
  return page({
    title: areaName(area), depth: 1,
    desc: areaBlurb(area), body,
  });
}

function fullSkillPackage(skill) {
  if (!skill.spec) return skill.raw;
  const parts = [
    `AgentCounsel selective execution package for ${skill.name}.

The core skill always applies. Choose one declared execution mode and evaluate each module's machine-readable activation object exactly. Missing activation inputs fail closed: do not load every conditional module. A module without activation is not selected unless it is required or explicitly requested. Use only the selected resources, preserve why each resource was selected, and keep every parent safety rule active.

This portable package contains every possible resource. For true prompt-size reduction, use the MCP get_skill_context tool or another client that sends only the selected bundle.

=== BEGIN AGENTCOUNSEL CORE SKILL ===
${skill.raw}
=== END AGENTCOUNSEL CORE SKILL ===

=== BEGIN AGENTCOUNSEL SPEC ===
Canonical path: ${skill.specPath}
${skill.specRaw}
=== END AGENTCOUNSEL SPEC ===`,
  ];
  for (const resource of skill.specResources) {
    parts.push(`=== BEGIN AGENTCOUNSEL MODULE: ${resource.id} ===
Kind: ${resource.kind || 'resource'}
Canonical path: ${resource.path}
Load when: ${resource.load_when || 'explicit selection'}

${resource.content}
=== END AGENTCOUNSEL MODULE: ${resource.id} ===`);
  }
  return parts.join('\n\n');
}

function oneOffPrompt(skill) {
  const packageText = fullSkillPackage(skill);
  const selectiveRule = skill.spec
    ? `\n- This skill has a typed execution contract. Choose a declared mode, evaluate every module activation exactly, and treat missing activation inputs as unresolved rather than loading all modules.`
    : '';
  return `You are assisting with a legal task using AgentCounsel, a platform-agnostic legal skills library. Use the skill package provided below and follow it exactly.

Operating rules (these always apply):
- Produce draft legal work product for review by a licensed attorney. This is not legal advice and not a final answer.
- Never invent legal authority, citations, quotations, facts, or deadlines. Mark every gap with a visible placeholder such as [CONFIRM: ...] or [VERIFY: ...].
- Identify jurisdiction, governing law, posture, and the relevant date — or flag them as unknown. Never compute a deadline.
- Keep facts, assumptions, analysis, strategy, and verification items visibly separate.
- Follow the skill's Workflow and Output Format. Complete its Attorney Verification Checklist.
- If a Required Input is missing, stop and ask for it. Do not guess.${selectiveRule}

=== BEGIN AGENTCOUNSEL EXECUTION PACKAGE: ${skill.name} ===
${packageText}
=== END AGENTCOUNSEL EXECUTION PACKAGE ===

First, confirm which Required Inputs you have and ask me for any that are missing. Then proceed with the Workflow.`;
}

function activationSummary(module) {
  const activation = module.activation;
  if (!activation || typeof activation !== 'object') {
    return module.required
      ? 'Required; no conditional activation.'
      : 'Explicit selection only; no machine-readable activation.';
  }
  const modes = Array.isArray(activation.modes) ? activation.modes.join(', ') : 'none';
  if (activation.operator === 'always') return 'Modes: ' + modes + '; always within an allowed mode.';
  if (activation.operator === 'present') {
    return 'Modes: ' + modes + '; when ' + activation.input_id + ' is present.';
  }
  if (activation.operator === 'equals') {
    return 'Modes: ' + modes + '; when ' + activation.input_id + ' equals ' + activation.value + '.';
  }
  if (activation.operator === 'contains-any') {
    return 'Modes: ' + modes + '; when ' + activation.input_id + ' contains any of: '
      + (activation.values || []).join(', ') + '.';
  }
  return 'Unsupported activation operator: ' + String(activation.operator || 'missing') + '.';
}

function selectiveExecutionPanel(skill) {
  if (!skill.spec) return '';
  const modes = (skill.spec.execution_modes || [])
    .filter((mode) => mode && mode.enabled !== false)
    .map((mode) => mode.id)
    .filter(Boolean);
  const scenarioCount = Array.isArray(skill.spec.context_scenarios)
    ? skill.spec.context_scenarios.length : 0;
  let rows = '';
  let details = '';
  for (const resource of skill.specResources) {
    rows += `<tr>
<td><code>${esc(resource.id)}</code></td>
<td>${esc(resource.kind || 'resource')}</td>
<td>${esc(activationSummary(resource))}</td>
<td><code>${esc(resource.path)}</code></td>
</tr>\n`;
    details += `<details class="module-detail">
<summary>Module: ${esc(resource.id)}</summary>
<p class="path">Canonical path: <code>${esc(resource.path)}</code></p>
${mdToHtml(resource.content)}
</details>\n`;
  }
  return `<section class="skill-section selective-package" id="selective-execution-package">
<h2>Selective execution package</h2>
<p>This skill has a typed execution contract at <code>${esc(skill.specPath)}</code>. Its compact core is suitable for routing and quick triage. Standard or deep execution also needs the resources selected by the contract.</p>
<p><strong>Selection rule:</strong> choose a declared mode and evaluate each module's machine-readable activation object exactly. Missing activation inputs fail closed. Do not load every conditional module merely because an input is absent.</p>
<div class="package-facts">
<p><span class="label">Declared modes:</span> ${esc(modes.join(', ') || 'See the compiled contract')}</p>
<p><span class="label">Budget scenarios:</span> ${scenarioCount}</p>
<p><span class="label">Portable copy:</span> “Copy Full Package” includes every possible resource, so it is complete but not context-minimal. Use MCP <code>get_skill_context</code> for the exact selected bundle.</p>
</div>
<table class="module-table">
<thead><tr><th>Module</th><th>Kind</th><th>Activation</th><th>Canonical path</th></tr></thead>
<tbody>${rows}</tbody>
</table>
<details class="module-detail">
<summary>Typed contract: SPEC.json</summary>
<pre class="code"><code>${esc(skill.specRaw)}</code></pre>
</details>
${details}</section>\n`;
}

// --- examples --------------------------------------------------------------

function loadExamples(skills) {
  const map = {};
  for (const s of skills) {
    const key = s.area + '/' + s.slug;
    const dir = join(EXAMPLES_DIR, s.area, s.slug);
    const out = join(dir, 'sample-output.md');
    const req = join(dir, 'sample-request.md');
    if (existsSync(out)) {
      map[key] = {
        kind: 'per-skill',
        output: readFileSync(out, 'utf8'),
        request: existsSync(req) ? readFileSync(req, 'utf8') : '',
        htmlRel: 'examples/' + s.area + '/' + s.slug + '.html',
      };
      continue;
    }
    const flagship = FLAGSHIP_EXAMPLES[key];
    if (flagship) {
      const fp = join(EXAMPLES_DIR, flagship);
      if (existsSync(fp)) {
        map[key] = {
          kind: 'flagship',
          output: readFileSync(fp, 'utf8'),
          request: '',
          htmlRel: 'examples/' + flagship.replace(/\.md$/, '.html'),
        };
      }
    }
  }
  return map;
}

function buildExamplePage(skill, ex) {
  const depth = ex.htmlRel.split('/').length - 1;
  const r = '../'.repeat(depth);
  let body = `<nav class="breadcrumb"><a href="${r}index.html">Home</a> / <a href="${r}practice-areas/${skill.area}.html">${esc(areaName(skill.area))}</a> / <a href="${r}skills/${skill.area}/${skill.slug}.html">${esc(skill.name)}</a> / <span>Sample output</span></nav>
<h1>Sample output: ${esc(skill.name)}</h1>
<p class="lead">This is an illustrative sample of what the <a href="${r}skills/${skill.area}/${skill.slug}.html">${esc(skill.name)}</a> skill produces. Every party, date, document, and fact is <strong>fictional</strong> — invented for illustration only.</p>
${REVIEW_NOTICE}
`;
  if (ex.request) {
    body += `<section class="skill-section">
<h2>The fictional scenario</h2>
${mdToHtml(ex.request)}
</section>
`;
  }
  body += `<section class="skill-section">
<h2>What the skill produced</h2>
${mdToHtml(ex.output)}
</section>`;
  return page({
    title: 'Sample: ' + skill.name, depth,
    desc: 'Illustrative sample output for the ' + skill.name + ' skill — fictional facts, draft work product, not legal advice.',
    body,
  });
}

function buildSkillPage(skill, example, meta) {
  const a = skill.area;
  let sections = '';
  for (const name of SECTION_ORDER) {
    const content = skill.sections[name];
    if (!content) continue;
    sections += `<section class="skill-section" id="${slugify(name)}">
<h2>${esc(name)}</h2>
${mdToHtml(content)}
</section>\n`;
  }
  const summaryLines = [];
  if (skill.outputs && skill.outputs.length) {
    summaryLines.push(`<p><span class="label">What this produces:</span> ${esc(skill.outputs.join('; '))}</p>`);
  }
  if (skill.inputs && skill.inputs.length) {
    summaryLines.push(`<p><span class="label">What you give it:</span> ${esc(skill.inputs.join('; '))}</p>`);
  }
  const firstUseWhen = firstUseWhenBullet(skill);
  if (firstUseWhen) {
    summaryLines.push(`<p><span class="label">When to use it:</span> ${inline(firstUseWhen)}</p>`);
  }
  const summaryBlock = summaryLines.length
    ? `<div class="skill-summary">
${summaryLines.join('\n')}
</div>
`
    : '';

  let exampleBlock;
  if (example) {
    exampleBlock = `<div class="example-callout">
<strong>See sample output</strong> &mdash; <a href="../../${example.htmlRel}">View an illustrative sample of what this skill produces &rarr;</a>
</div>
`;
  } else {
    exampleBlock = `<p class="example-missing">Example output not yet available.</p>
`;
  }

  const copyToolbar = skill.spec
    ? `<button class="btn" type="button" data-copy="raw">Copy Core Skill</button>
<button class="btn" type="button" data-copy="package">Copy Full Package</button>
<button class="btn" type="button" data-copy="oneoff">Copy One-Off Prompt</button>`
    : `<button class="btn" type="button" data-copy="raw">Copy Full Skill</button>
<button class="btn" type="button" data-copy="oneoff">Copy One-Off Prompt</button>`;
  const packageText = fullSkillPackage(skill);
  const packagePanel = selectiveExecutionPanel(skill);
  const rawTitle = skill.spec ? 'Core raw SKILL.md' : 'Full raw SKILL.md';

  const body = `<nav class="breadcrumb"><a href="../../index.html">Home</a> / <a href="../../practice-areas/${a}.html">${esc(areaName(a))}</a> / <span>${esc(skill.name)}</span></nav>
<h1>${esc(skill.name)}</h1>
<p class="path">Canonical path: <code>${esc(skill.path)}</code></p>

<div class="toolbar">
${copyToolbar}
</div>

<div class="trigger">
<h2>Agent Trigger Description</h2>
<p>${inline(skill.description)}</p>
</div>

${summaryBlock}${skillFactsPanel(meta)}${exampleBlock}${packagePanel}
${sections}<section class="skill-section" id="raw-skill">
<h2>${rawTitle}</h2>
<pre id="raw" class="raw">${esc(skill.raw)}</pre>
</section>

<pre id="package" hidden>${esc(packageText)}</pre>
<pre id="oneoff" hidden>${esc(oneOffPrompt(skill))}</pre>`;
  return page({
    title: skill.name, depth: 2,
    desc: skill.description, body,
  });
}

// --- platform pages --------------------------------------------------------

const PLATFORMS = [
  {
    slug: 'chatgpt-projects',
    title: 'ChatGPT Projects',
    lead: 'ChatGPT Projects group related chats and let you attach files and custom instructions that apply to every conversation in the Project.',
    steps: [
      'Create a new Project in ChatGPT.',
      'Attach AgentCounsel’s operating rules: copy the six files from the repository’s <code>core/</code> directory into the Project files, or paste them into the Project’s custom instructions. These safety rules apply to every skill.',
      'For a task, open the skill you need from the <a href="../skill-index.html">skill index</a>. Use <strong>Copy Full Skill</strong> for an ordinary skill. When the page offers a typed package, use <strong>Copy Full Package</strong> for standard or deep work; <strong>Copy Core Skill</strong> is the compact routing and quick triage path.',
      'Give ChatGPT the skill’s Required Inputs — the document, the facts, the client role, the jurisdiction.',
      'Follow the skill’s Workflow, then review the result against its Attorney Verification Checklist before relying on it.',
    ],
    tips: [
      'Load one skill per task. Do not paste the whole library into a Project.',
      'The <code>core/</code> rules can stay attached to the Project and be reused across many tasks.',
      'The <strong>Copy One-Off Prompt</strong> button gives you a single self-contained prompt that already includes the operating rules.',
    ],
  },
  {
    slug: 'claude-projects',
    title: 'Claude Projects',
    lead: 'Claude Projects keep a shared knowledge base and instructions across every conversation in the Project.',
    steps: [
      'Create a new Project in Claude.',
      'Add AgentCounsel’s operating rules to the Project knowledge: upload the six files from the repository’s <code>core/</code> directory.',
      'Open the skill you need from the <a href="../skill-index.html">skill index</a>. Use <strong>Copy Full Skill</strong> for an ordinary skill. When a typed package is shown, use <strong>Copy Full Package</strong> for standard or deep work; the compact <strong>Copy Core Skill</strong> option is for routing and quick triage.',
      'Provide the skill’s Required Inputs and ask Claude to follow the skill’s Workflow.',
      'Review the output against the skill’s Attorney Verification Checklist.',
    ],
    tips: [
      'AgentCounsel ships a Claude Code plugin bundle at <code>adapters/claude-code-plugin/</code> and a local-folder playbook at <code>adapters/claude-cowork/</code> for Claude Code users.',
      'Keep one skill active per task; the <code>core/</code> rules can stay in Project knowledge.',
    ],
  },
  {
    slug: 'gemini-notebooks',
    title: 'Gemini Notebooks',
    lead: 'Use AgentCounsel with Gemini by adding the skill files as notebook sources, so the model can read and follow them.',
    steps: [
      'Create a notebook or workspace in your Gemini environment.',
      'Add AgentCounsel’s operating rules as sources: the six files from the repository’s <code>core/</code> directory.',
      'Add the skill you need as another source. Use <strong>Copy Full Skill</strong> for an ordinary skill. When a typed package is shown, use <strong>Copy Full Package</strong> for standard or deep work; <strong>Copy Core Skill</strong> is the compact quick triage path.',
      'Ask Gemini to follow the skill’s Workflow and Output Format, and provide the Required Inputs.',
      'Review the output against the skill’s Attorney Verification Checklist.',
    ],
    tips: [
      'AgentCounsel also ships a Gemini CLI extension at <code>adapters/gemini/</code>. Installing the repository as an extension loads the operating model automatically.',
      'Add only the skills you need as sources; the library is large.',
    ],
  },
  {
    slug: 'codex-repo-agents',
    title: 'Codex / repo agents',
    lead: 'Repo-based coding and legal agents — such as Codex — can use AgentCounsel directly from a checkout of the repository.',
    steps: [
      'Give the agent access to a checkout of the AgentCounsel repository.',
      'Point the agent at <code>adapters/codex/AGENTS.md</code> — the repo-agent instructions that explain how to work in the library.',
      'The agent routes a task with <code>WORKFLOW_ROUTER.md</code> to the narrowest relevant skill, or uses a command from <code>COMMANDS.md</code>.',
      'It reads the <code>core/</code> rules and the selected <code>SKILL.md</code>, then follows the Workflow.',
      'It produces draft legal work product and completes the Attorney Verification Checklist.',
    ],
    tips: [
      '<code>COMMANDS.md</code> maps slash-style commands (for example <code>/contracts:nda</code>) to skills.',
      'The agent should select one narrow skill per task rather than loading the whole library.',
    ],
  },
  {
    slug: 'one-off-prompt',
    title: 'One-off prompt use',
    lead: 'For a single task in any AI assistant — no Project, no setup — paste one skill as a self-contained prompt.',
    steps: [
      'Open the page for the skill you need from the <a href="../skill-index.html">skill index</a>.',
      'Click <strong>Copy One-Off Prompt</strong>. The copied text wraps the skill with AgentCounsel’s operating rules and, when present, its typed contract plus every selectable resource.',
      'Paste it into any AI assistant.',
      'Provide the Required Inputs the skill asks for.',
      'Follow the Workflow, then review the output against the Attorney Verification Checklist.',
    ],
    tips: [
      'For repeated work, prefer a Project or notebook so the operating rules persist across tasks.',
      'Use <strong>Copy Full Skill</strong> for an ordinary raw <code>SKILL.md</code>. On typed pages, <strong>Copy Core Skill</strong> copies only the compact core and <strong>Copy Full Package</strong> includes the contract and resources.',
    ],
  },
];

function buildPlatformPage(p) {
  const steps = p.steps.map((s) => '<li>' + s + '</li>').join('\n');
  const tips = p.tips.map((s) => '<li>' + s + '</li>').join('\n');
  const body = `<nav class="breadcrumb"><a href="../index.html">Home</a> / <a href="index.html">Platform setup</a> / <span>${esc(p.title)}</span></nav>
<h1>${esc(p.title)}</h1>
<p class="lead">${p.lead}</p>

<section>
<h2>Setup</h2>
<ol>
${steps}
</ol>
</section>

<section>
<h2>Tips</h2>
<ul>
${tips}
</ul>
</section>

${REVIEW_NOTICE}`;
  return page({ title: p.title, depth: 1, desc: p.lead, body });
}

function buildPacksPage() {
  const indexPath = join(REPO_ROOT, 'metadata', 'index.json');
  if (!existsSync(indexPath)) return null;
  const meta = JSON.parse(readFileSync(indexPath, 'utf8'));
  const packsMetaPath = join(REPO_ROOT, 'metadata', 'packs.json');
  const packsMeta = existsSync(packsMetaPath)
    ? JSON.parse(readFileSync(packsMetaPath, 'utf8'))
    : null;
  const areas = {};
  for (const s of meta.skills || []) {
    const a = s.practice_area;
    if (!a) continue;
    (areas[a] = areas[a] || []).push(s);
  }
  const packByArea = {};
  if (packsMeta && Array.isArray(packsMeta.packs)) {
    for (const p of packsMeta.packs) {
      if (!p.practice_area || !p.platform || p.practice_area === 'all') continue;
      (packByArea[p.practice_area] = packByArea[p.practice_area] || {})[p.platform] = p;
    }
  }

  const baseName = (p) => {
    const mm = String(p).match(/([^/]+)\.md$/);
    return mm ? mm[1] : String(p).replace(/\/$/, '').split('/').pop();
  };
  let rows = '';
  let details = '';
  for (const a of AREA_ORDER) {
    const list = areas[a] || [];
    if (!list.length) continue;
    const manifest = packByArea[a] || {};
    const anyPack = Object.values(manifest)[0] || {};
    const platforms = Object.keys(manifest).sort().join(', ') || 'chatgpt, claude, gemini';
    const checks = [...new Set(Object.values(manifest).flatMap((p) => p.included_quality_checks || []))];
    const playbooks = [...new Set(Object.values(manifest).flatMap((p) => p.included_playbooks || []))];
    const panels = [...new Set(Object.values(manifest).flatMap((p) => p.included_review_panels || []))];
    const reqs = anyPack.attorney_review_requirements || [];
    rows += `<tr>
<td>${esc(areaName(a))}</td>
<td class="count">${list.length}</td>
<td>${esc(platforms)}</td>
<td class="count">${checks.length || '—'}</td>
<td class="count">${playbooks.length || '—'}</td>
<td class="count">${panels.length || '—'}</td>
<td><a href="chatgpt/${a}.md">ChatGPT (.md)</a> · <a href="claude/${a}.zip">Claude (.zip)</a> · <a href="gemini/${a}.zip">Gemini (.zip)</a></td>
</tr>\n`;

    const skillSlug = (s) => {
      const mm = String(s.path || s.id || '').match(/skills\/[^/]+\/([^/]+)/) || String(s.id || '').match(/[^/]+\/(.+)$/);
      return mm ? mm[1] : slugify(s.title || s.name || '');
    };
    const skillItems = list.map((s) => `<li><a href="../skills/${a}/${skillSlug(s)}.html">${esc(s.title || s.name || s.id)}</a></li>`).join('');
    const checkItems = checks.map((c) => `<code>${esc(c)}</code>`).join(' ') || '—';
    const pbItems = playbooks.map((p) => `<code>${esc(baseName(p))}</code>`).join(' ') || '—';
    const panelItems = panels.map((p) => `<code>${esc(baseName(p))}</code>`).join(' ') || '—';
    const reqItems = reqs.map((r) => `<li>${esc(r)}</li>`).join('') || '<li>A licensed attorney must review and adopt all outputs before reliance.</li>';
    details += `<details class="pack-detail">
<summary><strong>${esc(areaName(a))}</strong> — ${list.length} skills · platforms: ${esc(platforms)}</summary>
<p><span class="label">Use case:</span> practice-area legal workflow pack. Upload one file; the agent routes to the matching skill.</p>
<p><span class="label">Included quality checks:</span> ${checkItems}</p>
<p><span class="label">Included playbooks:</span> ${pbItems}</p>
<p><span class="label">Included review panels:</span> ${panelItems}</p>
<p><span class="label">Attorney-review requirements:</span></p>
<ul>${reqItems}</ul>
<p><span class="label">Setup:</span> ${esc(anyPack.setup_instructions || 'Upload the pack to your AI tool and apply the global safety rules.')}</p>
<p><span class="label">Included skills:</span></p>
<ul class="pack-skill-list">${skillItems}</ul>
</details>\n`;
  }

  const body = `<nav class="breadcrumb"><a href="../index.html">Home</a> / <span>Packs</span></nav>
<h1>Practice-area packs</h1>
<p class="lead">A platform pack is one file you upload to your AI tool's project or workspace. It bundles the global safety rules, the practice profile, the slash commands, and every skill in a practice area — so you can start work without copying files one at a time.</p>

${REVIEW_NOTICE}

<section>
<h2>Downloads</h2>
<p>The generated <a href="packs.json">pack manifest</a> lists each pack's platform, included skills, core rules, templates, quality checks, matter-pack references, workspace templates, setup instructions, and attorney-review requirements.</p>
<table class="index-table">
<thead><tr><th>Practice area</th><th>Skills</th><th>Platforms</th><th>Quality checks</th><th>Playbooks</th><th>Panels</th><th>Downloads</th></tr></thead>
<tbody>
${rows}</tbody>
</table>
</section>

<section>
<h2>What each pack includes</h2>
<p>Expand a practice area to see its included skills, quality checks, playbooks, review panels, attorney-review requirements, and setup instructions. The authoritative manifest is <a href="packs.json">packs.json</a>.</p>
${details}</section>

<section>
<h2>Repo agents (Cursor, Codex, Claude Code)</h2>
<p>For agents that run against a local checkout, use the repo-agent packs instead of the per-practice-area files:</p>
<ul class="quicklinks">
<li><a href="repo-agents/AGENTS.md">AGENTS.md</a> &mdash; Codex and repo-agent instructions.</li>
<li><a href="repo-agents/CLAUDE.md">CLAUDE.md</a> &mdash; Claude Code instructions.</li>
<li><a href="repo-agents/README.md">README.md</a> &mdash; how the repo-agent packs work.</li>
</ul>
</section>

<section>
<h2>How to use a pack</h2>
<h3>ChatGPT</h3>
<ol>
<li>In ChatGPT, create a new Project for the practice area.</li>
<li>Upload the practice area's <code>.md</code> file to the Project's files.</li>
<li>In the Project instructions, paste: <em>"Follow the AgentCounsel pack in the Project files. Apply the global safety rules to every task. Use the practice profile and the skill that matches the request. Produce draft legal work product for attorney review — not legal advice."</em></li>
<li>Start a chat, name the task, and let ChatGPT route to the right skill.</li>
</ol>

<h3>Claude</h3>
<ol>
<li>In Claude, create a new Project for the practice area.</li>
<li>Unzip the <code>.zip</code> and upload its contents to the Project knowledge — or upload the zip directly if your Claude environment accepts it.</li>
<li>In the Project's custom instructions, paste the same AgentCounsel operating instruction shown for ChatGPT above.</li>
<li>Start a chat and describe the task.</li>
</ol>

<h3>Gemini</h3>
<ol>
<li>Create a notebook or workspace in your Gemini environment.</li>
<li>Unzip the <code>.zip</code> and add its contents as sources, or upload the zip if your environment accepts it.</li>
<li>Tell Gemini to follow the AgentCounsel pack and apply the safety rules. Provide the Required Inputs for the skill that matches the task.</li>
</ol>

<h3>Repo agents (Cursor, Codex, Claude Code)</h3>
<ol>
<li>Copy <code>AGENTS.md</code> (Codex) or <code>CLAUDE.md</code> (Claude Code) into your project root.</li>
<li>The agent loads the operating rules and routes the task to the narrowest skill.</li>
</ol>
</section>

<section>
<h2>What every pack contains</h2>
<ul>
<li>The global safety rules from <code>core/</code> — the rules every skill inherits.</li>
<li>The practice profile and command list for the practice area.</li>
<li>Every <code>SKILL.md</code> in the practice area, with workflow and attorney-verification checklist.</li>
<li>A "How to use this pack" header keyed to the target platform.</li>
</ul>
<p>Packs are regenerated on every push to <code>main</code>; the canonical library under <a href="../skill-index.html">skills/</a> is always the source of truth.</p>
</section>`;

  return page({
    title: 'Packs', depth: 1,
    desc: 'Pre-built AgentCounsel platform packs — one file per practice area for ChatGPT, Claude, Gemini, and repo agents.',
    body,
  });
}

const REPO_BLOB = 'https://github.com/zgbrenner/agentcounsel/blob/main';

function buildConceptsPage() {
  const body = `<nav class="breadcrumb"><a href="../index.html">Home</a> / <span>How it works</span></nav>
<h1>How AgentCounsel works</h1>
<p class="lead">AgentCounsel is a Markdown-native legal skills library. Most tasks are a single skill; larger work uses packs, matter workspaces, playbooks, review panels, and a quality layer. Everything is plain Markdown — no backend, no account, no lock-in.</p>

${REVIEW_NOTICE}

<section>
<h2>Skills</h2>
<p>Each <a href="../skill-index.html">skill</a> is one workflow with a fixed structure (Purpose, Use When, Required Inputs, Do Not Use When, Legal Safety Rules, Workflow, Output Format, Attorney Verification Checklist). Browse by <a href="../index.html#practice-areas">practice area</a>.</p>
</section>

<section>
<h2>Packs</h2>
<p><a href="../packs/index.html">Practice-area packs</a> bundle every skill in an area — plus the safety rules and commands — into one file you upload to ChatGPT, Claude, or Gemini, with repo-agent variants for Cursor, Codex, and Claude Code. Packs are available for multiple AI tools.</p>
</section>

<section>
<h2>Quality layer</h2>
<p>Cross-cutting quality checks review a draft before it is relied upon: source validation, citation integrity, assumption audit, hallucination red-team, privilege/confidentiality review, prose polish, output-format compliance, and the attorney-review gate. See <a href="${REPO_BLOB}/docs/QUALITY_LAYER.md">docs/QUALITY_LAYER.md</a>.</p>
</section>

<section>
<h2>Evals and benchmarks</h2>
<p>Lightweight, no-API evals check structure, routing, metadata, packs, and candidate-output safety signals. They <strong>do not verify legal correctness</strong> and do not replace attorney review. See <a href="${REPO_BLOB}/docs/EVALS.md">docs/EVALS.md</a> and the <a href="${REPO_BLOB}/reports/eval-coverage.md">coverage report</a>.</p>
</section>

<section>
<h2>Matter workspaces</h2>
<p>A <a href="${REPO_BLOB}/docs/MATTER_WORKSPACES.md">matter workspace</a> organizes one matter — parties, facts, sources, deadlines, outputs, and attorney review — as plain Markdown. Start one with <code>py scripts/init_matter_workspace.py</code> from the canonical multi-file template. Choose a workspace over a single skill when the work is multi-step, document-heavy, or deadline-sensitive.</p>
</section>

<section>
<h2>Playbooks</h2>
<p><a href="${REPO_BLOB}/docs/PLAYBOOKS.md">Playbooks</a> are repeatable recipes for recurring task types (NDA review, demand letter, DPA review) — default questions, risk-tolerance settings, required sources, and required quality checks on top of a skill.</p>
</section>

<section>
<h2>Review panels</h2>
<p><a href="${REPO_BLOB}/docs/REVIEW_PANELS.md">Review panels</a> run a draft through several supervised review passes (issue spotter, source/citation, client-position, privilege, business-risk) ending with the attorney gatekeeper. The passes are review passes — not autonomous agents and not lawyers.</p>
</section>

<section>
<h2>Platform compatibility</h2>
<p>AgentCounsel runs in ChatGPT, Claude, Gemini, Cursor, Codex, Claude Code, and plain Markdown. See <a href="../platforms/index.html">platform setup</a> and <a href="${REPO_BLOB}/docs/PLUGIN_COMPATIBILITY.md">docs/PLUGIN_COMPATIBILITY.md</a>.</p>
</section>

<section>
<h2>Workflow router</h2>
<p>Not sure which surface to use? The <a href="${REPO_BLOB}/WORKFLOW_ROUTER.md">workflow router</a> maps "I need to do X" to the right skill or surface, and <a href="${REPO_BLOB}/docs/CHOOSE_YOUR_WORKFLOW.md">docs/CHOOSE_YOUR_WORKFLOW.md</a> is a decision guide with worked examples.</p>
</section>

<section>
<h2>Contributing</h2>
<p>AgentCounsel is open source under Apache-2.0. See <a href="${REPO_BLOB}/CONTRIBUTING.md">CONTRIBUTING.md</a> for how to add skills, quality checks, evals, playbooks, review panels, and packs — and the safety rules that are not negotiable.</p>
</section>`;
  return page({
    title: 'How it works', depth: 1,
    desc: 'How AgentCounsel works — skills, packs, the quality layer, evals, matter workspaces, playbooks, and review panels. Every output is draft work product for attorney review.',
    body,
  });
}

function buildPlatformIndex() {
  let items = '';
  for (const p of PLATFORMS) {
    items += `<li><a href="${p.slug}.html">${esc(p.title)}</a> &mdash; ${p.lead}</li>\n`;
  }
  const body = `<nav class="breadcrumb"><a href="../index.html">Home</a> / <span>Platform setup</span></nav>
<h1>Platform setup</h1>
<p class="lead">How to use AgentCounsel in common AI environments. The library is plain Markdown, so it works anywhere an agent or person can read text.</p>
<ul class="quicklinks">
${items}</ul>
${REVIEW_NOTICE}`;
  return page({ title: 'Platform setup', depth: 1, desc: 'How to use AgentCounsel across AI platforms.', body });
}

// --- llms.txt files --------------------------------------------------------

function buildLlms(skills, byArea) {
  let txt = '# AgentCounsel\n\n';
  txt += '> AgentCounsel is an open, Markdown-native, platform-agnostic legal skills library. '
    + 'Each skill is a structured workflow that produces draft legal work product for review by a '
    + 'licensed attorney. It does not provide legal advice.\n\n';
  txt += '## Purpose\n\n';
  txt += 'AgentCounsel gives AI agents and legal professionals a consistent, reviewable way to draft '
    + 'and triage legal work. Each skill defines how to scope a task, what inputs to gather, how to '
    + 'structure the output, and what a supervising attorney must verify. The library supplies process '
    + 'and structure, not the law itself, and is jurisdiction-agnostic. Every output is draft legal '
    + 'work product; a licensed legal professional must review and adopt it before it is relied upon.\n\n';
  txt += '## Practice areas\n\n';
  for (const area of AREA_ORDER) {
    if (!(byArea[area] || []).length) continue;
    txt += '- ' + areaName(area) + ': ' + areaBlurb(area) + '\n';
  }
  txt += '\n## Top-level links\n\n';
  txt += '- Skill index: skill-index.html\n';
  txt += '- Practice area pages: practice-areas/\n';
  txt += '- Platform setup: platforms/index.html\n';
  txt += '- Full skill data: llms-full.txt\n';
  txt += '- Canonical skill library (repository): skills/\n';
  txt += '- Core operating rules (repository): core/\n\n';
  txt += '## Skill index summary\n\n';
  for (const area of AREA_ORDER) {
    for (const s of byArea[area] || []) {
      txt += '- [' + areaName(area) + '] ' + s.name + ': ' + s.description + '\n';
    }
  }
  return txt + '\n';
}

function buildLlmsFull(skills, byArea) {
  let txt = '# AgentCounsel — Full Skill Data\n\n';
  txt += '> Full catalog of every AgentCounsel skill: name, repository path, catalog page, trigger '
    + 'description, and a use-when summary. Every skill produces draft legal work product for review '
    + 'by a licensed attorney; AgentCounsel does not provide legal advice.\n\n';
  txt += 'Total skills: ' + skills.length + '\n';
  let areaCount = 0;
  for (const area of AREA_ORDER) if ((byArea[area] || []).length) areaCount++;
  txt += 'Practice areas: ' + areaCount + '\n\n';
  for (const area of AREA_ORDER) {
    const list = byArea[area] || [];
    if (!list.length) continue;
    txt += '## ' + areaName(area) + ' (' + list.length + ' skill'
      + (list.length === 1 ? '' : 's') + ')\n\n';
    for (const s of list) {
      txt += '### ' + s.name + '\n';
      txt += 'Path: ' + s.path + '\n';
      txt += 'Catalog page: skills/' + area + '/' + s.slug + '.html\n';
      txt += 'Trigger: ' + s.description + '\n';
      const bullets = useWhenBullets(s);
      if (bullets.length) {
        txt += 'Use when:\n';
        for (const b of bullets) txt += '  - ' + b + '\n';
      }
      txt += '\n';
    }
  }
  return txt;
}

// --- write ----------------------------------------------------------------

function write(relPath, content) {
  const fp = join(OUT, relPath);
  mkdirSync(dirname(fp), { recursive: true });
  writeFileSync(fp, content);
}

function main() {
  if (!existsSync(SKILLS_DIR)) {
    console.error('Cannot find skills/ directory at ' + SKILLS_DIR);
    process.exit(1);
  }
  const skills = loadSkills();
  skills.sort((a, b) => a.name.localeCompare(b.name));
  const metaByPath = loadSkillMeta();
  const byArea = {};
  for (const s of skills) (byArea[s.area] = byArea[s.area] || []).push(s);
  for (const area of Object.keys(byArea)) {
    byArea[area].sort((a, b) => a.name.localeCompare(b.name));
  }

  // Wipe site/public, but preserve any preexisting site/public/packs/
  // (the CI workflow copies dist/* into packs/ before this runs).
  if (existsSync(OUT)) {
    for (const entry of readdirSync(OUT)) {
      if (entry === 'packs') continue;
      rmSync(join(OUT, entry), { recursive: true, force: true });
    }
  } else {
    mkdirSync(OUT, { recursive: true });
  }

  let count = 0;

  write('index.html', buildHome(skills, byArea));
  count++;
  write('skill-index.html', buildSkillIndex(skills, byArea));
  count++;

  for (const area of AREA_ORDER) {
    if (!(byArea[area] || []).length) continue;
    write('practice-areas/' + area + '.html', buildAreaPage(area, byArea[area]));
    count++;
  }

  const examples = loadExamples(skills);
  for (const s of skills) {
    const ex = examples[s.area + '/' + s.slug];
    write('skills/' + s.area + '/' + s.slug + '.html', buildSkillPage(s, ex, metaByPath[s.path]));
    count++;
  }
  for (const s of skills) {
    const ex = examples[s.area + '/' + s.slug];
    if (!ex) continue;
    write(ex.htmlRel, buildExamplePage(s, ex));
    count++;
  }

  write('concepts/index.html', buildConceptsPage());
  count++;
  write('platforms/index.html', buildPlatformIndex());
  count++;
  for (const p of PLATFORMS) {
    write('platforms/' + p.slug + '.html', buildPlatformPage(p));
    count++;
  }

  const packsPage = buildPacksPage();
  if (packsPage) {
    write('packs/index.html', packsPage);
    count++;
  }

  write('llms.txt', buildLlms(skills, byArea));
  write('llms-full.txt', buildLlmsFull(skills, byArea));

  copyFileSync(join(ASSETS, 'style.css'), join(OUT, 'style.css'));
  copyFileSync(join(ASSETS, 'app.js'), join(OUT, 'app.js'));

  console.log('AgentCounsel site generated -> ' + OUT);
  console.log('  ' + skills.length + ' skills across '
    + Object.keys(byArea).length + ' practice areas');
  console.log('  ' + count + ' HTML pages + llms.txt + llms-full.txt + assets');
}

main();
