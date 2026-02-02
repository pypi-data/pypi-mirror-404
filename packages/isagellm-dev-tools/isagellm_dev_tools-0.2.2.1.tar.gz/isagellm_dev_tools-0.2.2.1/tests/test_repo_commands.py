"""Repository command unit tests."""

from __future__ import annotations

from click.testing import CliRunner

import sagellm_dev_tools.commands.repo as repo_cmd


def test_init_reports_success_and_skip(monkeypatch) -> None:
    runner = CliRunner()

    monkeypatch.setattr(repo_cmd, "SAGELLM_REPOS", ["repo-a", "repo-b"])

    def fake_clone(repo: str, parent_dir: str, use_ssh: bool = True) -> bool:
        return repo == "repo-a"

    monkeypatch.setattr(repo_cmd, "clone_repository", fake_clone)

    result = runner.invoke(repo_cmd.init, ["--parent-dir", "/tmp", "--https"])

    assert result.exit_code == 0
    assert "Cloned: 1" in result.output
    assert "Skipped: 1" in result.output


def test_push_check_skips_dirty_repo(monkeypatch) -> None:
    runner = CliRunner()

    monkeypatch.setattr(repo_cmd, "SAGELLM_REPOS", ["repo-a"])

    def fake_status(repo: str, parent_dir: str) -> dict:
        return {"exists": True, "is_repo": True, "dirty": True}

    def fake_push(repo: str, parent_dir: str) -> dict:
        raise AssertionError("push_repository should not be called for dirty repo")

    monkeypatch.setattr(repo_cmd, "get_repo_status", fake_status)
    monkeypatch.setattr(repo_cmd, "push_repository", fake_push)

    result = runner.invoke(repo_cmd.push, ["--parent-dir", "/tmp", "--check"])

    assert result.exit_code == 0
    assert "uncommitted changes" in result.output


def test_status_outputs_repo_state(monkeypatch) -> None:
    runner = CliRunner()

    monkeypatch.setattr(repo_cmd, "SAGELLM_REPOS", ["repo-a"])

    def fake_status(repo: str, parent_dir: str) -> dict:
        return {
            "exists": True,
            "is_repo": True,
            "branch": "main",
            "dirty": False,
            "ahead": 1,
            "behind": 0,
        }

    monkeypatch.setattr(repo_cmd, "get_repo_status", fake_status)

    result = runner.invoke(repo_cmd.status, ["--parent-dir", "/tmp"])

    assert result.exit_code == 0
    assert "repo-a" in result.output
    assert "main" in result.output
    assert "↑1" in result.output
