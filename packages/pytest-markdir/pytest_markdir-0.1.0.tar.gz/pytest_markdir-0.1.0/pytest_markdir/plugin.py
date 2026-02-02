from pathlib import Path


def pytest_collection_modifyitems(session, config, items):
    for item in items:
        for conftest in _iter_conftests(item):
            for mark in _get_conftest_marks(conftest):
                item.add_marker(mark)


def _get_conftest_marks(conftest):
    if marks := getattr(conftest, "pytestmark", None):
        if not isinstance(marks, (list, tuple)):
            marks = [marks]
        return marks
    return []


def _iter_conftests(item):
    manager = item.config.pluginmanager
    return manager._getconftestmodules(Path(item.fspath))
