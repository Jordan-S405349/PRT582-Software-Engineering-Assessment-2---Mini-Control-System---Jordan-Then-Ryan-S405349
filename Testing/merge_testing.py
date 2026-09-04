from MiniControlSystem import branch, merge
from MiniControlSystem.exceptions import(
    MergeConflictError,
    BranchCommitNotFound,
    UncommitedChanges
)
from .conftest import write
import pytest

def commit(repo, repo_path, filename, content, message):
    write(repo_path, filename, content)
    repo.staging(filename)
    return repo.commit(message)


class TestFastForwardMerge:
    def test_fast_forward_when_no_divergence(self, repo, repo_path):
        """Normal: merging a branch that's strictly ahead just fast-forwards."""
        commit(repo, repo_path, "a.txt", "1", "base")
        branch.creating_branch(repo, "feature")
        branch.switch_branch(repo, "feature")
        commit(repo, repo_path, "a.txt", "2", "feature change")
        branch.switch_branch(repo, "main")

        result = merge.merge(repo, "feature")
        assert result["status"] == "fast_forward"
        with open(f"{repo_path}/a.txt") as fh:
            assert fh.read() == "2"

    def test_merge_already_up_to_date(self, repo, repo_path):
        """Boundary: merging a branch with no new commits reports up_to_date."""
        commit(repo, repo_path, "a.txt", "1", "base")
        branch.creating_branch(repo, "feature")
        result = merge.merge(repo, "feature")
        assert result["status"] == "up_to_date"

    def test_merge_unknown_branch_raises(self, repo):
        """Invalid: merging a branch that doesn't exist fails clearly."""
        with pytest.raises(BranchCommitNotFound):
            merge.merge(repo, "ghost-branch")

    def test_merge_blocked_by_uncommitted_changes(self, repo, repo_path):
        """Invalid: merge must not silently discard staged work."""
        commit(repo, repo_path, "a.txt", "1", "base")
        branch.creating_branch(repo, "feature")
        write(repo_path, "b.txt", "uncommitted")
        repo.staging("b.txt")
        with pytest.raises(UncommitedChanges):
            merge.merge(repo, "feature")


class TestThreeWayMerge:
    def test_merge_non_conflicting_changes(self, repo, repo_path):
        """Normal: both branches edit different files -> clean auto-merge."""
        commit(repo, repo_path, "shared.txt", "base", "base commit")
        branch.creating_branch(repo, "feature")

        commit(repo, repo_path, "main_only.txt", "main change", "change on main")

        branch.switch_branch(repo, "feature")
        commit(repo, repo_path, "feature_only.txt", "feature change", "change on feature")

        branch.switch_branch(repo, "main")
        result = merge.merge(repo, "feature")

        assert result["status"] == "merged"
        commits = repo.load_json("commits.json")
        merged_files = commits[result["commit"]]["files"]
        assert set(merged_files.keys()) == {"shared.txt", "main_only.txt", "feature_only.txt"}

    def test_merge_conflict_detected(self, repo, repo_path):
        """Invalid/exception: both branches edit the SAME file differently
        -> must raise MergeConflictError naming the conflicting file, and
        must NOT silently pick one side's version."""
        commit(repo, repo_path, "shared.txt", "base", "base commit")
        branch.creating_branch(repo, "feature")

        commit(repo, repo_path, "shared.txt", "main version", "main edits shared.txt")

        branch.switch_branch(repo, "feature")
        commit(repo, repo_path, "shared.txt", "feature version", "feature edits shared.txt")

        branch.switch_branch(repo, "main")
        with pytest.raises(MergeConflictError) as excinfo:
            merge.merge(repo, "feature")
        assert "shared.txt" in excinfo.value.conflict

    def test_merge_does_not_mutate_state_on_conflict(self, repo, repo_path):
        """Regression: a failed merge must leave refs untouched, so the
        user can retry after resolving -- this guards against a bug we
        found where a partial merge commit was written before the
        conflict check ran (see Task 3 of the report)."""
        commit(repo, repo_path, "shared.txt", "base", "base commit")
        branch.creating_branch(repo, "feature")
        commit(repo, repo_path, "shared.txt", "main version", "main edit")
        branch.switch_branch(repo, "feature")
        commit(repo, repo_path, "shared.txt", "feature version", "feature edit")
        branch.switch_branch(repo, "main")

        refs_before = dict(repo.load_json("refs.json"))
        with pytest.raises(MergeConflictError):
            merge.merge(repo, "feature")
        refs_after = dict(repo.load_json("refs.json"))
        assert refs_before == refs_after

    def test_merge_same_deletion_is_not_a_conflict(self, repo, repo_path):
        """Boundary: if both branches independently arrive at the same
        result for a file, it's not a conflict even though both changed it."""
        commit(repo, repo_path, "shared.txt", "base", "base commit")
        branch.creating_branch(repo, "feature")

        commit(repo, repo_path, "shared.txt", "same edit", "main edit")

        branch.switch_branch(repo, "feature")
        commit(repo, repo_path, "shared.txt", "same edit", "feature edit (identical result)")

        branch.switch_branch(repo, "main")
        result = merge.merge(repo, "feature")
        assert result["status"] == "merged"
