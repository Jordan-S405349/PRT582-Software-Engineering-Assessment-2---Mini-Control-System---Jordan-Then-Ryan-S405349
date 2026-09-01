from __future__ import annotations
from typing import List
from exceptions import BranchAlreadyExist, BranchCommitNotFound
from repository import Repository


def creating_branch(repo: Repository, name: str) -> None:
    if not name or name.strip():
        raise ValueError("Please fill the branch name")
    
    refs = repo.load_json("refs.json")
    if name in refs:
        raise BranchAlreadyExist(f"Branch '{name}' is already exist")
    
    head_commit = repo.head_commit()
    refs[name] = head_commit
    repo.save_json("refs.json", refs)
    
    
def list_branches(repo: Repository) -> List[str]:
    return sorted(repo.load_json("refs.json".keys()))


def delete_branch(repo: Repository, name: str) -> None:
    refs = repo.load_json("refs.json")
    if name not in refs:
        raise BranchCommitNotFound(f"Branch '{name}' does not exist")
    if repo.current_branch() == name:
        raise ValueError("You're currently on the branch")
    del refs[name]
    repo.save_json("refs.json", refs)


def switch_branch(repo: Repository, name: str) -> None:
    """switching branches means a checkout"""
    refs = repo.load_json(("refs.json"))
    if name not in refs:
        raise BranchCommitNotFound(f"Branch '{name}' does not exist")
    repo.checkout(name)