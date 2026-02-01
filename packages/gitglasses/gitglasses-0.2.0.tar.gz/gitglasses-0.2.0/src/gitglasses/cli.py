import logging
import sys
from argparse import ArgumentParser
from enum import Enum
from pathlib import Path
from typing import Sequence

import pygit2

from gitglasses.gitglasses import show_branches

_logger = logging.getLogger(__name__)


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


def get_base_branch(from_: pygit2.Oid): ...


def get_from_branch(from_branch: str | None, repo: pygit2.Repository) -> pygit2.Oid:
    if from_branch is None:
        return repo.head.peel(pygit2.Commit).id
    if from_branch in repo.branches:
        cmt = repo.branches[from_branch].peel(pygit2.Commit)
        return cmt.id
    else:
        return repo.revparse_single(from_branch).id


def get_to_branch(
    to_branch: str, repo: pygit2.Repository, from_branch: pygit2.Oid
) -> pygit2.Oid:
    if to_branch in repo.branches:
        _logger.debug(
            "to_branch is a branch name. Finding merge base using the  from_branch"
        )
        to_branch_head = repo.branches[to_branch].peel(pygit2.Commit).id
        return repo.merge_base(from_branch, to_branch_head)
    return repo.revparse_single(to_branch).id


def run(args: Sequence[str] | None = None):
    parser = create_parser()

    arguments = parser.parse_args(args)

    repo = pygit2.Repository(Path.cwd())

    _from: str | None = arguments.source_commit_or_branch
    _from_commit = get_from_branch(_from, repo=repo)

    _to = arguments.target_commit_or_branch
    _to_commit = get_to_branch(_to, repo=repo, from_branch=_from_commit)

    if _from_commit == _to_commit:
        print("From and to are equal branches. Nothing to investigate.")
        sys.exit(1)

    show_branches(_from_commit, _to_commit, repo)


if __name__ == "__main__":
    run()
