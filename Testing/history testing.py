from MiniControlSystem import history
from .conftest import write

class TestHistory:
    def test_format_history_empty(self, repo):
        """Boundary: formatting an empty history returns a friendly message,
        not an empty string or a crash."""
        commits = history.get_history(repo)
        assert history.format_history(commits) == "No commits yet"

    def test_get_history_matches_repo_log(self, repo, repo_path):
        """Normal: history.get_history() delegates correctly to Repository.log()."""
        write(repo_path, "a.txt", "1")
        repo.staging("a.txt")
        repo.commit("first")

        commits = history.get_history(repo)
        assert len(commits) == 1
        assert commits[0]["message"] == "first"

    def test_format_history_includes_short_hash_and_message(self, repo, repo_path):
        """Normal: formatted output is human-readable and includes key fields."""
        write(repo_path, "a.txt", "1")
        repo.staging("a.txt")
        commit_hash = repo.commit("readable commit")

        commits = history.get_history(repo)
        formatted = history.format_history(commits)
        assert commit_hash[:7] in formatted
        assert "readable commit" in formatted