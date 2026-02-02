pytest_plugins = "pytester"


def _run(pytester):
    return pytester.runpytest_subprocess("-W", "error")


def test_single_conftest_mark_applied(pytester):
    pytester.makeini("""[pytest]
markers =
    foo: applied from conftest
""")

    pytester.makeconftest("""
import pytest
pytestmark = pytest.mark.foo
""")

    pytester.makepyfile(test_sample="""
import pytest
def test_mark_applied(request):
    assert request.node.get_closest_marker("foo")
""")

    result = _run(pytester)
    result.assert_outcomes(passed=1)


def test_list_and_tuple_marks_from_parent_and_child(pytester):
    pytester.makeini("""[pytest]
markers =
    rootmark: applied from root conftest
    submark: applied from subdir conftest
""")

    pytester.makeconftest("""
import pytest

pytestmark = [pytest.mark.rootmark]
""")

    subdir = pytester.mkdir("subdir")
    subdir.joinpath("conftest.py").write_text("""
import pytest
pytestmark = (pytest.mark.submark,)
""", encoding="utf-8")

    subdir.joinpath("test_in_subdir.py").write_text("""
import pytest
def test_marks_apply(request):
    assert request.node.get_closest_marker("rootmark")
    assert request.node.get_closest_marker("submark")
""", encoding="utf-8")

    result = _run(pytester)
    result.assert_outcomes(passed=1)


def test_no_conftest_mark_does_not_add_marker(pytester):
    pytester.makeini("""[pytest]
markers =
    foo: unused
""")
    pytester.makeconftest("""
# no pytestmark defined here
""")
    pytester.makepyfile(test_sample="""
import pytest
def test_no_mark(request):
    assert request.node.get_closest_marker("foo") is None
""")

    result = _run(pytester)
    result.assert_outcomes(passed=1)
