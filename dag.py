"""Helpers for running commands in the active Nuke node graph."""

from contextlib import contextmanager

import nuke

from .qt import QtWidgets

DAG_TITLE = "Node Graph"
DAG_OBJECT_NAME = "DAG"

# Last non-root DAG we resolved. Used after panel/dialog steals focus.
_last_dag = None


def get_dag_widgets(visible=True):
    """Return DAG Qt widgets."""
    app = QtWidgets.QApplication.instance()
    if app is None:
        return []
    dags = []
    for widget in app.allWidgets():
        if DAG_OBJECT_NAME in widget.objectName():
            if not visible or widget.isVisible():
                dags.append(widget)
    return dags


def get_current_dag():
    """Return the focused DAG widget (or a DAG that owns the focus widget)."""
    visible_dags = get_dag_widgets(visible=True)
    for dag in visible_dags:
        if dag.hasFocus():
            return dag

    app = QtWidgets.QApplication.instance()
    focus = app.focusWidget() if app is not None else None
    while focus is not None:
        for dag in visible_dags:
            if focus is dag or dag.isAncestorOf(focus):
                return dag
        focus = focus.parentWidget()
    return None


def this_group():
    try:
        return nuke.thisGroup()
    except Exception:
        return nuke.root()


def _alive(node):
    if node is None:
        return False
    try:
        node.name()
        return True
    except Exception:
        return False


def remember_dag(node):
    """Remember a DAG for later actions. Never remember root over a group."""
    global _last_dag
    if not _alive(node):
        return
    if node == nuke.root() and _alive(_last_dag) and _last_dag != nuke.root():
        return
    _last_dag = node


def get_dag_node(dag_widget):
    """Return the Nuke group for a DAG widget."""
    title = str(dag_widget.windowTitle()).strip()
    if DAG_TITLE not in title:
        return None
    # Main pane title stays "Node Graph" inside a Group — trust Nuke.
    if title == DAG_TITLE:
        return this_group()
    name = title.replace(" " + DAG_TITLE, "").strip().replace("/", ".")
    if not name:
        return this_group()
    return nuke.toNode(name)


def current_dag():
    """Return the Nuke group for the DAG the user is working in.

    Order:
      1. nuke.thisGroup() when entered into a Group (incl. nested)
      2. Focused floating DAG widget (title → node)
      3. Last remembered non-root DAG
      4. root
    """
    # Entered groups (any depth): thisGroup is authoritative.
    group = this_group()
    if group != nuke.root():
        remember_dag(group)
        return group

    widget = get_current_dag()
    if widget is not None:
        node = get_dag_node(widget)
        if _alive(node):
            if node == nuke.root():
                # Focused main DAG at root — drop sticky nested memory.
                global _last_dag
                _last_dag = None
                return node
            remember_dag(node)
            return node

    if _alive(_last_dag):
        return _last_dag

    return group


@contextmanager
def in_dag(node=None):
    """Run under a DAG group without kicking the user back to root.

    Nuke's group.end() / exiting ``with group`` always jumps to root and
    drops in-group selection — that made edit/recolor fail after create.
    We begin() when needed and do not end().
    """
    target = current_dag() if node is None else node
    if not _alive(target):
        target = current_dag()
    remember_dag(target)
    if target != this_group():
        target.begin()
    yield target


def wrapped(func):
    """Execute a function in the currently active DAG context."""

    def wrapper(*args, **kwargs):
        with in_dag():
            return func(*args, **kwargs)

    return wrapper
