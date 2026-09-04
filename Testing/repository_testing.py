import os
import pytest

from MiniControlSystem.repository import Repository
from MiniControlSystem.exceptions import (
    EmptyCommit,
    EmptyMessageCommit,
    NotARepository,
    BranchCommitNotFound,
    RepositoryAlredyExist,
    UncommitedChanges
)
from .conftest import write


# init() testing
class TestInit:
    def test_init_creates_metadata_dir(self, tmp_path):
        """Normal: init() should create the Mini Control System directory."""
        Repository.init(str(tmp_path))
        assert os.path.isdir(os.path.join(tmp_path, "Mini Control System"))

    def test_init_default_branch_is_main(self, repo):
        """Normal: a fresh repo starts on 'main' with no commits."""
        assert repo.current_branch() == "main"
        assert repo.head_commit() is None

    def test_init_twice_raises(self, tmp_path):
        """Invalid: re-initialising an existing repo must fail loudly,
        not silently wipe history (this is a real defect AI-generated
        code is prone)."""
        Repository.init(str(tmp_path))
        with pytest.raises(RepositoryAlredyExist):
            Repository.init(str(tmp_path))

    def test_opening_non_repo_raises(self, tmp_path):
        """Invalid: constructing Repository() on a plain folder must fail."""
        with pytest.raises(NotARepository):
            Repository(str(tmp_path))


# stage() or commit() testing
class TestStageAndCommit:
    def test_stage_then_commit_normal(self, repo, repo_path):
        """Normal: staging one file and committing succeeds."""
        write(repo_path, "a.txt", "hello")
        repo.staging("a.txt")
        commit_hash = repo.commit("first commit")
        assert commit_hash in repo.load_json("commits.json")

    def test_commit_with_empty_staging_raises(self, repo):
        """Invalid: committing nothing must be rejected, not create an
        empty/no-op commit (prevents meaningless history entries)."""
        with pytest.raises(EmptyCommit):
            repo.commit("nothing to see here")

    def test_commit_with_blank_message_raises(self, repo, repo_path):
        """Boundary/invalid: whitespace-only messages are rejected."""
        write(repo_path, "a.txt", "hello")
        repo.staging("a.txt")
        with pytest.raises(EmptyMessageCommit):
            repo.commit("   ")

    def test_stage_nonexistent_file_raises(self, repo):
        """Invalid: staging a file that doesn't exist must fail clearly."""
        with pytest.raises(FileNotFoundError):
            repo.staging("does_not_exist.txt")

    def test_staging_clears_after_commit(self, repo, repo_path):
        """Boundary: staging area is empty immediately after a commit,
        so a second commit with nothing new staged is correctly rejected."""
        write(repo_path, "a.txt", "hello")
        repo.staging("a.txt")
        repo.commit("first")
        assert repo.staging_files() == {}
        with pytest.raises(EmptyCommit):
            repo.commit("second, but nothing staged")

    def test_second_commit_carries_forward_unchanged_files(self, repo, repo_path):
        """Normal: committing file B shouldn't drop already-committed file A
        (a common AI-generated bug: overwriting the snapshot instead of
        layering on top of the parent)."""
        write(repo_path, "a.txt", "A")
        repo.staging("a.txt")
        repo.commit("add a")

        write(repo_path, "b.txt", "B")
        repo.staging("b.txt")
        c2 = repo.commit("add b")

        commits = repo.load_json("commits.json")
        assert set(commits[c2]["files"].keys()) == {"a.txt", "b.txt"}

    def test_identical_content_shares_one_blob(self, repo, repo_path):
        """Boundary: two files with identical content should be
        content-addressed to the same blob (storage efficiency check)."""
        write(repo_path, "a.txt", "same")
        write(repo_path, "b.txt", "same")
        repo.staging("a.txt")
        repo.staging("b.txt")
        repo.commit("dup content")
        staged_before_clear = repo.load_json("commits.json")
        last = list(staged_before_clear.values())[0]
        assert last["files"]["a.txt"] == last["files"]["b.txt"]


class TestRemove:
    def test_remove_tracked_file_normal(self, repo, repo_path):
        """Normal: removing a committed file and committing the removal
        drops it from the next commit's snapshot."""
        write(repo_path, "a.txt", "1")
        repo.staging("a.txt")
        repo.commit("add a")

        repo.remove("a.txt")
        c2 = repo.commit("remove a")

        commits = repo.load_json("commits.json")
        assert "a.txt" not in commits[c2]["files"]

    def test_remove_deletes_working_directory_file(self, repo, repo_path):
        """Normal: remove() also deletes the file from the working directory,
        mirroring `git rm` rather than just untracking it."""
        write(repo_path, "a.txt", "1")
        repo.staging("a.txt")
        repo.commit("add a")

        repo.remove("a.txt")
        assert not os.path.exists(os.path.join(repo_path, "a.txt"))

    def test_remove_untracked_file_raises(self, repo):
        """Invalid: removing a file that was never committed or staged
        must fail clearly rather than silently no-op."""
        with pytest.raises(FileNotFoundError):
            repo.remove("never_existed.txt")

    def test_remove_then_checkout_restores_file(self, repo, repo_path):
        """Regression: after committing a removal, checking out the
        PREVIOUS commit must bring the file back -- proving deletion is
        tracked as real history, not a destructive edit."""
        write(repo_path, "a.txt", "1")
        repo.staging("a.txt")
        c1 = repo.commit("add a")

        repo.remove("a.txt")
        repo.commit("remove a")

        repo.checkout(c1)
        with open(os.path.join(repo_path, "a.txt")) as fh:
            assert fh.read() == "1"

    def test_remove_other_files_unaffected(self, repo, repo_path):
        """Boundary: removing one file must not affect other tracked files
        in the same commit."""
        write(repo_path, "a.txt", "1")
        write(repo_path, "b.txt", "2")
        repo.staging("a.txt")
        repo.staging("b.txt")
        repo.commit("add both")

        repo.remove("a.txt")
        c2 = repo.commit("remove a only")

        commits = repo.load_json("commits.json")
        assert set(commits[c2]["files"].keys()) == {"b.txt"}


