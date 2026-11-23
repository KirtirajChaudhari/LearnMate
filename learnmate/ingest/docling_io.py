"""Optional Docling ingestion for faculty-supplied PDF/DOCX/PPTX files (spec C1, 'Should').

Produces the same ``Section`` objects as the d2l parser so chunking/indexing are unchanged.
Allow-listed extensions only; files are converted locally (no network fetches of remote URLs).
"""
from __future__ import annotations

from pathlib import Path

from ..io_utils import stable_id
from ..provenance import Section

ALLOWED = {".pdf", ".docx", ".pptx", ".md", ".html"}


def parse_with_docling(files: list[str | Path], course_title: str = "Course materials") -> tuple[list[Section], list[dict]]:
    try:
        from docling.document_converter import DocumentConverter  # type: ignore
    except ImportError as e:  # pragma: no cover
        raise ImportError("Install the optional extra: pip install 'learnmate[pdf]'") from e
    conv = DocumentConverter()
    sections: list[Section] = []
    failures: list[dict] = []
    for f in map(Path, files):
        if f.suffix.lower() not in ALLOWED:
            failures.append({"file": str(f), "reason": "extension not allow-listed"})
            continue
        try:
            doc = conv.convert(str(f)).document
            md = doc.export_to_markdown()
        except Exception as e:  # fail-closed: skip and log, never partial
            failures.append({"file": str(f), "reason": f"parse error: {e!r}"})
            continue
        doc_id = f"faculty/{f.stem}"
        cur_path: list[str] = [course_title, f.stem]
        buf: list[str] = []

        def flush():
            text = "\n".join(buf).strip()
            if text:
                sections.append(Section(doc_id=doc_id, section_id=stable_id(doc_id, *cur_path),
                                        section_path=list(cur_path), chapter=doc_id, text=text,
                                        source_url=f"file://{f.name}", flags=["docling"]))
        for line in md.splitlines():
            if line.startswith("#"):
                flush()
                buf = []
                level = len(line) - len(line.lstrip("#"))
                cur_path = cur_path[: 1 + min(level, len(cur_path) - 1)] + [line.lstrip("#").strip()]
            else:
                buf.append(line)
        flush()
    return sections, failures
