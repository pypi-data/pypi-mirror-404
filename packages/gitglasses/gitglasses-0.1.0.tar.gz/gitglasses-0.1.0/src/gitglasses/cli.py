import sys
from argparse import ArgumentParser
from enum import Enum
from pathlib import Path
from typing import Sequence

import pygit2

from gitglasses.gitglasses import show_branches


class Branches(Enum):
    CURRENT = "CURRENT"
    MAIN = "MAIN"


def create_parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument(
        "--from",
        dest="source_commit_or_branch",
        default=None,
        help="the commit hash to start looking from.",
    )
    parser.add_argument(
        "--to",
        dest="target_commit_or_branch",
        default="main",
        help="the branch name or hash to look until. [exclusive]",
    )
    return parser


def get_commit_oid(
    branchname_or_hash: str | None, repo: pygit2.Repository
) -> pygit2.Oid:
    all_branches = repo.branches
    if branchname_or_hash is None:
        return repo.head.peel(pygit2.Commit).id

    if branchname_or_hash in all_branches:
        branch = all_branches[branchname_or_hash]
        cmt = branch.peel(pygit2.Commit)
        return branch.peel(pygit2.Commit).id

    cmt = repo.revparse_single(branchname_or_hash)
    return cmt.id


def run(args: Sequence[str] | None = None):
    parser = create_parser()

    arguments = parser.parse_args(args)

    repo = pygit2.Repository(Path.cwd())

    _from: str | None = arguments.source_commit_or_branch
    _from_commit = get_commit_oid(_from, repo=repo)

    _to = arguments.target_commit_or_branch
    _to_commit = get_commit_oid(_to, repo=repo)

    if _from_commit == _to_commit:
        print("From and to are equal branches. Nothing to investigate.")
        sys.exit(1)

    show_branches(_from_commit, _to_commit, repo)


if __name__ == "__main__":
    run()