# log() Testing
class TestLog:
    def test_log_empty_repo(self, repo):
        """Boundary: log() on a repo with zero commits returns an empty list."""
        assert repo.log() == []

    def test_log_returns_newest_first(self, repo, repo_path):
        """Normal: log() orders commits from newest to oldest."""
        write(repo_path, "a.txt", "1")
        repo.staging("a.txt")
        repo.commit("first")
        write(repo_path, "a.txt", "2")
        repo.staging("a.txt")
        repo.commit("second")

        history = repo.log()
        assert [c["message"] for c in history] == ["second", "first"]



# checkout() testing
class TestCheckout:
    def test_checkout_unknown_ref_raises(self, repo):
        """Invalid: checking out a branch/commit that doesn't exist."""
        with pytest.raises(BranchCommitNotFound):
            repo.checkout("does-not-exist")

    def test_checkout_blocked_by_uncommitted_changes(self, repo, repo_path):
        """Invalid: checkout must refuse to silently discard staged work."""
        write(repo_path, "a.txt", "1")
        repo.staging("a.txt")
        repo.commit("first")

        write(repo_path, "b.txt", "uncommitted")
        repo.staging("b.txt")
        with pytest.raises(UncommitedChanges):
            repo.checkout("main")

    def test_checkout_restores_file_content(self, repo, repo_path):
        """Normal: checking out an earlier commit restores that snapshot."""
        write(repo_path, "a.txt", "version1")
        repo.staging("a.txt")
        c1 = repo.commit("v1")

        write(repo_path, "a.txt", "version2")
        repo.staging("a.txt")
        repo.commit("v2")

        repo.checkout(c1)
        with open(os.path.join(repo_path, "a.txt")) as fh:
            assert fh.read() == "version1"

    def test_checkout_removes_files_not_in_target_snapshot(self, repo, repo_path):
        """Boundary: a file created after the target commit must be
        removed from the working directory on checkout."""
        write(repo_path, "a.txt", "1")
        repo.staging("a.txt")
        c1 = repo.commit("only a")

        write(repo_path, "b.txt", "2")
        repo.staging("b.txt")
        repo.commit("add b")

        repo.checkout(c1)
        assert not os.path.exists(os.path.join(repo_path, "b.txt"))

    def test_checkout_by_hash_prefix(self, repo, repo_path):
        """Normal: a unique short hash prefix resolves like Git's `git checkout <short-sha>`."""
        write(repo_path, "a.txt", "1")
        repo.staging("a.txt")
        c1 = repo.commit("first")
        write(repo_path, "a.txt", "2")
        repo.staging("a.txt")
        repo.commit("second")

        repo.checkout(c1[:7])
        with open(os.path.join(repo_path, "a.txt")) as fh:
            assert fh.read() == "1"

    def test_checkout_commit_hash_enters_detached_head(self, repo, repo_path):
        """Normal: checking out a raw commit hash (not a branch) detaches HEAD,
        matching real Git's detached-HEAD behaviour."""
        write(repo_path, "a.txt", "1")
        repo.staging("a.txt")
        c1 = repo.commit("first")
        repo.checkout(c1)
        assert repo.current_branch() is None

    def test_commit_while_detached_advances_head_not_branch(self, repo, repo_path):
        """Boundary: committing in detached HEAD must not move 'main' --
        this is the exact scenario real Git warns about losing commits in."""
        write(repo_path, "a.txt", "1")
        repo.staging("a.txt")
        c1 = repo.commit("first")
        repo.checkout(c1)

        write(repo_path, "a.txt", "2")
        repo.staging("a.txt")
        c2 = repo.commit("detached commit")

        refs = repo.load_json("refs.json")
        assert refs["main"] == c1
        assert repo.head_commit() == c2


class TestResolveRef:
    def test_resolve_ambiguous_prefix_raises(self, repo, repo_path):
        """Invalid: an unrecognisable ref (here, simply nonsense) must raise,
        not silently resolve to the wrong commit."""
        write(repo_path, "a.txt", "1")
        repo.staging("a.txt")
        repo.commit("first")
        with pytest.raises(BranchCommitNotFound):
            repo.ref_resolve("zzzzzzz")        