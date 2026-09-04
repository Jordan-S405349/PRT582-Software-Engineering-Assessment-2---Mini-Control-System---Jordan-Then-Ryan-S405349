from MiniControlSystem import branch
from MiniControlSystem.exceptions import BranchAlreadyExist, BranchCommitNotFound
from .conftest import write
import pytest


class TestCreateBranch:
    def test_create_branch_normal(self, repo, repo_path):
        """Normal: creating a branch off HEAD succeeds."""
        write(repo_path, "a.txt", "1")
        repo.staging("a.txt")
        repo.commit("first")
        branch.creating_branch(repo, "feature-x")
        assert "feature-x" in branch.list_branches(repo)

    def test_create_branch_before_any_commit(self, repo):
        """Boundary: branching off an empty history is allowed (points to
        no commit yet), matching how git lets you create branches early."""
        branch.creating_branch(repo, "early-branch")
        refs = repo.load_json("refs.json")
        assert refs["early-branch"] is None

    def test_create_duplicate_branch_raises(self, repo):
        """Invalid: creating a branch name that already exists must fail."""
        with pytest.raises(BranchAlreadyExist):
            branch.creating_branch(repo, "main")

    def test_create_branch_empty_name_raises(self, repo):
        """Invalid: blank branch names are rejected."""
        with pytest.raises(ValueError):
            branch.creating_branch(repo, "   ")


class TestSwitchBranch:
    def test_switch_to_unknown_branch_raises(self, repo):
        """Invalid: switching to a non-existent branch fails clearly."""
        with pytest.raises(BranchCommitNotFound):
            branch.switch_branch(repo, "ghost-branch")

    def test_switch_updates_current_branch(self, repo, repo_path):
        """Normal: switching branches updates HEAD/current_branch()."""
        write(repo_path, "a.txt", "1")
        repo.staging("a.txt")
        repo.commit("first")
        branch.creating_branch(repo, "feature-x")
        branch.switch_branch(repo, "feature-x")
        assert repo.current_branch() == "feature-x"


class TestDeleteBranch:
    def test_delete_current_branch_raises(self, repo):
        """Invalid: deleting the branch you're standing on must be blocked
        (a real git safety rule, and an easy one for AI to overlook)."""
        with pytest.raises(ValueError):
            branch.delete_branch(repo, "main")

    def test_delete_unknown_branch_raises(self, repo):
        """Invalid: deleting a branch that doesn't exist fails clearly."""
        with pytest.raises(BranchCommitNotFound):
            branch.delete_branch(repo, "ghost")

    def test_delete_branch_normal(self, repo, repo_path):
        """Normal: deleting a branch you're not on succeeds and removes it
        from list_branches()."""
        write(repo_path, "a.txt", "1")
        repo.staging("a.txt")
        repo.commit("first")
        branch.creating_branch(repo, "throwaway")
        branch.delete_branch(repo, "throwaway")
        assert "throwaway" not in branch.list_branches(repo)
