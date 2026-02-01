from pathlib import Path

from gitglasses.cli import run


def test_cli_defaults(monkeypatch, git_simple_branches, main_branch, branch_a):
    monkeypatch.chdir(git_simple_branches)
    res = run([])


def test_cli_by_branch_names(monkeypatch, git_simple_branches):
    monkeypatch.chdir(git_simple_branches)
    res = run(["--from", "branch-a", "--to", "main"])


def test_cli_by_branch_names_2(monkeypatch, git_simple_branches):
    monkeypatch.chdir(git_simple_branches)
    res = run(["--from", "branch-c", "--to", "main"])
