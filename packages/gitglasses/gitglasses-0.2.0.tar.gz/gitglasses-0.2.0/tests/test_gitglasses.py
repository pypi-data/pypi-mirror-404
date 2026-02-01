import os
import subprocess
from pathlib import Path

import pygit2
import pytest
from pygit2 import Oid

from gitglasses import gitglasses


def test_repo(
    repo: pygit2.Repository, main_branch: pygit2.Commit, branch_a: pygit2.Commit
):
    result = gitglasses.get_tree(
        current_hash=branch_a.id,
        end_hash=main_branch.id,
        repo=repo,
    )

    [no_parent_commit] = (cmt for cmt in result.values() if cmt.to)

    assert no_parent_commit.commit_message_short == "change to my_file.txt"
    [child_commit] = no_parent_commit.children
    assert child_commit.commit_message_short == "changes in my_file.txt"
    [child_commit] = child_commit.children
    assert child_commit.commit_message_short == "more changes to my_file.txt"
    branch_b, branch_d = child_commit.children

    assert branch_b.commit_message_short == "more changes"
    assert branch_d.commit_message_short == "a commit to branch d"


def test_parse_tree(
    repo: pygit2.Repository, main_branch: pygit2.Commit, branch_a: pygit2.Commit
):
    tree = gitglasses.get_tree(
        current_hash=branch_a.id, end_hash=main_branch.id, repo=repo
    )
    parsed_tree = gitglasses.parse_tree(tree)

    assert parsed_tree == (
        "├─• change to my_file.txt, -- set()",
        "├─• changes in my_file.txt, -- set()",
        "├─┬──• more changes to my_file.txt, -- {'branch-a'}",
        "│ ╰─• a commit to branch d, -- {'branch-d'}",
        "• more changes, -- {'branch-b'}",
    )
