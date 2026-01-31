# Arkfast

## Examples

### Temporary paths

```python
from pathlib import Path

from arkfast import TemporaryPath, TemporaryTemplatedPath

with TemporaryPath("data/a/b") as temp_dir:
    (Path(temp_dir) / "output.txt").write_text("hello")

with TemporaryTemplatedPath("template.zip", "workdir") as workdir:
    Path(workdir / "README.md").write_text("updated")
```

### Project metadata

```python
from pathlib import Path

from arkfast import get_project_metadata

name, version = get_project_metadata(Path("."))
print(name, version)
```

### Running a module

```python
from pathlib import Path

from arkfast import run_module

run_module(Path("scripts/smoke_test.py"))
```

## Changelog

### Next

### 0.2.0 | *2026-01-31*
- Add project metadata helper and improve docstrings.
- Simplify TemporaryTemplatedPath logic and refine cleanup semantics.
- Add comprehensive utils tests.
- Add examples to README and docs.

### 0.1.0 | *2025-06-23*
- Add project version getter.

### 0.0.6 | *2025-06-20*
- Move readme to Markdown.

### 0.0.5 | *2025-06-20*
- Add pypi release.
- Fix release numbering.

### 0.0.4 | *2025-06-20*
- Disable drawio plugin.
- Add Templated utilities.

### 0.0.3 | *2022-09-07*
- First actual release on PyPI.

### 0.0.2 | *2022-09-07*
- Remove caption because PyPi complains.

### 0.0.1 | *2022-09-07*
- Create release files.
