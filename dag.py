"""Helpers for running commands in the Node Graph the user is working in."""

from contextlib import contextmanager

import nuke


def _alive(node):
    if node is None:
        return False
    try:
        node.name()
        return True
    except Exception:
        return False


def current_dag():
    """Group of the Node Graph the user last clicked in (root if none).

    lastHitGroup() follows main-graph Group entry and floating Group tabs, and
    is not changed by clicking the panel or a dialog. nukescripts uses it too.
    """
    group = nuke.lastHitGroup()
    return group if _alive(group) else nuke.root()


@contextmanager
def in_dag(node=None):
    """Run under a group, then restore the previous group context.

    begin()/end() nest like a stack, but an unpaired end() jumps to root, so
    we only end() after our own begin(). Leaving it begun would leave Nuke's
    context on the group, which is unsafe once undo deletes that group.
    """
    target = node if _alive(node) else current_dag()
    if target == nuke.thisGroup():
        yield target
        return
    target.begin()
    try:
        yield target
    finally:
        # The group may have been deleted inside the block (e.g. by undo).
        if _alive(target):
            target.end()


def wrapped(func):
    """Execute a function in the currently active DAG context."""

    def wrapper(*args, **kwargs):
        with in_dag():
            return func(*args, **kwargs)

    return wrapper
