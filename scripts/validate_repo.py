#!/usr/bin/env python3
"""AgentCounsel repository validation.

Lightweight structural and consistency checks for the AgentCounsel legal
skills library. Standard library only — no third-party packages, no build
tools. Run from anywhere:

    python scripts/validate_repo.py

Exit code 0 if all checks pass, 1 if any error is found. Warnings do not
affect the exit code. See VALIDATION.md for details.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Allow importing sibling scripts (e.g. sync_plugin_skills) when run directly.
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


# Required H2 sections for every canonical skill, in order. The bare titles are
# defined once in _shared; validate_repo enforces the heading form and order.
from _shared import REQUIRED_SECTIONS as _SECTION_TITLES
REQUIRED_SECTIONS = ["## " + title for title in _SECTION_TITLES]

# Content-scan file types.
TEXT_SUFFIXES = {".md", ".json", ".py", ".txt"}

# Directory names under skills/<area>/ that hold shared reference material,
# not a skill. They have no SKILL.md and are not catalogued as skills.
NON_SKILL_DIRS = {"references"}

# Top-level directories (and the contract references folder) the library
# expects to exist. Checked by check_repo_layout.
EXPECTED_DIRS = [
    "core",
    "skills",
    "adapters",
    "connectors",
    "practice-profiles",
    "matter-workspaces",
    "matter-workspaces/_template",
    "matter-plans",
    "playbooks",
    "review-panels",
    "overlays",
    "skills/setup",
    "skills/legal-methodology",
    "skills/contracts/references",
]


from _shared import split_frontmatter


def strip_code(text: str) -> str:
    """Remove fenced and inline code spans, so example link or badge
    syntax shown inside code is not mistaken for a real link."""
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.sub(r"`[^`\n]+`", "", text)
    return text


def canonical_skill_dirs() -> list[Path]:
    base = REPO_ROOT / "skills"
    dirs: list[Path] = []
    if not base.is_dir():
        err("skills/ directory not found")
        return dirs
    for area in sorted(p for p in base.iterdir() if p.is_dir()):
        for skill in sorted(p for p in area.iterdir() if p.is_dir()):
            if skill.name in NON_SKILL_DIRS:
                continue
            dirs.append(skill)
    return dirs


def plugin_skill_dirs() -> list[Path]:
    base = REPO_ROOT / "adapters" / "claude-code-plugin" / "skills"
    if not base.is_dir():
        return []
    return sorted(p for p in base.iterdir() if p.is_dir())


def iter_text_files():
    for path in sorted(REPO_ROOT.rglob("*")):
        if not path.is_file():
            continue
        # Skip VCS internals and generated build output (dist/ is produced by
        # scripts/build_platform_packs.py; node_modules by the site tooling).
        if {".git", "dist", "node_modules"} & set(path.parts):
            continue
        if path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def excluded_from_content_scan(path: Path) -> bool:
    """The validator and its docs legitimately mention the forbidden strings."""
    parts = path.relative_to(REPO_ROOT).parts
    if parts and parts[0] == "scripts":
        return True
    if path.name == "VALIDATION.md":
        return True
    return False


# --- Check: expected repository layout ------------------------------------

def check_repo_layout() -> None:
    """Confirm the directories the library is organized around exist."""
    for relpath in EXPECTED_DIRS:
        path = REPO_ROOT / relpath
        if not path.is_dir():
            err(f"expected directory '{relpath}/' is missing")
        elif not any(p.name != ".gitkeep" for p in path.iterdir()):
            warn(f"directory '{relpath}/' is empty")


# --- Check: overlays structure --------------------------------------------

def check_overlays() -> None:
    """Every overlay folder under overlays/ contains an OVERLAY.md.

    overlays/ holds industry and regulatory overlays — profiles and
    reference packs that tune existing skills for a sector. Overlays are
    not skills. Folders whose name starts with '_' (such as _template)
    are scaffolding and are skipped. See overlays/README.md."""
    base = REPO_ROOT / "overlays"
    if not base.is_dir():
        return
    for sub in sorted(p for p in base.iterdir() if p.is_dir()):
        if sub.name.startswith("_"):
            continue
        if not (sub / "OVERLAY.md").is_file():
            err(f"{rel(sub)}: missing OVERLAY.md")


# --- Check: skill structure ------------------------------------------------

def check_skill(skill_dir: Path, require_sections: bool) -> None:
    md = skill_dir / "SKILL.md"
    if not md.is_file():
        err(f"{rel(skill_dir)}: missing SKILL.md")
        return
    text = md.read_text(encoding="utf-8")
    frontmatter, body = split_frontmatter(text)
    if frontmatter is None:
        err(f"{rel(md)}: missing or unterminated YAML frontmatter "
            f"(file must start with '---' and have a closing '---')")
        return
    fm_text = "\n".join(frontmatter)
    if not re.search(r"^name:\s*\S", fm_text, re.M):
        err(f"{rel(md)}: frontmatter is missing a non-empty 'name:' field")
    if not re.search(r"^description:\s*\S", fm_text, re.M):
        err(f"{rel(md)}: frontmatter is missing a non-empty 'description:' field")

    if not re.search(r"^#\s+\S", body, re.M):
        err(f"{rel(md)}: missing an H1 title ('# Skill Name')")

    if not require_sections:
        return

    positions: dict[str, int] = {}
    for section in REQUIRED_SECTIONS:
        match = re.search(rf"^{re.escape(section)}\s*$", body, re.M)
        if match is None:
            err(f"{rel(md)}: missing required section '{section}'")
        else:
            positions[section] = match.start()
    found_order = [positions[s] for s in REQUIRED_SECTIONS if s in positions]
    if found_order != sorted(found_order):
        err(f"{rel(md)}: required sections are present but out of order")


# --- Check: forbidden phrasing --------------------------------------------

def check_whitespace() -> None:
    """Flag trailing whitespace and missing final newlines in text files so
    the drift the audit found cannot silently recur. Same file set as the
    other content scans; generated output under dist/ is skipped."""
    for path in iter_text_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        for i, line in enumerate(text.split("\n"), 1):
            if line != line.rstrip():
                err(f"{rel(path)}:{i}: trailing whitespace")
                break  # one report per file is enough
        if text and not text.endswith("\n"):
            err(f"{rel(path)}: missing final newline")


def check_content_scans() -> None:
    forbidden = ["chatgpt project instructions", "chatgpt project package"]
    advice_pat = re.compile(
        r"(provides?|gives?|offers?|renders?)\s+(final\s+)?legal\s+advice"
        r"|\bis\s+legal\s+advice",
        re.I,
    )
    negation_pat = re.compile(
        r"(\bnot\b|\bnever\b|\bno\b|\bnone\b|\bneither\b|\bcannot\b|n't)", re.I)
    todo_pat = re.compile(r"\bTODO\b|\bFIXME\b|lorem ipsum", re.I)

    for path in iter_text_files():
        if excluded_from_content_scan(path):
            continue
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for phrase in forbidden:
            if phrase in lowered:
                err(f"{rel(path)}: contains forbidden phrase '{phrase}'")
        for match in advice_pat.finditer(text):
            window = text[max(0, match.start() - 48):match.start()]
            if not negation_pat.search(window):
                snippet = match.group(0).strip()
                err(f"{rel(path)}: appears to state that AgentCounsel "
                    f"provides legal advice ('{snippet}') — outputs must be "
                    f"described as draft legal work product for attorney review")
        for match in todo_pat.finditer(text):
            err(f"{rel(path)}: leftover placeholder marker '{match.group(0)}'")


# --- Check: quality-layer overclaims --------------------------------------

_QUALITY_LIMIT_FILES = [
    "docs/QUALITY_LAYER.md",
    "docs/SOURCE_VALIDATION.md",
    "docs/CITATION_INTEGRITY.md",
    "docs/ATTORNEY_REVIEW_GATE.md",
    "skills/legal-methodology/source-validation/SKILL.md",
    "skills/legal-methodology/citation-integrity-check/SKILL.md",
]

_OVERCLAIM_PATTERNS = [
    re.compile(r"\bguarantees?\s+(legal\s+)?(correctness|accuracy|citation)", re.I),
    re.compile(r"\bcertif(?:y|ies)\s+(legal\s+)?(correctness|accuracy|citation)", re.I),
    re.compile(r"\bindependently\s+verif(?:y|ies)\s+(current\s+)?law", re.I),
    re.compile(r"\bautomatically\s+verif(?:y|ies)\s+(current\s+)?law", re.I),
    re.compile(r"\bautomated\s+legal\s+citation\s+verification\b", re.I),
]

_LIMITING_LANGUAGE = re.compile(
    r"\b(not|does\s+not|do\s+not|cannot|no|never|without|unless)\b",
    re.I,
)


def check_quality_layer_overclaims() -> None:
    """Quality-layer docs must not imply automated legal verification.

    AgentCounsel can classify source support and citation risk, but it does
    not independently verify current law or certify citation correctness.
    """
    for relpath in _QUALITY_LIMIT_FILES:
        path = REPO_ROOT / relpath
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        sentences = re.split(r"(?<=[.!?])\s+", text)
        for sentence in sentences:
            for pat in _OVERCLAIM_PATTERNS:
                if not pat.search(sentence):
                    continue
                if _LIMITING_LANGUAGE.search(sentence):
                    continue
                err(f"{relpath}: possible quality-layer overclaim "
                    f"('{sentence.strip()}')")


# --- Check: relative links resolve ----------------------------------------

LINK_PAT = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
IMAGE_LINK_PAT = re.compile(r"\[!\[[^\]]*\]\([^)]+\)\]\(([^)]+)\)")


def check_links() -> None:
    for path in iter_text_files():
        if path.suffix.lower() != ".md":
            continue
        text = strip_code(path.read_text(encoding="utf-8"))
        targets = [m.group(1) for m in LINK_PAT.finditer(text)]
        # Also the outer target of a linked image/badge: [![alt](img)](target).
        targets += [m.group(1) for m in IMAGE_LINK_PAT.finditer(text)]
        for raw in targets:
            target = raw.strip()
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = target.split("#", 1)[0].strip()
            if not target:
                continue
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                err(f"{rel(path)}: broken relative link -> '{target}'")


# --- Check: index paths ---------------------------------------------------

SKILL_PATH_PAT = re.compile(r"skills/[A-Za-z0-9_./-]+?/SKILL\.md")


def check_index_paths(index_name: str) -> None:
    index = REPO_ROOT / index_name
    if not index.is_file():
        err(f"{index_name}: file not found")
        return
    text = index.read_text(encoding="utf-8")
    referenced = sorted(set(SKILL_PATH_PAT.findall(text)))
    if not referenced:
        warn(f"{index_name}: no skill paths found to validate")
    for skill_path in referenced:
        if not (REPO_ROOT / skill_path).is_file():
            err(f"{index_name}: references missing skill path '{skill_path}'")


# --- Check: adapters point back to canonical ------------------------------

def check_adapters() -> None:
    back_refs = {
        "adapters/codex/SKILLS_INDEX.md": "../../SKILLS_INDEX.md",
        "adapters/claude-cowork/SKILLS_INDEX.md": "../../SKILLS_INDEX.md",
        "adapters/claude-cowork/WORKFLOW_ROUTER.md": "../../WORKFLOW_ROUTER.md",
    }
    for name, expected in back_refs.items():
        path = REPO_ROOT / name
        if not path.is_file():
            err(f"{name}: adapter file not found")
            continue
        if expected not in path.read_text(encoding="utf-8"):
            err(f"{name}: should point back to the canonical root file "
                f"('{expected}')")

    agents = REPO_ROOT / "adapters" / "codex" / "AGENTS.md"
    if agents.is_file() and "/skills" not in agents.read_text(encoding="utf-8"):
        err("adapters/codex/AGENTS.md: should direct repo agents to the "
            "canonical '/skills' library")


# --- Check: plugin manifest ------------------------------------------------

def check_plugin_manifest() -> None:
    manifest = REPO_ROOT / "adapters" / "claude-code-plugin" / "plugin.json"
    if not manifest.is_file():
        err("adapters/claude-code-plugin/plugin.json: file not found")
        return
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        err(f"adapters/claude-code-plugin/plugin.json: invalid JSON ({exc})")
        return
    for field in ("name", "version", "description"):
        if not data.get(field):
            err(f"adapters/claude-code-plugin/plugin.json: missing '{field}'")


# --- Check: release version is consistent ---------------------------------

# Distribution manifests whose "version" an end user's plugin/extension
# manager reads. They must match the latest released version in CHANGELOG.md
# so a release bump can never silently drift (see the v0.2.0 drift fixed in
# PR #74). CHANGELOG.md is the single source of truth.
VERSIONED_MANIFESTS = (
    "adapters/claude-code-plugin/plugin.json",
    "gemini-extension.json",
    "site/package.json",
)


def latest_changelog_version() -> str | None:
    """Return the most recent released version in CHANGELOG.md.

    The first `## [X.Y.Z]` heading that is not `[Unreleased]` is the current
    release. Returns None if CHANGELOG.md is missing or has no released entry.
    """
    changelog = REPO_ROOT / "CHANGELOG.md"
    if not changelog.is_file():
        return None
    for match in re.finditer(
        r"^## \[(.+?)\]", changelog.read_text(encoding="utf-8"), re.MULTILINE
    ):
        tag = match.group(1)
        if tag.lower() != "unreleased":
            return tag
    return None


def check_release_version_consistency() -> None:
    release = latest_changelog_version()
    if release is None:
        err("CHANGELOG.md: no released version heading found (expected '## [X.Y.Z]')")
        return
    for name in VERSIONED_MANIFESTS:
        manifest = REPO_ROOT / name
        if not manifest.is_file():
            err(f"{name}: file not found")
            continue
        try:
            version = json.loads(manifest.read_text(encoding="utf-8")).get("version")
        except json.JSONDecodeError as exc:
            err(f"{name}: invalid JSON ({exc})")
            continue
        if version != release:
            err(
                f"{name}: version '{version}' does not match the latest "
                f"CHANGELOG.md release '{release}' — bump it or update the changelog"
            )


# --- Check: standardized skill frontmatter --------------------------------

def check_skill_frontmatter(skill_dirs: list[Path]) -> None:
    """Every canonical skill must declare valid standardized frontmatter.

    The metadata standard and its validation rules live in
    scripts/build_skill_index.py; see docs/SKILL_METADATA_STANDARD.md.
    """
    try:
        import build_skill_index as index
    except Exception as exc:  # pragma: no cover - defensive
        warn(f"could not run skill frontmatter checks (import failed: {exc})")
        return
    for skill_dir in skill_dirs:
        for msg in index.validate_skill_metadata(skill_dir):
            err(msg)


# --- Check: skill metadata index is in sync -------------------------------

def check_skill_index() -> None:
    """The generated metadata/index.json must match canonical /skills."""
    try:
        import build_skill_index as index
    except Exception as exc:  # pragma: no cover - defensive
        warn(f"could not run skill index checks (import failed: {exc})")
        return
    index_path = REPO_ROOT / "metadata" / "index.json"
    if not index_path.is_file():
        err("metadata/index.json is missing — run: "
            "python scripts/build_skill_index.py")
        return
    # Drift is only meaningful once frontmatter is valid; any frontmatter
    # errors are already reported by check_skill_frontmatter.
    if any(index.validate_skill_metadata(d)
           for d in index.canonical_skill_dirs()):
        return
    if index_path.read_text(encoding="utf-8") != index.render_index():
        err("metadata/index.json is out of date — run: "
            "python scripts/build_skill_index.py")


# --- Check: every canonical skill is catalogued ---------------------------

def check_index_coverage(skill_dirs: list[Path]) -> None:
    """Every canonical skill must appear as exactly one row in the main
    SKILLS_INDEX.md table.

    Missing entries are structural drift (the family-law cluster shipped
    without being indexed for one release because this was only a warning).
    Bullet-list mentions outside the table also satisfied a substring check
    once, hiding both Antitrust's absence from the main table and Insurance /
    Family Law duplication, so this counts table rows specifically: a row
    starts with `|` and contains the canonical path wrapped in backticks.
    """
    index = REPO_ROOT / "SKILLS_INDEX.md"
    if not index.is_file():
        return
    lines = index.read_text(encoding="utf-8").splitlines()
    table_rows = [line for line in lines if line.lstrip().startswith("|")]
    counts: dict[str, int] = {}
    for skill_dir in skill_dirs:
        skill_path = rel(skill_dir / "SKILL.md")
        token = f"`{skill_path}`"
        n = sum(1 for row in table_rows if token in row)
        counts[skill_path] = n
        if n == 0:
            err(f"{skill_path}: not listed in the SKILLS_INDEX.md main table")
        elif n > 1:
            err(f"{skill_path}: appears {n} times in the SKILLS_INDEX.md "
                f"main table (expected exactly one row)")


# --- Check: related_skills are wired in dense clusters --------------------

# Practice-area folders that hold cross-cutting infrastructure rather than
# a tightly interrelated workflow cluster — empty related_skills lists in
# these areas are not necessarily drift.
_RELATED_SKILLS_EXEMPT_AREAS = {
    "setup",
    "legal-methodology",
    "legal-ops",
    "legal-research",
}


def check_related_skills_wired(skill_dirs: list[Path]) -> None:
    """In any practice-area cluster of four or more skills, an empty
    `related_skills:` list almost certainly means the skill was added in
    isolation and never wired into its cluster. The securities-capital-markets
    cluster shipped with all twelve skills unwired for one release because
    nothing caught this, so it is an error.
    """
    by_area: dict[str, list[Path]] = {}
    for d in skill_dirs:
        parts = d.relative_to(REPO_ROOT / "skills").parts
        if len(parts) < 2:
            continue
        by_area.setdefault(parts[0], []).append(d)

    for area, skills in by_area.items():
        if area in _RELATED_SKILLS_EXEMPT_AREAS:
            continue
        if len(skills) < 4:
            continue
        for skill_dir in skills:
            fm, _ = split_frontmatter((skill_dir / "SKILL.md")
                                      .read_text(encoding="utf-8"))
            if fm is None:
                continue
            if _related_skills_is_empty(fm):
                err(f"{rel(skill_dir / 'SKILL.md')}: "
                    f"related_skills is empty, but the "
                    f"'{area}' cluster has {len(skills)} skills — wire it "
                    f"to its workflow neighbors")


def _related_skills_is_empty(fm_lines: list[str]) -> bool:
    """True if `related_skills:` is present in the frontmatter but lists
    no entries (either `[]` or a colon followed by no `- ...` items before
    the next top-level field).
    """
    lines = fm_lines
    for i, line in enumerate(lines):
        if not line.startswith("related_skills:"):
            continue
        rest = line[len("related_skills:"):].strip()
        if rest == "[]":
            return True
        if rest:
            return False
        # No inline value — look for indented list items on following lines
        # until the next top-level field (a line starting with a non-space
        # character) or end of frontmatter.
        for follow in lines[i + 1:]:
            if not follow.strip():
                continue
            if not follow.startswith(" ") and not follow.startswith("\t"):
                return True  # reached next field with no items
            if follow.lstrip().startswith("- "):
                return False  # at least one item
        return True
    return False  # field not present at all (other checks cover that)


# --- Check: README counts match the actual library ------------------------

def check_readme_counts(skill_dirs: list[Path]) -> None:
    """The README badges and the 'AgentCounsel has N skills' line drift
    from reality whenever a new practice area or skill is added without a
    README pass (the family-law cluster shipped with the README still
    saying 153 skills / 19 practice areas). Catch that here.
    """
    readme = REPO_ROOT / "README.md"
    if not readme.is_file():
        return
    text = readme.read_text(encoding="utf-8")

    skill_count = len(skill_dirs)
    area_count = len({
        d.relative_to(REPO_ROOT / "skills").parts[0] for d in skill_dirs
    })

    badge_skills = re.search(r"shields\.io/badge/skills-(\d+)", text)
    if badge_skills and int(badge_skills.group(1)) != skill_count:
        err(f"README.md: skills badge says "
            f"{badge_skills.group(1)} but library has {skill_count}")

    badge_areas = re.search(
        r"shields\.io/badge/practice%20areas-(\d+)", text)
    if badge_areas:
        # README counts the supporting cross-cutting groups as separate from
        # practice areas, so the badge is the practice-area count minus the
        # four cross-cutting buckets (setup, legal-methodology, legal-ops,
        # legal-research is its own practice area in the README).
        cross_cutting = {"setup", "legal-methodology", "legal-ops"}
        readme_areas = area_count - sum(
            1 for c in cross_cutting
            if (REPO_ROOT / "skills" / c).is_dir())
        if int(badge_areas.group(1)) != readme_areas:
            err(f"README.md: practice-areas badge says "
                f"{badge_areas.group(1)} but library has {readme_areas} "
                f"(of {area_count} total skill folders, "
                f"{len(cross_cutting)} are cross-cutting groups)")

    has_line = re.search(
        r"AgentCounsel has \*\*(\d+) skills\*\*", text)
    if has_line and int(has_line.group(1)) != skill_count:
        err(f"README.md: 'AgentCounsel has N skills' says "
            f"{has_line.group(1)} but library has {skill_count}")

    # The README's cross-cutting bullet block names per-group counts:
    #   "- **Setup** (5 skills) — ..."
    # These drift silently from disk whenever a new skill is added to one of
    # the cross-cutting groups (Setup gained 14 cold-start interviews but the
    # bullet kept reading "5 skills"). Map each bullet name to its skills/
    # folder and verify.
    group_dirs = {
        "Setup": "setup",
        "Legal Methodology": "legal-methodology",
        "Legal Operations": "legal-ops",
    }
    bullet_pat = re.compile(
        r"\*\*(Setup|Legal Methodology|Legal Operations)\*\*\s*"
        r"\((\d+)\s+skills?\)")
    for match in bullet_pat.finditer(text):
        group, claimed = match.group(1), int(match.group(2))
        folder = REPO_ROOT / "skills" / group_dirs[group]
        if not folder.is_dir():
            continue
        actual = sum(
            1 for p in folder.iterdir()
            if p.is_dir() and p.name not in NON_SKILL_DIRS)
        if claimed != actual:
            err(f"README.md: '{group}' bullet says {claimed} skills "
                f"but skills/{group_dirs[group]}/ has {actual}")


# --- Check: plugin bundle is present and in sync --------------------------

def check_plugin_bundle() -> None:
    """Detect Claude Code plugin bundle drift against canonical /skills."""
    try:
        import sync_plugin_skills as sync
    except Exception as exc:  # pragma: no cover - defensive
        warn(f"could not run plugin bundle checks (import failed: {exc})")
        return

    expected = list(sync.CURATED_BUNDLE) + list(sync.MAINTAINED_SKILLS)

    for name in expected:
        skill_md = sync.PLUGIN_ROOT / name / "SKILL.md"
        if not skill_md.is_file():
            err(f"plugin bundle: expected skill '{name}' is missing "
                f"({rel(skill_md)})")

    if sync.PLUGIN_ROOT.is_dir():
        for sub in sorted(p for p in sync.PLUGIN_ROOT.iterdir() if p.is_dir()):
            if sub.name not in expected:
                warn(f"plugin bundle: unexpected skill folder '{sub.name}' "
                     f"(not in the curated bundle or the maintained set)")

    for name in sync.CURATED_BUNDLE:
        canonical_dir, _, actions = sync.plan_skill(name)
        if canonical_dir is None:
            err(f"plugin bundle: no canonical source found for curated "
                f"skill '{name}' under skills/")
            continue
        drift = [(status, relpath) for status, relpath in actions
                 if status != "unchanged"]
        if drift:
            detail = ", ".join(f"{relpath} ({status})"
                               for status, relpath in drift)
            err(f"plugin bundle: '{name}' is out of sync with canonical "
                f"skills/ [{detail}] — run: python scripts/sync_plugin_skills.py")


# --- Check: source and citation discipline --------------------------------

_CITATION_REF = "source-and-citation-discipline"
_CITATION_LANGUAGE = re.compile(r"\b(do not|never|don't)\s+invent\b", re.I)
_CITATION_TOPIC = re.compile(
    r"authorit|citation|statute|case law|\bcases\b|regulation|quotation",
    re.I)


def check_citation_discipline(skill_dirs: list[Path]) -> None:
    """Every canonical skill must reference the source/citation discipline
    core rule, or carry equivalent discipline language of its own."""
    for skill_dir in skill_dirs:
        md = skill_dir / "SKILL.md"
        if not md.is_file():
            continue
        text = md.read_text(encoding="utf-8")
        if _CITATION_REF in text:
            continue
        if _CITATION_LANGUAGE.search(text) and _CITATION_TOPIC.search(text):
            continue
        err(f"{rel(md)}: missing source/citation discipline — reference "
            f"core/source-and-citation-discipline.md, or include explicit "
            f"language against inventing legal authority or citations")


# --- Check: practice-profile references in skills are consistent ----------

PROFILE_REF_RE = re.compile(r"practice-profiles/([a-z0-9-]+)\.md")
PRACTICE_AREA_RE = re.compile(r"^practice_area:\s*([a-z0-9-]+)\s*$", re.M)


def check_profile_references_consistent(skill_dirs: list[Path]) -> None:
    """Every reference to practice-profiles/<area>.md in a non-setup skill
    must use the slug that matches the skill's own practice_area frontmatter
    value. Catches a contracts skill accidentally pointing at
    practice-profiles/employment.md, etc.

    File existence is NOT checked — silent-if-absent is the design, and a
    skill may reference a profile that has not yet been authored."""
    for skill_dir in skill_dirs:
        rel_dir = rel(skill_dir)
        if rel_dir.startswith("skills/setup/"):
            continue
        md = skill_dir / "SKILL.md"
        if not md.is_file():
            continue
        text = md.read_text(encoding="utf-8")
        m = PRACTICE_AREA_RE.search(text)
        if not m:
            continue
        skill_area = m.group(1).strip()
        for ref in PROFILE_REF_RE.findall(text):
            if ref != skill_area:
                err(
                    f"{rel(md)}: references practice-profiles/{ref}.md but "
                    f"the skill's practice_area is '{skill_area}'"
                )


# --- Check: normalized metadata and router --------------------------------

def check_normalized_metadata() -> None:
    """Validate derived metadata fields and the generated router artifact."""
    try:
        import build_skill_index as index
    except Exception as exc:  # pragma: no cover - defensive
        warn(f"could not run normalized metadata checks (import failed: {exc})")
        return

    router_path = REPO_ROOT / "metadata" / "router.json"
    if not router_path.is_file():
        err("metadata/router.json is missing — run: "
            "python scripts/build_skill_index.py")
    elif router_path.read_text(encoding="utf-8") != index.render_router():
        err("metadata/router.json is out of date — run: "
            "python scripts/build_skill_index.py")

    for msg in index.validate_normalized_index():
        err(f"normalized metadata: {msg}")


# --- Check: platform pack registry ----------------------------------------

def check_pack_registry() -> None:
    """metadata/packs.json must match the platform pack generator and
    reference only existing source files."""
    try:
        import build_platform_packs as packs
    except Exception as exc:  # pragma: no cover - defensive
        warn(f"could not run pack registry checks (import failed: {exc})")
        return

    path = REPO_ROOT / "metadata" / "packs.json"
    if not path.is_file():
        err("metadata/packs.json is missing — run: "
            "python scripts/build_platform_packs.py")
        return
    areas = packs.load_areas()
    if path.read_text(encoding="utf-8") != packs.render_pack_registry(areas):
        err("metadata/packs.json is out of date — run: "
            "python scripts/build_platform_packs.py")
    for msg in packs.validate_pack_registry(packs.build_pack_registry(areas)):
        err(f"pack registry: {msg}")


# --- Check: matter workspace template, playbooks, review panels ------------

# Canonical multi-file matter workspace template contents.
WORKSPACE_TEMPLATE_FILES = [
    "matter_profile.md", "facts.md", "open_questions.md", "source_log.md",
    "citation_map.md", "unsupported_claims.md", "assumptions.md", "tasks.md",
    "skills_used.md", "attorney_review.md", "matter_status.md",
    "documents/README.md", "outputs/README.md", "quality_checks/README.md",
]

# Required H2 sections for every playbook, in order.
PLAYBOOK_SECTIONS = [
    "## When to Use", "## Required Inputs", "## Default Client-Position Questions",
    "## Risk Tolerance Settings", "## Required Source Materials",
    "## Recommended Primary Skills", "## Required Quality Checks",
    "## Attorney Escalation Triggers", "## Expected Outputs",
    "## Source and Citation Expectations", "## Common Failure Modes",
    "## Final Attorney-Review Gate",
]

# Required H2 sections for every review panel, in order.
PANEL_SECTIONS = [
    "## When to Use", "## Inputs", "## Review Passes", "## Sequence",
    "## Required Quality Checks", "## Attorney Escalation Triggers",
    "## Expected Outputs", "## Safety and Supervision Model",
    "## Common Failure Modes", "## Final Attorney-Review Gate",
]

# Quality-layer source classification labels the tracking templates must carry.
CLASSIFICATION_LABELS = [
    "source-supported", "source-mentioned but insufficient", "unsupported",
    "contradicted by source", "legal authority required",
    "attorney judgment required", "user-provided authority",
    "model-suggested authority requiring verification",
    "unsupported or unverifiable authority",
]


# Matter packs count on disk when this check was added — a floor, not an
# exact match. See check_matter_packs().
MATTER_PACKS_MIN_COUNT = 9

# Bold-labeled concepts present in every current matter pack file, tolerant of
# the colon/period punctuation variance across files. See check_matter_packs().
MATTER_PACK_REQUIRED_LABELS = [
    ("When to use", re.compile(r"\*\*When to use[:.]\*\*")),
    ("Required starting materials",
     re.compile(r"\*\*Required starting materials[:.]\*\*")),
    ("Recommended skill sequence",
     re.compile(r"\*\*Recommended skill sequence[:.]\*\*")),
    ("Expected outputs", re.compile(r"\*\*Expected outputs[:.]\*\*")),
    ("Do-not-use boundaries",
     re.compile(r"\*\*Do-not-use boundaries[:.]\*\*|\*\*Do not use when[:.]\*\*")),
]

# The numbered H2 headings documented as the connector contract in
# connectors/README.md. See check_connectors().
CONNECTOR_REQUIRED_HEADINGS = [
    ("1. Source", re.compile(r"^## 1\.\s+Source\s*$", re.M)),
    ("2. In scope", re.compile(r"^## 2\.\s+In scope\b", re.M)),
    ("3. Out of scope", re.compile(r"^## 3\.\s+Out of scope\b", re.M)),
    ("4. Surface", re.compile(r"^## 4\.\s+Surface\b", re.M)),
    ("5. Calling pattern from a skill",
     re.compile(r"^## 5\.\s+Calling pattern from a skill\s*$", re.M)),
    ("6. Fallback behavior", re.compile(r"^## 6\.\s+Fallback behavior\s*$", re.M)),
    ("7. Limits and known failure modes",
     re.compile(r"^## 7\.\s+Limits and known failure modes\s*$", re.M)),
]


def _h2_sections(text: str) -> list[str]:
    return [ln.strip() for ln in text.splitlines() if ln.startswith("## ")]


def _check_required_sections(path: Path, required: list[str], label: str) -> None:
    text = path.read_text(encoding="utf-8")
    present = _h2_sections(text)
    for section in required:
        if section not in present:
            err(f"{rel(path)}: {label} missing required section '{section}'")
    # Order check: the required sections must appear in the given order.
    indexed = [present.index(s) for s in required if s in present]
    if indexed != sorted(indexed):
        err(f"{rel(path)}: {label} sections are out of order")


def check_matter_workspace_template() -> None:
    """The canonical multi-file matter workspace template must be complete and
    its source/citation tracking templates must carry the quality-layer
    classification vocabulary."""
    base = REPO_ROOT / "matter-workspaces" / "_template"
    if not base.is_dir():
        err("matter-workspaces/_template/ is missing (canonical workspace template)")
        return
    for name in WORKSPACE_TEMPLATE_FILES:
        if not (base / name).is_file():
            err(f"matter-workspaces/_template/{name}: workspace template file missing")
    # Source/citation tracking templates must match the quality-layer labels.
    for name in ("source_log.md", "citation_map.md", "unsupported_claims.md",
                 "assumptions.md"):
        path = base / name
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if name in ("source_log.md", "citation_map.md"):
            # These carry the full classification vocabulary.
            for lbl in CLASSIFICATION_LABELS:
                if lbl not in text:
                    err(f"matter-workspaces/_template/{name}: missing "
                        f"quality-layer classification label '{lbl}'")
        else:
            # unsupported_claims / assumptions carry the relevant subset; require
            # at least three recognized labels so they stay aligned with the layer.
            found = sum(1 for lbl in CLASSIFICATION_LABELS if lbl in text)
            if found < 3:
                err(f"matter-workspaces/_template/{name}: too few quality-layer "
                    f"classification labels ({found}); expected at least 3")
        # Every tracking template must reference the classification idea.
        if "classification" not in text.lower():
            err(f"matter-workspaces/_template/{name}: no classification vocabulary")


def check_playbooks() -> None:
    """Every playbook (excluding the README) must carry the required sections."""
    base = REPO_ROOT / "playbooks"
    if not base.is_dir():
        err("playbooks/ directory is missing")
        return
    files = [p for p in sorted(base.glob("*.md")) if p.name != "README.md"]
    if len(files) < 8:
        err(f"playbooks/: expected at least 8 playbooks, found {len(files)}")
    for path in files:
        _check_required_sections(path, PLAYBOOK_SECTIONS, "playbook")


def check_review_panels() -> None:
    """Every review panel (excluding the README) must carry the required
    sections and state that passes are not autonomous agents or lawyers."""
    base = REPO_ROOT / "review-panels"
    if not base.is_dir():
        err("review-panels/ directory is missing")
        return
    files = [p for p in sorted(base.glob("*.md")) if p.name != "README.md"]
    if len(files) < 6:
        err(f"review-panels/: expected at least 6 panels, found {len(files)}")
    for path in files:
        _check_required_sections(path, PANEL_SECTIONS, "review panel")
        text = path.read_text(encoding="utf-8").lower()
        if "not" not in text or ("autonomous" not in text and "lawyer" not in text):
            err(f"{rel(path)}: review panel must state passes are not "
                "autonomous agents or lawyers")


def check_matter_packs() -> None:
    """Every matter pack (excluding the README) must carry the bold-labeled
    sections common to every matter pack.

    Matter packs don't share literal H2 titles the way playbooks and review
    panels do — each H2 is the pack's own name (e.g. '## 3. M&A Antitrust
    Matter Pack'). What every pack actually shares is a set of bold-labeled
    bullets inside each entry. Label punctuation varies file to file ('When
    to use:' vs 'When to use.', 'Do-not-use boundaries:' vs 'Do not use
    when.'), so this matches the concept, not one exact string. Only the five
    labels present in every current pack file are required; 'Handoff notes'
    (absent from real-estate.md) and 'Attorney verification checkpoints'
    (renamed 'Qualified tax professional checkpoints' in tax.md) are not
    universal and are intentionally not enforced here.

    The minimum file count is the count on disk as of this check's addition
    (9); it is a floor, not an exact match, so a pack legitimately being added
    concurrently does not trip this check.
    """
    base = REPO_ROOT / "matter-packs"
    if not base.is_dir():
        err("matter-packs/ directory is missing")
        return
    files = [p for p in sorted(base.glob("*.md")) if p.name != "README.md"]
    if len(files) < MATTER_PACKS_MIN_COUNT:
        err(f"matter-packs/: expected at least {MATTER_PACKS_MIN_COUNT} "
            f"packs, found {len(files)}")
    for path in files:
        text = path.read_text(encoding="utf-8")
        for label, pattern in MATTER_PACK_REQUIRED_LABELS:
            if not pattern.search(text):
                err(f"{rel(path)}: matter pack missing required "
                    f"'{label}' label")


def check_connectors() -> None:
    """Every connector doc (excluding the README) must carry the numbered
    headings documented as the connector contract in connectors/README.md:
    Source, In scope, Out of scope, Surface, Calling pattern from a skill,
    Fallback behavior, and Limits and known failure modes."""
    base = REPO_ROOT / "connectors"
    if not base.is_dir():
        err("connectors/ directory is missing")
        return
    files = [p for p in sorted(base.glob("*.md")) if p.name != "README.md"]
    for path in files:
        text = path.read_text(encoding="utf-8")
        for label, pattern in CONNECTOR_REQUIRED_HEADINGS:
            if not pattern.search(text):
                err(f"{rel(path)}: connector doc missing required "
                    f"'## {label}' heading")


def check_practice_area_doc_sync() -> None:
    """docs/SKILL_METADATA_STANDARD.md documents the closed set of valid
    practice_area values as 'Current values: `a`, `b`, ...'. That enumeration
    must equal the set of directory names under skills/ in both directions —
    a new skills/<area>/ added without updating the doc, or a stale value
    left in the doc after an area is removed/renamed, are both drift."""
    doc = REPO_ROOT / "docs" / "SKILL_METADATA_STANDARD.md"
    if not doc.is_file():
        err("docs/SKILL_METADATA_STANDARD.md: file not found")
        return
    text = doc.read_text(encoding="utf-8")
    match = re.search(r"Current\s+values:\s*(.+?)\.", text, re.S)
    if not match:
        err("docs/SKILL_METADATA_STANDARD.md: could not find the "
            "practice_area 'Current values:' enumeration")
        return
    documented = set(re.findall(r"`([a-z0-9-]+)`", match.group(1)))
    skills_dir = REPO_ROOT / "skills"
    if not skills_dir.is_dir():
        return
    actual = {p.name for p in skills_dir.iterdir() if p.is_dir()}
    for area in sorted(actual - documented):
        err(f"docs/SKILL_METADATA_STANDARD.md: skills/{area}/ exists but is "
            f"not listed in the practice_area 'Current values:' enumeration")
    for area in sorted(documented - actual):
        err(f"docs/SKILL_METADATA_STANDARD.md: practice_area 'Current "
            f"values:' lists '{area}' but skills/{area}/ does not exist")


def check_router_workspace_references() -> None:
    """Router examples that point at a workspace, playbook, or review panel must
    reference files/dirs that exist."""
    router_path = REPO_ROOT / "metadata" / "router.json"
    if not router_path.is_file():
        return
    try:
        data = json.loads(router_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        err(f"metadata/router.json: invalid JSON ({exc})")
        return
    for example in data.get("examples", []):
        target = example.get("route_to", "")
        if not target:
            continue
        if target.startswith(("matter-workspaces/", "playbooks/",
                              "review-panels/", "practice-profiles/")):
            if not (REPO_ROOT / target).exists():
                err(f"metadata/router.json: example route_to does not exist: {target}")


# --- Check: required docs and doc/script references ------------------------

# Top-level docs a new user / contributor relies on. Missing one is an error.
REQUIRED_DOCS = [
    "README.md",
    "QUICKSTART.md",
    "CONTRIBUTING.md",
    "WORKFLOW_ROUTER.md",
    "docs/CHOOSE_YOUR_WORKFLOW.md",
    "docs/CLI.md",
    "docs/AGENT_COMMANDS.md",
    "docs/WORKFLOW_MAP.md",
    "docs/PROJECT_STATUS.md",
    "docs/MATTER_WORKSPACES.md",
    "docs/PLAYBOOKS.md",
    "docs/REVIEW_PANELS.md",
    "docs/QUALITY_LAYER.md",
    "docs/SAFETY_MODEL.md",
]

# Docs that document how to run the tooling. Every scripts/<name>.py they name
# must exist, so command guidance never points at a missing script.
DOC_COMMAND_FILES = [
    "README.md", "QUICKSTART.md", "CONTRIBUTING.md",
    "docs/CLI.md", "docs/AGENT_COMMANDS.md",
]
_SCRIPT_REF_PAT = re.compile(r"scripts/([A-Za-z0-9_]+\.py)")


def check_required_docs() -> None:
    """Required top-level and docs/ files must exist."""
    for rel_path in REQUIRED_DOCS:
        if not (REPO_ROOT / rel_path).is_file():
            err(f"required doc missing: {rel_path}")


def check_doc_script_references() -> None:
    """Every scripts/<name>.py referenced in command docs must exist, and a
    referenced 'node site/generate.mjs' must point at a real file."""
    for rel_path in DOC_COMMAND_FILES:
        path = REPO_ROOT / rel_path
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for script in sorted(set(_SCRIPT_REF_PAT.findall(text))):
            if not (REPO_ROOT / "scripts" / script).is_file():
                err(f"{rel_path}: references missing script 'scripts/{script}'")
        if "site/generate.mjs" in text and not (REPO_ROOT / "site" / "generate.mjs").is_file():
            err(f"{rel_path}: references missing 'site/generate.mjs'")


# --- Main ------------------------------------------------------------------

def main() -> int:
    argparse.ArgumentParser(
        description="Validate AgentCounsel repository structure, safety framing, "
                    "and link integrity (stdlib-only). Exit 0 if all checks pass. "
                    "See VALIDATION.md.",
    ).parse_args()
    canonical = canonical_skill_dirs()
    plugin = plugin_skill_dirs()

    print(f"AgentCounsel repository validation — {rel(REPO_ROOT) or '.'}")
    print(f"  canonical skills: {len(canonical)}")
    print(f"  plugin skills:    {len(plugin)}")
    print()

    for skill_dir in canonical:
        check_skill(skill_dir, require_sections=True)
    for skill_dir in plugin:
        check_skill(skill_dir, require_sections=False)

    check_repo_layout()
    check_overlays()
    check_citation_discipline(canonical)
    check_content_scans()
    check_whitespace()
    check_quality_layer_overclaims()
    check_links()
    check_index_paths("SKILLS_INDEX.md")
    check_index_paths("WORKFLOW_ROUTER.md")
    check_index_paths("COMMANDS.md")
    check_adapters()
    check_plugin_manifest()
    check_release_version_consistency()
    check_plugin_bundle()
    check_skill_frontmatter(canonical)
    check_skill_index()
    check_normalized_metadata()
    check_pack_registry()
    check_index_coverage(canonical)
    check_related_skills_wired(canonical)
    check_readme_counts(canonical)
    check_profile_references_consistent(canonical)
    check_matter_workspace_template()
    check_playbooks()
    check_review_panels()
    check_matter_packs()
    check_connectors()
    check_practice_area_doc_sync()
    check_router_workspace_references()
    check_required_docs()
    check_doc_script_references()

    if warnings:
        print(f"Warnings ({len(warnings)}):")
        for msg in warnings:
            print(f"  ! {msg}")
        print()

    if errors:
        print(f"Errors ({len(errors)}):")
        for msg in errors:
            print(f"  x {msg}")
        print()
        print("VALIDATION FAILED")
        return 1

    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
