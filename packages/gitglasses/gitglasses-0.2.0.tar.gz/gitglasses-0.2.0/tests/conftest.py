import os
import subprocess
from pathlib import Path

import pygit2
import pytest

from gitglasses import gitglasses


@pytest.fixture
def git_simple_branches(tmp_path) -> Path:
    # * main
    # |
    # * changes in my_file.txt
    # |
    # * more changes to my_file.txt  [branch A]
    # |\
    # | * a commit to branch d [branch D]
    # |
    # * more changes [branch B]

    script = """

    git init

    touch my_file.txt
    git add .
    git commit -m 'commit on main'
    echo 'change on main' >> my_file.txt
    git add .
    git commit -m 'change to my_file.txt'

    git checkout -b branch-a
    echo 'change_a' >> my_file.txt
    git add .
    git commit -m 'changes in my_file.txt'

    echo 'change_ab' >> my_file.txt
    git add .
    git commit -m 'more changes to my_file.txt'


    git checkout -b branch-b
    echo 'change_b' >> my_file.txt
    git add .
    git commit -m 'more changes'

    git checkout main
    git checkout -b branch-c
    touch other_file.txt
    git add .
    git commit -m 'add branch c'

    git checkout branch-a
    git checkout -b branch-d
    touch file_d.txt
    echo 'change_to_d' >> file_d.txt
    git add .
    git commit -m 'a commit to branch d'


    git checkout branch-a
    """

    result = subprocess.run(
        ["bash", "-c", script], check=True, capture_output=True, text=True, cwd=tmp_path
    )
    print(result.stdout)

    return tmp_path


@pytest.fixture
def repo(git_simple_branches) -> pygit2.Repository:
    repo = pygit2.Repository(git_simple_branches)
    return repo


@pytest.fixture
def main_branch(repo, git_simple_branches) -> pygit2.Commit:
    main_commit = repo.references["refs/heads/main"].peel(pygit2.Commit)
    return main_commit


@pytest.fixture
def branch_a(repo):
    branch = repo.references["refs/heads/branch-a"].peel(pygit2.Commit)
    return branch
