from __future__ import annotations
from typing import Dict, List, Optional
from repository import Repository, hash_bytes
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
    
    if their_hash is None:
        return {"status": "up_to_date"}
    if our_hash == their_hash:
        return {"status": "up_to_date"}
    
    ancestor_hash = find_common_ancestor(repo, our_hash, their_hash) if our_hash else None
    
    # fast foward:
    if our_hash is None or ancestor_hash == our_hash:
        refs[current_branch] = their_hash
        repo.save_json("refs.json", refs)
        repo.checkout(current_branch, force=True)
        return {"status": "fast_forward", "commit": their_hash}
    
    # already up to date:
    if ancestor_hash == their_hash:
        return {"status": "up_to_date"}
    
    commits = repo.load_json("commits.json")
    base_file = commits[ancestor_hash]["files"] if ancestor_hash else {}
    our_file = commits[our_hash]["files"]
    their_file = commits[their_hash]["files"]
    
    merged_files = dict(our_file)
    conflict = []
    all_path = set(base_file) | set(our_file) | set(their_file)
    
    for path in all_path:
        base_blob = base_file.get(path)
        our_blob = our_file.get(path)
        their_blob = their_file.get(path)
        
        if our_blob == their_blob:
            continue # both identical
        if our_blob == base_blob:
            # we did not change it, taking their changes
            if their_blob is None:
                merged_files.pop(path, None)
            else:
                merged_files[path] = their_blob
        elif their_blob == base_blob:
            continue # we did change it, it keep ours
        else:
            conflict.append(path) # both changed differently
            
    if conflict:
        raise MergeConflictError(sorted(conflict))
    
    import time as time
    commit_objects = {
        "message": f"Merge brench '{source_branch}' into {current_branch}",
        "timestamp": time.time(),
        "parent": our_hash,
        "second_parent": their_hash,
        "files": merged_files
    }
    
    import json as json
    payload = json.dumps(commit_objects, sort_keys=True).encode("utf-8")
    commit_hash = hash_bytes(payload)
    commits[commits] = commit_objects
    repo.save_json("commits.json", commits)
    refs[current_branch] = commit_hash
    repo.save_json("refs.json", refs)
    repo.checkout(current_branch, force=True)
    
    return {"status": "merged", "commit": commit_hash}