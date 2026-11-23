"""Generate the Colab notebooks from cell lists (keeps notebooks reviewable as code)."""
import json
from pathlib import Path

SETUP = [
    "md:# LearnMate — {title}\nRuns on a free Colab **T4** (Runtime → Change runtime type → GPU). "
    "Checkpoints and caches are written to Google Drive so a disconnect never loses work.",
    "from google.colab import drive\ndrive.mount('/content/drive')",
    "%cd /content\n!git clone -b claude/wonderful-bohr-1idsaa https://github.com/KirtirajChaudhari/LearnMate.git || (cd LearnMate && git pull)\n%cd /content/LearnMate",
    "!pip -q install -e '.[gpu,eval,dev]'\n!nvidia-smi --query-gpu=name,memory.total --format=csv",
    "# persist large/expensive artifacts on Drive\nimport os\nD='/content/drive/MyDrive/learnmate'\nfor sub in ['data_raw','data_processed','data_cache','models','results']:\n    os.makedirs(f'{D}/{sub}', exist_ok=True)\n!mkdir -p data && ln -sfn {D}/data_raw data/raw && ln -sfn {D}/data_processed data/processed && ln -sfn {D}/data_cache data/cache && ln -sfn {D}/models models && ln -sfn {D}/results results".replace("{D}", "$D"),
    "!test -d data/raw/d2l-en || git clone https://github.com/d2l-ai/d2l-en.git data/raw/d2l-en\n!git -C data/raw/d2l-en checkout -q 23d7a5aecceee57d1292c56e90cce307f183bb0a\n!python -m learnmate.ingest --check\n!python scripts/build_squad.py",
]

NB = {
    "00_smoke_colab.ipynb": ("M0 environment smoke test", [
        "md:Loads every model once, runs a forward pass and records latency and **peak VRAM** to `results/m0_smoke.json`. "
        "The fp16 vs NF4 result decides the frozen generator runtime (ADR-003).",
        "!python scripts/smoke_models.py\n!cat results/m0_smoke.json",
        "!pip freeze > requirements.lock && head -50 requirements.lock",
        "!python -m pytest -q",
    ]),
    "01_gate_training.ipynb": ("M4 sufficiency-gate training", [
        "md:Trains the DeBERTa-v3-base sufficiency gate on SQuAD 2.0 + BM25 hard negatives (spec C6) and the "
        "no-hard-negative ablation (A4). Resumable: rerun the same cell with `--resume` after a disconnect.",
        "!python -m learnmate.gate.train --out models/gate-v1 --resume",
        "!python -m learnmate.gate.train --out models/gate-noHN --no-hard-negatives --resume",
        "import json\nfor m in ['gate-v1','gate-noHN']:\n    log=json.load(open(f'models/{m}/train_log.json'))\n    print(m, {k:log[k] for k in ['best_dev_auroc','gpu_minutes','peak_vram_gb','examples_per_sec','steps']})",
    ]),
    "02_experiments.ipynb": ("M5–M7 experiments", [
        "md:## 1. Indices and calibration-split runs (allowed before pre-registration)",
        "!python scripts/build_indices.py",
        "!python -m eval.run --split squad-cal --stages all",
        "!python -m eval.run --split course-dev --stages all\n!python -m eval.run --split course-dev --condition S4 --stages all\n!python -m eval.run --split course-cal --stages all",
        "md:Judge course-cal outputs (blinded) before calibrating — see `annotation/GUIDELINES.md` §6.",
        "!python -m learnmate.annotation judge-sheet --run results/runs/course-cal__clean --out data/annotations/judge_cal.jsonl",
        "!python -m eval.calibrate --squad-cal results/runs/squad-cal__clean --course-cal results/runs/course-cal__clean --judgments data/annotations/judgments_cal.jsonl --course-dev-s4 results/runs/course-dev__S4",
        "md:## 2. STOP — write `research/preregistration.md` (STATUS: FROZEN), commit and tag `prereg-v1` before continuing.",
        "md:## 3. Locked test runs (executed once)",
        "for cond in ['clean','S1','S2','S3','S4']:\n    !python -m eval.run --split course-test --condition {cond} --stages all --require-prereg\n!python -m eval.run --split squad-test --stages all --require-prereg\n!python -m eval.run --split course-test --stages evaluator --require-prereg",
        "md:Judge test outputs blinded (GUIDELINES §6), merge, then run the registered analysis.",
        "!python -m eval.analyze --run results/runs/course-test__clean --judgments data/annotations/judgments_test.jsonl\n!python -m eval.analyze --run results/runs/squad-test__clean",
        "for cond in ['S1','S2','S3','S4']:\n    !python -m eval.analyze --run results/runs/course-test__{cond} --judgments data/annotations/judgments_test.jsonl",
        "!python scripts/make_figures.py",
    ]),
}


def cell(src):
    if src.startswith("md:"):
        return {"cell_type": "markdown", "metadata": {}, "source": src[3:]}
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": src}


for name, (title, cells) in NB.items():
    nb = {"nbformat": 4, "nbformat_minor": 5,
          "metadata": {"accelerator": "GPU", "colab": {"provenance": []}, "kernelspec": {"name": "python3", "display_name": "Python 3"}},
          "cells": [cell(SETUP[0].format(title=title))] + [cell(c) for c in SETUP[1:]] + [cell(c) for c in cells]}
    Path("notebooks", name).write_text(json.dumps(nb, indent=1))
    print("wrote notebooks/" + name)
