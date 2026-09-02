import shutil
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from MiniControlSystem import Repository, branch, merge, history
from MiniControlSystem.exceptions import MergeConflictError

DEMO_DIR = "demo_repo"


def write(filename, content):
    with open(os.path.join(DEMO_DIR, filename), "w") as fh:
        fh.write(content)


def section(title):
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


if os.path.exists(DEMO_DIR):
    shutil.rmtree(DEMO_DIR)
os.makedirs(DEMO_DIR)

section("1. Initialise repository")
repo = Repository.init(DEMO_DIR)
print(f"Initialised empty Mini VCS repository in {DEMO_DIR}/.minivcs")
print(f"Current branch: {repo.current_branch()}")

section("2. Stage and commit")
write("readme.txt", "Mini VCS demo project")
repo.staging("readme.txt")
c1 = repo.commit("Initial commit")
print(f"Committed {c1[:7]} -> 'Initial commit'")

section("3. Create and switch branch")
branch.create_branch(repo, "feature/login")
branch.switch_branch(repo, "feature/login")
print(f"Branches: {branch.list_branches(repo)}")
print(f"Now on: {repo.current_branch()}")

write("login.py", "def login(): pass")
repo.staging("login.py")
c2 = repo.commit("Add login stub")
print(f"Committed {c2[:7]} -> 'Add login stub'")

section("4. Checkout back to main")
branch.switch_branch(repo, "main")
print(f"Now on: {repo.current_branch()}")
print(f"Files present: {os.listdir(DEMO_DIR)}")

section("5. Merge feature/login into main (fast-forward)")
result = merge.merge(repo, "feature/login")
print(f"Merge result: {result['status']}")
print(f"Files present after merge: {os.listdir(DEMO_DIR)}")

section("6. Conflict detection demo")
branch.create_branch(repo, "conflict-branch")
write("readme.txt", "Changed on main")
repo.stage("readme.txt")
repo.commit("Edit readme on main")

branch.switch_branch(repo, "conflict-branch")
write("readme.txt", "Changed on conflict-branch")
repo.stage("readme.txt")
repo.commit("Edit readme on conflict-branch")

branch.switch_branch(repo, "main")
try:
    merge.merge(repo, "conflict-branch")
except MergeConflictError as e:
    print(f"MergeConflictError raised as expected: {e}")

section("7. Commit history")
print(history.format_history(history.get_history(repo)))

print("\nDemo complete.")