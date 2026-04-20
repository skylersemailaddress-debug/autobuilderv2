from __future__ import annotations

import shutil
from pathlib import Path


def rollback_to_last_valid(current_dir: str, backup_dir: str) -> bool:
    cur = Path(current_dir)
    bak = Path(backup_dir)
    if not bak.exists():
        return False
    if cur.exists():
        shutil.rmtree(cur)
    shutil.copytree(bak, cur)
    return True
