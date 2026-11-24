"""Colab helper: persist big artifacts on Google Drive via symlinks. Idempotent; repairs earlier broken layouts.

    python scripts/colab_setup.py     # Drive must be mounted: from google.colab import drive; drive.mount('/content/drive')
Env: LEARNMATE_DRIVE (default /content/drive/MyDrive/learnmate)

Only UNTRACKED paths are linked. Directories that contain git-tracked files (data/processed, results) stay real
directories, otherwise git refuses to pull ("beyond a symbolic link"). An older version linked those whole
directories; this script migrates their contents and restores the tracked files.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRIVE = Path(os.environ.get("LEARNMATE_DRIVE", "/content/drive/MyDrive/learnmate"))
LINKS = {  # repo path -> Drive folder
    "data/raw": "data_raw", "data/cache": "data_cache", "models": "models", "configs/frozen": "frozen",
    "data/processed/indices": "processed_indices", "data/processed/squad_rag": "processed_squad_rag",
    "results/runs": "results_runs", "results/figures": "results_figures",
}
LEGACY = {  # whole-directory links made by older versions: repo path -> (old Drive folder, {child: new Drive folder})
    "data/processed": ("data_processed", {"indices": "processed_indices", "squad_rag": "processed_squad_rag"}),
    "results": ("results", {"runs": "results_runs", "figures": "results_figures"}),
}


def git(*args) -> None:
    subprocess.run(["git", "-C", str(ROOT), *args], check=False, capture_output=True)


def main() -> None:
    if not DRIVE.parent.is_dir():
        sys.exit(f"{DRIVE.parent} not found: mount Google Drive first:\n"
                 "  from google.colab import drive; drive.mount('/content/drive')")
    for dst_rel, (old_sub, children) in LEGACY.items():
        dst = ROOT / dst_rel
        if not dst.is_symlink():
            continue
        old = DRIVE / old_sub
        for child, new_sub in children.items():  # keep what earlier runs produced
            src, new = old / child, DRIVE / new_sub
            if src.exists() and not src.is_symlink() and not new.exists():
                shutil.move(str(src), str(new))
                print(f"migrated {old_sub}/{child} -> {new_sub}")
        dst.unlink()
        dst.mkdir(parents=True, exist_ok=True)
        git("checkout", "HEAD", "--", dst_rel)       # restore the git-tracked files inside
        print(f"{dst_rel}: whole-directory link replaced by a real directory (tracked files restored)")
    for dst_rel, sub in LINKS.items():
        target, dst = DRIVE / sub, ROOT / dst_rel
        target.mkdir(parents=True, exist_ok=True)
        if dst.is_symlink() or dst.is_file():          # also removes DANGLING links (exists() is False for those)
            dst.unlink()
        elif dst.exists():                              # real directory made locally: move its contents to Drive
            shutil.copytree(dst, target, dirs_exist_ok=True)
            shutil.rmtree(dst)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.symlink_to(target, target_is_directory=True)
        print(f"{dst_rel} -> {target}")
    stray = ROOT / "$D"                                 # left behind by the first, buggy setup cell
    if stray.exists():
        shutil.rmtree(stray)
        print("removed stray directory '$D'")


if __name__ == "__main__":
    main()
