# pytest-markdir

Apply `pytestmark` declared in any `conftest.py` to all collected tests under that directory tree.

This is helpful when you want directory-wide markers (e.g., `slow`, `integration`, `db`) without repeating decorators in every test file.

## Install

```bash
pip install pytest-markdir
```

## Usage

Define `pytestmark` in a `conftest.py` anywhere in your test tree. The plugin will add those marks to every collected test in that directory and its subdirectories.

### Single mark

```py
# conftest.py
import pytest
pytestmark = pytest.mark.slow
```

```py
# test_sample.py
def test_example(request):
    assert request.node.get_closest_marker("slow")
```

Run:

```bash
pytest -m slow
```

### Multiple marks (list/tuple)

```py
# conftest.py (root)
import pytest
pytestmark = [pytest.mark.integration, pytest.mark.db]
```

```py
# subdir/conftest.py
import pytest
pytestmark = (pytest.mark.subdir_only,)
```

```py
# subdir/test_in_subdir.py
def test_marks(request):
    assert request.node.get_closest_marker("integration")
    assert request.node.get_closest_marker("db")
    assert request.node.get_closest_marker("subdir_only")
```

### Register markers (recommended)

```ini
# pytest.ini
[pytest]
markers =
    slow: long running tests
    integration: uses external services
    db: touches the database
    subdir_only: applies only under subdir/
```

## How it works

During collection, the plugin finds every `conftest.py` that applies to a test item and copies its `pytestmark` onto the test item.

## Compatibility

- Python: 3.10+
- pytest: 8.x–9.x

## License

MIT. See `LICENSE`.
