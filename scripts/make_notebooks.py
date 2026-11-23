"""Generate the Colab notebooks from cell lists (keeps notebooks reviewable as code)."""
import json
from pathlib import Path

SETUP = [
    "md:# LearnMate — {title}\nRuns on a free Colab **T4** (Runtime → Change runtime type → GPU). "
    "Checkpoints and caches are written to Google Drive so a disconnect never loses work.",
    "from google.colab import drive\ndrive.mount('/content/drive')",
    "%cd /content\n!git clone -b claude/wonderful-bohr-1idsaa https://github.com/KirtirajChaudhari/LearnMate.git || (cd LearnMate && git pull)\n%cd /content/LearnMate",
    "!pip -q install -e '.[gpu,eval,dev]'\n!nvidia-smi --query-gpu=name,memory.total --format=csv",
    "# persist large/expensive artifacts on Drive (safe against directories that are tracked in git)\nimport os, shutil\nD = '/content/drive/MyDrive/learnmate'\nfor dst, sub in {'data/raw': 'data_raw', 'data/processed': 'data_processed', 'data/cache': 'data_cache', 'models': 'models', 'results': 'results'}.items():\n    os.makedirs(f'{D}/{sub}', exist_ok=True)\n    if os.path.islink(dst): os.remove(dst)\n    elif os.path.exists(dst): shutil.rmtree(dst)\n    os.makedirs(os.path.dirname(dst) or '.', exist_ok=True)\n    os.symlink(f'{D}/{sub}', dst)\nprint(os.listdir('/content/LearnMate/data'))",
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


DEADLINE_SETUP = [c for c in SETUP]
DEADLINE_SETUP[3] = "!pip -q install -e '.[gpu,dev]'\n!nvidia-smi --query-gpu=name,memory.total --format=csv"

NB_DEADLINE = ("Deadline profile: reduced end-to-end run", [
    "md:**Run the parts in order. Every stage is cached and resumable: after a disconnect, rerun the same cell.**\n\nPart 1 needs no human input.",
    "md:## Part 1a — indices and the sufficiency gate",
    "!python scripts/build_indices.py",
    "!python -m learnmate.gate.train --out models/gate-v1 --pairs 24000 --epochs 1 --resume\n!cat models/gate-v1/train_log.json | head -40",
    "md:## Part 1b — calibration-split run (SQuAD, 300 questions) and calibration",
    "!python -m eval.run --split squad-cal --stages retrieve generate gate b0 verify assemble",
    "!python -m eval.calibrate --squad-cal results/runs/squad-cal__clean",
    "md:## STOP — Part 2 needs the frozen course items (git pull the verified `data/annotations/course_items.jsonl`, then `python -m learnmate.annotation freeze`) and `python scripts/freeze_prereg.py`.",
    "!git pull -q --autostash\n!python -m learnmate.annotation validate\n!python -m learnmate.annotation assign-splits --all-split test\n!python -m learnmate.annotation kappa\n!python -m learnmate.annotation freeze\n!python scripts/freeze_prereg.py --dtype float16",
    "md:## Part 2 — locked test runs (once)",
    "!python -m eval.run --split course-test --condition clean --stages retrieve generate gate b0 verify assemble --require-prereg\n!python -m eval.run --split course-test --condition S1 --stages retrieve generate gate b0 verify assemble --require-prereg\n!python -m eval.run --split squad-test --stages retrieve generate gate b0 verify assemble --require-prereg",
    "md:## Part 3 — blinded judging sheet (download `judge_test.jsonl`, judge with `python scripts/review.py judge`, upload the judged file back)",
    "!python -m learnmate.annotation judge-sheet --run results/runs/course-test__clean --out data/annotations/judge_test.jsonl",
    "md:After judging: `python -m learnmate.annotation merge --sheet data/annotations/judge_test.jsonl --key data/annotations/judge_test_KEY_DO_NOT_OPEN.jsonl --out data/annotations/judgments_test.jsonl`",
    "!python -m learnmate.annotation merge --sheet data/annotations/judge_test.jsonl --key data/annotations/judge_test_KEY_DO_NOT_OPEN.jsonl --out data/annotations/judgments_test.jsonl\n!python -m eval.analyze --run results/runs/course-test__clean --judgments data/annotations/judgments_test.jsonl\n!python -m eval.analyze --run results/runs/course-test__S1\n!python -m eval.analyze --run results/runs/squad-test__clean\n!python scripts/make_figures.py",
    "md:## Optional — live demo from Colab (for the recorded walkthrough)",
    "!wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O cloudflared && chmod +x cloudflared\nimport subprocess, time\nsubprocess.Popen(['streamlit','run','app/streamlit_app.py','--server.port','8501','--server.headless','true'])\nsubprocess.Popen(['./cloudflared','tunnel','--url','http://localhost:8501'], stdout=open('tunnel.log','w'), stderr=subprocess.STDOUT)\ntime.sleep(15)\n!grep -o 'https://[a-z0-9-]*[.]trycloudflare[.]com' tunnel.log | head -1",
])
NB["03_deadline_run.ipynb"] = NB_DEADLINE


def cell(src):
    if src.startswith("md:"):
        return {"cell_type": "markdown", "metadata": {}, "source": src[3:]}
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": src}


for name, (title, cells) in NB.items():
    setup = DEADLINE_SETUP if name.startswith("03") else SETUP
    nb = {"nbformat": 4, "nbformat_minor": 5,
          "metadata": {"accelerator": "GPU", "colab": {"provenance": []}, "kernelspec": {"name": "python3", "display_name": "Python 3"}},
          "cells": [cell(setup[0].format(title=title))] + [cell(c) for c in setup[1:]] + [cell(c) for c in cells]}
    Path("notebooks", name).write_text(json.dumps(nb, indent=1))
    print("wrote notebooks/" + name)
