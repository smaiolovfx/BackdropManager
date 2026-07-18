"""Helpers for running commands in the active Nuke node graph."""

import nuke

from .qt import QtWidgets

DAG_TITLE = "Node Graph"
DAG_OBJECT_NAME = "DAG"


def get_dag_widgets(visible=True):
    """Return DAG Qt widgets."""
    dags = []
    app = QtWidgets.QApplication.instance()
    if app is None:
        return dags

    for widget in app.allWidgets():
        if DAG_OBJECT_NAME in widget.objectName():
            if not visible or widget.isVisible():
                dags.append(widget)
    return dags


def get_current_dag():
    """Return the currently active DAG."""
    visible_dags = get_dag_widgets(visible=True)
    for dag in visible_dags:
        if dag.hasFocus():
            return dag

    if visible_dags:
        return visible_dags[0]
    return None


def get_dag_node(dag_widget):
    """Return the Nuke node that owns a DAG widget."""
    title = str(dag_widget.windowTitle())
    if DAG_TITLE not in title:
        return None
    if dag_widget.objectName() == DAG_OBJECT_NAME:
        return nuke.root()
    return nuke.toNode(title.replace(" " + DAG_TITLE, ""))


def active_dag_node():
    """Return the Nuke node for the active DAG, or root if unknown."""
    active_dag = get_current_dag()
    if not active_dag:
        return nuke.root()
    return get_dag_node(active_dag) or nuke.root()


def wrapped(func):
    """Execute a function in the currently active DAG context."""

    def wrapper(*args, **kwargs):
        with active_dag_node():
            return func(*args, **kwargs)

    return wrapper
