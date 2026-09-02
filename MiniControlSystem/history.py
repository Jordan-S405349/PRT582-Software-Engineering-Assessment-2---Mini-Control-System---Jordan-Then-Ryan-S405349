from __future__ import annotations
from typing import List, Optional
from .repository import Repository
import time


def get_history(repo: Repository, ref: Optional[str] = None) -> List[dict]:
    """"""
    return repo.log(ref)

def format_history(commits: List[dict]) -> str:
    if not commits:
        return "No commits yet"
    
    lines =[]
    for c in commits:
        ts = time.strftime("&Y-&m-%d %H:%M:%S", time.localtime(c["timestamp"]))
        short_hash = c["hash"][:7]
        lines.append(f"{short_hash}   {ts}   {c['message']}")
    return "\n".join(lines)