from __future__ import annotations
from typing import Dict, List, Optional
from repository import Repository
from exceptions import (
    MergeConflictError,
    BranchCommitNotFound,
    UncommitedChanges
)


def ancestor(repo: Repository, commit_hash: Optional[str]) -> List[str]:
    """It will returning all the ancestor commit hashes, commit_hash go first, and the oldest last"""
    commits = repo.load_json("commits.json")
    chain = []
    h = commit_hash
    while h is not None:
        chain.append(h)
        h = commits[h].get("parent")
    return chain


def find_common_ancestor(repo: Repository, commit_a: str, commit_b: str) -> Optional[str]:
    ancestors = set(ancestor(repo, commit_a))
    for h in ancestor(repo, commit_b):
        if h in ancestors:
            return h
    return None


def mmerge(repo: Repository, source_branch: str) -> Dict:
    """Merging the 'source_branch' into the current branch
    """
    
    if repo.uncommitted_changes():
        raise UncommitedChanges("PLease commit or discard stages change before merging")
    
    current_branch = repo.current_branch()
    if current_branch is None:
        raise ValueError("Cannot be merge due in detached HEAD state")
    
    refs = repo.load_json("refs.json")
    if source_branch not in refs:
        raise BranchCommitNotFound(f"Branch '{source_branch}' does not exist")
    
    our_hash = refs[current_branch]
    their_hash = refs[source_branch]