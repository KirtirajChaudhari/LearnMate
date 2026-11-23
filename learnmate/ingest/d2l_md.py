"""Parser for the Dive into Deep Learning (d2l-en) Markdown dialect (spec C1).

d2l specifics handled here:
* multi-framework code cells  ```{.python .input}\n%%tab pytorch ...```  -> keep only the configured framework
  (and framework-agnostic cells), drop notebook setup cells (``%load_ext d2lbook.tab``);
* directives ``:label:`x` ``, ``:eqlabel:`x` ``, ``:numref:`x` ``, ``:eqref:`x` ``, ``:cite:`x` ``;
* figures ``![caption](path)`` -> "Figure: caption";
* ```toc``` blocks (chapter tables of contents) and ```eval_rst``` / bibtex blocks are dropped;
* LaTeX math (``$..$``, ``$$..$$``) is kept verbatim.

Output: a list of ``Section`` objects, one per heading-delimited (sub)section, in reading order.
No network access happens here: the repo must already be cloned at the pinned commit.
"""
from __future__ import annotations

import re
from pathlib import Path

from ..io_utils import stable_id
from ..provenance import Section

FENCE_RE = re.compile(r"^```(.*)$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
LABEL_LINE_RE = re.compile(r"^\s*:(label|eqlabel):`([^`]*)`\s*$")
NUMREF_RE = re.compile(r":numref:`([^`]*)`")
EQREF_RE = re.compile(r":eqref:`([^`]*)`")
CITE_RE = re.compile(r":cite[pt]?:`([^`]*)`")
FIG_RE = re.compile(r"!\[([^\]]*)\]\([^)]*\)")
OTHER_ROLE_RE = re.compile(r":(width|height|begin_tab|end_tab)[^\n]*")
BEGIN_TAB_RE = re.compile(r"^\s*:begin_tab:`([^`]*)`\s*$")
END_TAB_RE = re.compile(r"^\s*:end_tab:\s*$")
HILITE_RE = re.compile(r"\[\*\*(.*?)\*\*\]", re.S)
MATH_RE = re.compile(r"\$[^$]+\$")

FRAMEWORKS = ("mxnet", "pytorch", "tensorflow", "jax")


def read_toc(index_md: Path) -> list[str]:
    """Return the ordered list of file stems from a chapter's ```toc``` block."""
    text = index_md.read_text(encoding="utf-8")
    m = re.search(r"```toc\n(.*?)```", text, re.S)
    if not m:
        return []
    stems = []
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith(":"):
            continue
        stems.append(line)
    return stems


def chapter_title(index_md: Path) -> str:
    for line in index_md.read_text(encoding="utf-8").splitlines():
        hm = HEADING_RE.match(line)
        if hm and len(hm.group(1)) == 1:
            return clean_inline(hm.group(2))
    return index_md.parent.name


def clean_inline(text: str, label_titles: dict[str, str] | None = None) -> str:
    label_titles = label_titles or {}

    def numref(m: re.Match) -> str:
        key = m.group(1)
        return f"[{label_titles[key]}]" if key in label_titles else f"[{key}]"

    text = NUMREF_RE.sub(numref, text)
    text = EQREF_RE.sub(lambda m: f"({m.group(1)})", text)
    text = CITE_RE.sub("", text)
    text = text.replace("[**", "").replace("**]", "")
    text = FIG_RE.sub(lambda m: f"Figure: {m.group(1)}", text)
    return text


def _keep_code_cell(lines: list[str], framework: str) -> tuple[bool, list[str], str | None]:
    """Decide whether a ```{.python .input} cell is kept. Returns (keep, body_lines, dropped_framework)."""
    body = list(lines)
    if any("%load_ext d2lbook" in l or "tab.interact_select" in l for l in body):
        return False, [], "setup"
    first = body[0].strip() if body else ""
    if first.startswith("%%tab"):
        tabs = first[len("%%tab"):].replace(",", " ").split()
        body = body[1:]
        if "all" in tabs or framework in tabs:
            return True, body, None
        return False, [], ",".join(tabs)
    if first.startswith("#@tab"):
        tabs = first[len("#@tab"):].replace(",", " ").split()
        body = body[1:]
        if "all" in tabs or framework in tabs:
            return True, body, None
        return False, [], ",".join(tabs)
    # framework-agnostic cell
    body = [l for l in body if not l.strip().startswith(("%matplotlib", "%%"))]
    return True, body, None


def parse_markdown_file(
    path: Path,
    chapter: str,
    chapter_title_text: str,
    framework: str = "pytorch",
    web_base: str = "https://d2l.ai",
    label_titles: dict[str, str] | None = None,
) -> list[Section]:
    """Split one d2l markdown file into heading-delimited sections with normalized text."""
    raw_lines = path.read_text(encoding="utf-8").splitlines()
    doc_id = f"{chapter}/{path.stem}"
    source_url = f"{web_base}/{chapter}/{path.stem}.html"

    # Pass 1: resolve fenced blocks into normalized text lines (keep headings separate).
    out: list[tuple[str, str]] = []  # (kind, text) kind in {"heading:<level>", "line"}
    flags_per_line: list[set[str]] = []
    i = 0
    while i < len(raw_lines):
        line = raw_lines[i]
        fm = FENCE_RE.match(line)
        if fm:
            info = fm.group(1).strip()
            j = i + 1
            block: list[str] = []
            while j < len(raw_lines) and not raw_lines[j].startswith("```"):
                block.append(raw_lines[j])
                j += 1
            i = j + 1  # skip closing fence
            if info.startswith("{.python .input}") or info.startswith("{.python .input "):
                keep, body, dropped = _keep_code_cell(block, framework)
                if keep and any(b.strip() for b in body):
                    out.append(("line", "```python"))
                    for b in body:
                        out.append(("line", b))
                    out.append(("line", "```"))
                    flags_per_line.extend([{"code"}] * (len(body) + 2))
                elif dropped:
                    out.append(("flag", f"code_dropped:{dropped}"))
                    flags_per_line.append(set())
            elif info.startswith("toc") or info.startswith("eval_rst") or info.startswith("bibtex") \
                    or info.startswith("{.python .output}") or info.startswith("{.input"):
                pass  # navigation / output / rst blocks: drop
            else:
                out.append(("line", "```" + info))
                for b in block:
                    out.append(("line", b))
                out.append(("line", "```"))
                flags_per_line.extend([{"code"}] * (len(block) + 2))
            continue
        hm = HEADING_RE.match(line)
        if hm:
            out.append((f"heading:{len(hm.group(1))}", clean_inline(hm.group(2), label_titles)))
            flags_per_line.append(set())
            i += 1
            continue
        lm = LABEL_LINE_RE.match(line)
        if lm:
            if lm.group(1) == "label":
                out.append(("label", lm.group(2)))
                flags_per_line.append(set())
            i += 1
            continue
        bt = BEGIN_TAB_RE.match(line)
        if bt:
            tabs = bt.group(1).replace(",", " ").split()
            if not ("all" in tabs or framework in tabs):
                # skip framework-specific prose for other frameworks
                j = i + 1
                while j < len(raw_lines) and not END_TAB_RE.match(raw_lines[j]):
                    j += 1
                out.append(("flag", f"prose_dropped:{','.join(tabs)}"))
                flags_per_line.append(set())
                i = j + 1
            else:
                i += 1
            continue
        if END_TAB_RE.match(line):
            i += 1
            continue
        out.append(("line", clean_inline(line, label_titles)))
        flags_per_line.append(set())
        i += 1

    # Pass 2: group into sections by headings.
    sections: list[Section] = []
    path_stack: list[tuple[int, str]] = []
    cur_lines: list[str] = []
    cur_flags: set[str] = set()
    cur_label: str | None = None

    def flush() -> None:
        nonlocal cur_lines, cur_flags, cur_label
        text = "\n".join(cur_lines).strip()
        text = re.sub(r"\n{3,}", "\n\n", text)
        if text and path_stack:
            sp = [chapter_title_text] + [t for _, t in path_stack]
            if MATH_RE.search(text) or "$$" in text:
                cur_flags.add("math")
            sections.append(Section(
                doc_id=doc_id,
                section_id=stable_id(doc_id, *sp),
                section_path=sp,
                chapter=chapter,
                text=text,
                source_url=source_url,
                label=cur_label,
                flags=sorted(cur_flags),
            ))
        cur_lines, cur_flags, cur_label = [], set(), None

    for kind, text in out:
        if kind.startswith("heading:"):
            flush()
            level = int(kind.split(":")[1])
            while path_stack and path_stack[-1][0] >= level:
                path_stack.pop()
            path_stack.append((level, text))
        elif kind == "label":
            cur_label = cur_label or text
        elif kind == "flag":
            cur_flags.add(text)
        else:
            cur_lines.append(text)
    flush()
    return sections


def collect_label_titles(repo: Path, chapters: list[str]) -> dict[str, str]:
    """Map d2l :label: keys to heading titles (for readable :numref: substitution)."""
    titles: dict[str, str] = {}
    for ch in chapters:
        for md in sorted((repo / ch).glob("*.md")):
            last_heading = None
            for line in md.read_text(encoding="utf-8").splitlines():
                hm = HEADING_RE.match(line)
                if hm:
                    last_heading = clean_inline(hm.group(2))
                    continue
                lm = LABEL_LINE_RE.match(line)
                if lm and lm.group(1) == "label" and last_heading:
                    titles[lm.group(2)] = last_heading
    return titles


def parse_d2l(repo: str | Path, chapters: list[str], framework: str = "pytorch",
              web_base: str = "https://d2l.ai") -> list[Section]:
    """Parse the given chapters (in toc order) of a local d2l-en checkout."""
    repo = Path(repo)
    label_titles = collect_label_titles(repo, chapters)
    sections: list[Section] = []
    for ch in chapters:
        index_md = repo / ch / "index.md"
        if not index_md.exists():
            raise FileNotFoundError(index_md)
        ctitle = chapter_title(index_md)
        # chapter intro text (index.md minus toc) is a section too
        sections.extend(parse_markdown_file(index_md, ch, ctitle, framework, web_base, label_titles))
        for stem in read_toc(index_md):
            md = repo / ch / f"{stem}.md"
            if not md.exists():
                continue
            sections.extend(parse_markdown_file(md, ch, ctitle, framework, web_base, label_titles))
    # de-duplicate the chapter-title level that index.md repeats as its own H1
    for s in sections:
        if len(s.section_path) >= 2 and s.section_path[0] == s.section_path[1]:
            s.section_path = s.section_path[1:]
    return sections
