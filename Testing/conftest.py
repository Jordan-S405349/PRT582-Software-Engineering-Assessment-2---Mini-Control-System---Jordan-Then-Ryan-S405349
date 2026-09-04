import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from MiniControlSystem.repository import Repository

def write(repo_path, filename, content):
    full = os.path.join(repo_path, filename)
    os.makedirs(os.path.dirname(full) or repo_path, exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(content)


@pytest.fixture
def repo(tmp_path):
    """creating a temp directory"""
    return Repository.init(str(tmp_path))


@pytest.fixture
def repo_path(tmp_path):
    return str(tmp_path)