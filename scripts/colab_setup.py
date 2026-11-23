"""Colab helper: persist big artifacts on Google Drive via symlinks. Idempotent; repairs dangling links.

    python scripts/colab_setup.py            # Drive must be mounted (from google.colab import drive; drive.mount('/content/drive'))
Env: LEARNMATE_DRIVE (default /content/drive/MyDrive/learnmate)
"""
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRIVE = Path(os.environ.get("LEARNMATE_DRIVE", "/content/drive/MyDrive/learnmate"))
LINKS = {"data/raw": "data_raw", "data/processed": "data_processed", "data/cache": "data_cache",
         "models": "models", "results": "results"}


def main() -> None:
    if not DRIVE.parent.is_dir():
        sys.exit(f"{DRIVE.parent} not found: mount Google Drive first:\n"
                 "  from google.colab import drive; drive.mount('/content/drive')")
    for dst_rel, sub in LINKS.items():
        target, dst = DRIVE / sub, ROOT / dst_rel
        target.mkdir(parents=True, exist_ok=True)
        if dst.is_symlink() or dst.is_file():      # also removes DANGLING symlinks (exists() is False for those)
            dst.unlink()
        elif dst.exists():
            shutil.rmtree(dst)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.symlink_to(target, target_is_directory=True)
        print(f"{dst_rel} -> {target}")
    stray = ROOT / "$D"                            # left behind by the old (buggy) setup cell
    if stray.exists():
        shutil.rmtree(stray)
        print("removed stray directory '$D'")


if __name__ == "__main__":
    main()
