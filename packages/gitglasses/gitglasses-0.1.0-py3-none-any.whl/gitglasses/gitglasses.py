"""main implementation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generator

import pygit2
from pygit2 import Commit, Oid
from pygit2.repository import Repository


@dataclass
class Cmt:
    commit: Commit
    branch_names: set[str] = field(default_factory=set)
    children: list[Cmt] = field(default_factory=list)
    from_: bool = False
    to: bool = False

    @property
    def commit_message_short(self) -> str:
        return self.commit.message.strip("\n")


def show_branches(current_hash: Oid, end_hash: Oid, repo: Repository) -> None:
    tree = get_tree(current_hash, end_hash, repo)
    parsed = parse_tree(tree)

    print(parsed)


def parse_tree(tree: dict[Oid, Cmt]) -> tuple[str, ...]:
    [no_parent_commit] = (cmt for cmt in tree.values() if cmt.to)

    def traverse_tree(items: list[Cmt]):
        if len(items) == 0:
            return

        *commits, last_commit = items

        first = "│ " * len(commits)

        #  ┬ ─┬ ╮ │ ╰ ─•
        if len(last_commit.children) > 1:
            branch_off = f"├{'─┬' * (len(last_commit.children) - 1)}──"
            branch_draw = "│" * len(commits) + branch_off
        elif len(last_commit.children) == 0:
            branch_draw = "╰─" * len(commits)
        else:
            branch_draw = "├─" * len(items)

        yield (
            first
            + branch_draw
            + f"• {last_commit.commit_message_short}, -- {last_commit.branch_names}"
        )

        new_items = (*commits, *last_commit.children)
        yield from traverse_tree(new_items)

    lines = tuple(traverse_tree([no_parent_commit]))

    return lines


def get_tree(current_hash: Oid, end_hash: Oid, repo: Repository) -> dict[Oid, Cmt]:
    """given a hash of the current head and a hash of the end commit,

    investigate all given commits and those inbetween.
    check if a commit has any branches. Include them in the output.
    """

    all_branches = repo.branches

    def _commits_from_to(_from: Oid, _to: Oid) -> Generator[Commit, None, None]:
        for _commit in repo.walk(_from):
            if _commit.id == _to:
                # yield _commit
                return
            yield _commit

    def relevant_branches(_from: Oid, _to: Oid, branches: dict[str, Oid]):
        for cmt in _commits_from_to(_from, _to):
            for branch in all_branches.with_commit(cmt):
                if branch in branches:
                    continue
                tip_of_branch = all_branches[branch].peel(pygit2.Commit)
                branches[branch] = tip_of_branch.id
                relevant_branches(tip_of_branch.id, cmt.id, branches)

    _rel_branches = {}
    relevant_branches(current_hash, end_hash, _rel_branches)

    def all_relevant_commits() -> Generator[Commit, None, None]:
        for branch, oid in _rel_branches.items():
            for cmt in _commits_from_to(oid, end_hash):
                yield cmt

    _relevant_commits = {
        cmt.id: Cmt(commit=cmt, from_=cmt.id == current_hash)
        for cmt in all_relevant_commits()
    }

    for branch, oid in _rel_branches.items():
        _relevant_commits[oid].branch_names.add(branch)

    # the end commit.
    to_commit = repo.get(end_hash)
    assert isinstance(to_commit, Commit)

    _relevant_commits[to_commit.id] = Cmt(commit=to_commit, to=True)

    def parent_to_children():
        # reverse and sort the tree.
        for commit in _relevant_commits.values():
            if commit.to is True:
                # the end commit. we're not looking further for parents.
                continue
            for parent_id in commit.commit.parent_ids:
                _relevant_commits[parent_id].children.append(commit)

    parent_to_children()

    return _relevant_commits
