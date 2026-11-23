from pathlib import Path

from learnmate.chunking import build_chunks, chunk_section
from learnmate.ingest.d2l_md import parse_markdown_file
from learnmate.provenance import ChunkStore, Section

D2L_SAMPLE = """```{.python .input}
%load_ext d2lbook.tab
tab.interact_select(['mxnet', 'pytorch', 'tensorflow', 'jax'])
```

# Linear Regression
:label:`sec_linreg`

*Regression* problems predict a numerical value, see :numref:`sec_other` and :eqref:`eq_mse` :cite:`Foo.2020`.

## Basics

The loss is $\\ell = \\frac{1}{2}(y-\\hat y)^2$.

$$L(\\mathbf{w}) = \\frac{1}{n}\\sum_i \\ell_i.$$
:eqlabel:`eq_mse`

```{.python .input}
%%tab mxnet
from mxnet import np
```

```{.python .input}
%%tab pytorch
import torch
```

:begin_tab:`tensorflow`
TensorFlow specific prose.
:end_tab:

:begin_tab:`pytorch`
PyTorch specific prose.
:end_tab:

![A figure caption.](../img/x.svg)

```toc
:maxdepth: 2
a
```
"""


def _parse(tmp_path):
    f = tmp_path / "linreg.md"
    f.write_text(D2L_SAMPLE)
    return parse_markdown_file(f, "chapter_x", "Chapter X", "pytorch", label_titles={"sec_other": "Other Section"})


def test_d2l_parser_framework_and_directives(tmp_path):
    secs = _parse(tmp_path)
    paths = [s.section_path for s in secs]
    assert ["Chapter X", "Linear Regression"] in paths
    assert ["Chapter X", "Linear Regression", "Basics"] in paths
    text = "\n".join(s.text for s in secs)
    assert "import torch" in text and "mxnet" not in text
    assert "PyTorch specific prose" in text and "TensorFlow specific" not in text
    assert ":label:" not in text and ":cite:" not in text and ":eqlabel:" not in text and "d2lbook" not in text
    assert "[Other Section]" in text and "(eq_mse)" in text
    assert "Figure: A figure caption." in text
    assert "$$L(\\mathbf{w})" in text  # math preserved verbatim
    assert "maxdepth" not in text      # toc dropped


def _count(t):
    return len(t.split())


def test_chunks_never_cross_sections_and_reproduce_spans(tmp_path):
    secs = _parse(tmp_path)
    long = Section("d", "sid", ["C", "S"], "chapter_x", " ".join(f"Sentence number {i} is here." for i in range(300)), "u")
    secs.append(long)
    chunks = build_chunks(secs, _count, {"commit": "abc", "license": "L", "attribution": "A"}, 60, 10, 5)
    by = {s.section_id: s for s in secs}
    for c in chunks:
        assert by[c.parent_section_id].text[c.char_start:c.char_end] == c.text
        assert c.token_count <= 60
    store = ChunkStore(chunks)
    assert len(store) == len(chunks)
    # overlap exists between consecutive chunks of the long section
    spans = chunk_section(long, _count, 60, 10, 5)
    assert all(spans[i + 1][0] < spans[i][1] for i in range(len(spans) - 1))


def test_chunk_ids_deterministic(tmp_path):
    secs = _parse(tmp_path)
    a = build_chunks(secs, _count, {}, 60, 10, 5, access_date="2026-11-23")
    b = build_chunks(secs, _count, {}, 60, 10, 5, access_date="2026-11-23")
    assert [c.chunk_id for c in a] == [c.chunk_id for c in b]


def test_store_rejects_tampered_chunk(tmp_path):
    secs = _parse(tmp_path)
    chunks = build_chunks(secs, _count, {}, 60, 10, 5)
    chunks[0].text += " tampered"
    import pytest
    with pytest.raises(ValueError):
        ChunkStore(chunks)
