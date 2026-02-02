"""GitHub command unit tests."""

from __future__ import annotations

from click.testing import CliRunner

import sagellm_dev_tools.commands.gh as gh_cmd
from sagellm_dev_tools.github_cli import IssueInfo


def test_extract_priority_from_title_and_labels() -> None:
    assert gh_cmd._extract_priority("[P0] urgent", []) == 0
    assert gh_cmd._extract_priority("Fix", ["P2"]) == 2
    assert gh_cmd._extract_priority("Fix", ["priority/P1"]) == 1
    assert gh_cmd._extract_priority("Fix", []) == 99


def test_gh_list_flat_table(monkeypatch) -> None:
    runner = CliRunner()

    monkeypatch.setattr(gh_cmd, "SAGELLM_REPOS", ["repo-a"])

    class DummyGitHubCLI:
        def list_issues(self, repo: str, state: str = "open", limit: int = 200):
            return [
                IssueInfo(
                    number=1,
                    title="[P1] Sample issue",
                    state="open",
                    assignees=["alice"],
                    labels=["P1"],
                    body="details",
                )
            ]

        def get_current_user_login(self):
            return "alice"

    monkeypatch.setattr(gh_cmd, "GitHubCLI", DummyGitHubCLI)

    result = runner.invoke(gh_cmd.gh, ["list", "repo-a"])

    assert result.exit_code == 0
    assert "Sample issue" in result.output
    assert "repo-a" in result.output
    assert "P1" in result.output
