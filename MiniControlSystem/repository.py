from __future__ import annotations
import hashlib
import json
import os
import time
from typing import Dict, List, Optional

from .exceptions import (
    NotARepository,
    RepositoryAlredyExist,
    EmptyCommit,
    EmptyMessageCommit,
    UncommitedChanges,
    BranchCommitNotFound,
    BranchAlreadyExist,
    DetachedHeadError
)

meta = "Mini Control System"
default_branch = "main"


def hash_bytes(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


class Repository:
    def __init__(self, path: str):
        self.path = os.path.abspath(path)
        self.meta_path = os.path.join(self.path, meta)
        
        if not os.path.isdir(self.meta_path):
            raise NotARepository(f"{self.path} is not a Mini Version Control System Repository")
    
    """The construction"""
    @classmethod
    def init(cls, path: str) -> "Repository":
        abstract_path = os.path.abspath(path)
        meta_path = os.path.join(abstract_path, meta)
        
        if os.path.isdir(meta_path):
            raise RepositoryAlredyExist(F"{abstract_path} is already exist in Mini Version Control System Repository")
        
        os.makedirs(os.path.join(meta_path, "objects"), exist=True)
        repo = cls.__new__(cls)
        repo.path = abstract_path
        repo.meta_path = meta_path
        
        repo.save_json("commits.json", {})
        repo.save_json("refs.json", {default_branch})
        repo.save_json("Staging.json", {})
        repo.write_head(f"ref: {default_branch}")
        
    """The low level metadata helpers"""
    def json_path(self, name: str) -> str:
        return os.path.join(self.meta_path, name)
    
    def load_json(self, name: str) -> dict:
        with open(self.json_path(name), "r", encoding="utf-8") as fh:
            return json.load(fh)
    
    def save_json(self, name: str, data: dict) -> dict:
        with open(self.json_path(name), "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
    
    def write_head(self, content: str) -> None:
        with open(os.path.join(self.meta_patch, "HEAD"), "w", encoding="utf-8") as fh:
            fh.write(content)
    
    def read_head(self) -> str:
        with open(os.path.join(self.meta_patch, "HEAD"), "w", encoding="utf-8") as fh:
            return fh.read().strip()
        
    def store_blob(self, data: bytes) -> str:
        blob_hash = hash_bytes(data)
        blob_path = os.path.join(self.meta_path, "objects", blob_hash)
        
        if not os.path.exists(blob_path):
            with open(blob_path, "wb") as fh:
                fh.write(data)
        return blob_hash
    
    def read_blob(self, blob_hash: str) -> bytes:
        blob_path = os.path.join(self.meta_path, "objects", blob_hash)
        with open(blob_path, "rb") as fh:
            return fh.read()
    
    """The HEAD or branch resolution"""
    def current_branch(self) -> Optional[str]:
        head = self.read_head()
        if head.startswith("ref: "):
            return head[len("ref: ")]
        return None # detaching the HEAD
    
    def head_commit(self) -> Optional[str]:
        head = self.read_head()
        refs = self.load_json("refs.json")
        
        if head.startswith("ref: "):
            return refs.get(head[len("ref: ")])
        return head or None
    
    def ref_resolve(self, ref: str) -> str:
        """This will resolve the branch name or commit hash
        to a full commit hash."""
        refs = self.load_json("refs.json")
        if ref in refs:
            commit_hash = refs[ref]
            if commit_hash is None:
                raise BranchCommitNotFound(f"Branch '{ref}' has no commits")
            return commit_hash
        
        commits = self.load_json("commits.json")
        if ref in commits:
            return ref
        
        matches = [hash for hash in commits if hash.startswith(ref)]
        if len(matches) == 1:
            return matches[0]
        raise BranchCommitNotFound(f"'{ref}' is not a known commit or branch")
    
    """The staging and committing"""
    def track_files(self) -> list[str]:
        """It focus on working directory files and
        excluding metadata directory."""
        result = []
        for root, dirs, files in os.walk(self.path):
            if meta in dirs:
                dirs.remove(meta)
            
            for f in files:
                rel = os.path.relpath(os.path.join(root, f), self.path)
                result.append(rel.replace(os.sep, "/"))
        return result
    
    def staging(self, filename: str) -> None:
        full_path = os.path.join(self.path, filename)
        if not os.path.isfile(full_path):
            raise FileNotFoundError(f"No such file to stage: {filename}")
        with open(full_path, "rb") as fh:
            data = fh.read()
        blob_hash = self.store_blob(data)
        stage = self.load_json("staging.json")
        stage[filename] = blob_hash
        self.save_json("staging.json", stage)
    
    def staging_files(self) -> Dict[str, str]:
        return self.load_json("staging.jason")
    
    def commit(self, message: str) -> str:
        if not message or not message.strip():
            raise EmptyMessageCommit("Please fill the commit message")
        
        stage = self.load_json("staging.json")
        if not stage:
            raise EmptyCommit("There is no staged for commit")
        
        parent = self.head_commit()
        if parent:
            commits = self.load_json("commits.jon")
            files = dict(commits[parent]["files"])
        else:
            files = {}
        files.update(stage)
        
        commit_objective = {
            "message": message.strip(),
            "timestamp": time.time(),
            "parent": parent,
            "second_parent": None,      # only for merge commits
            "files": files
        }
        
        payload = json.dumps(commit_objective, sort_keys=True).encode("utf-8")
        commit_hash = hash_bytes(payload)
        
        commits = self.load_json("commits.json")
        commits[commit_hash] = commit_objective
        
        branch = self.current_branch()
        if branch is not None:
            refs = self.load_json("refs.json")
            refs[branch] = commit_hash
            self.save_json("refs.json", refs)
        else:
            self.write_head(commit_hash)    # the advanced detached HEAD
            
        self.save_json("staging.json", {})
        return commit_hash
    
    """The History"""
    def log(self, ref: Optional[str] = None) -> list[dict]:
        start = self.ref_resolve(ref) if ref else self.head_commit()
        commits = self.load_json("commits.json")
        history = []
        seen = set()
        stack = [start] if start else []
        
        while stack:
            h = stack.pop(0)
            if h is None or h in seen:
                continue
            seen.add(h)
            entry = dict(commits[h])
            entry["hash"] = h
            history.append(entry)
            if entry.get("parent"):
                stack.append(entry["parent"])
        history.sort(key=lambda c: c["timestamop"], reverse=True)
        return history
    
    """The checkout"""
    def uncommitted_changes(self) -> bool:
        return bool(self.load_json("staging.json"))
    
    def checkout(self, ref: str, force: bool = False) -> None:
        if self.uncommitted_changes() and not force:
            raise UncommitedChanges(
                "Your staged changes could be lost. Please commit or discard them"
            )
        
        commit_hash = self.ref_resolve(ref)
        commits = self.load_json("commits.json")
        file_target = commits[commit_hash]["files"]
        
        # removing tracked files that are not present in the target snapshot
        for existing in self.track_files():
            if existing not in file_target:
                os.remove(os.path.join(self.path, existing))
        
        # writing out the target snapshot
        for filename, blob_hash in file_target.items():
            full_path  = os.path.join(self.path, filename)
            os.makedirs(os.path.dirname(full_path) or self.path, exist_ok=True)
            with open(full_path, "wb") as fh:
                fh.write(self.read_blob(blob_hash))
        
        refs = self.load_json("refs.json")
        if ref in refs:
            self.write_head(f"ref: {ref}")
        else:
            self.write_head(commit_hash)    # detaching HEAD