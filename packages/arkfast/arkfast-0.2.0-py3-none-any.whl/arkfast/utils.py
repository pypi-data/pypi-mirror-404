import os
import runpy
import tomllib
import zipfile
import shutil
from pathlib import Path
from typing import TypeVar

PathLikeT = TypeVar("PathLikeT", Path, str)


class TemporaryTemplatedPath:
    """Context manager that materializes a path from a template and cleans up created paths."""

    def __init__(self, template_file_path: PathLikeT | None, extraction_path: PathLikeT,
                 remove_after_completion: bool = True):
        self.template_file_path = Path(template_file_path) if isinstance(template_file_path,
                                                                         str) else template_file_path
        self.extraction_path = extraction_path if isinstance(extraction_path, Path) else Path(extraction_path)
        self.remove_after_completion = remove_after_completion
        self._preexisting_paths: set[Path] = set()
        self._root_existed = False
        self._preexisting_file = False
        self._keep_until: Path | None = None

    def __enter__(self):
        self._root_existed = self.extraction_path.exists()
        self._preexisting_file = self._root_existed and self.extraction_path.is_file()
        if self._root_existed and self.extraction_path.is_dir():
            self._preexisting_paths = self._snapshot_tree(self.extraction_path)

        self._keep_until = self._find_existing_parent(self.extraction_path)
        self._materialize()
        return self.extraction_path

    def __exit__(self, exc_type, exc_value, traceback):
        if not self.remove_after_completion:
            return
        try:
            if not self._root_existed:
                self._remove_root()
                self._cleanup_parents()
                return
            if self._preexisting_file:
                return
            if self.extraction_path.is_dir():
                self._remove_new_entries()
        except FileNotFoundError:
            pass

    def _materialize(self) -> None:
        """Create the extraction path from the template path (if any)."""
        if not self.template_file_path:
            self._ensure_path()
            return
        if self.template_file_path.suffix == ".zip":
            with zipfile.ZipFile(self.template_file_path) as zip_file:
                zip_file.extractall(self.extraction_path)
            return
        if self.template_file_path.is_dir():
            shutil.copytree(self.template_file_path, self.extraction_path)
            return
        if self.template_file_path.is_file():
            self.extraction_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )  # This will cause the made directories to be left after cleanup.
            shutil.copyfile(self.template_file_path, self.extraction_path)
            return
        raise ValueError(f"Unexpected extension ({self.template_file_path.suffix}).")

    def _ensure_path(self) -> None:
        """Ensure the extraction path exists, creating a file or directory as needed."""
        if self.extraction_path.exists():
            return
        if self.extraction_path.suffix:
            self.extraction_path.parent.mkdir(parents=True, exist_ok=True)
            self.extraction_path.touch()
        else:
            self.extraction_path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _snapshot_tree(root: Path) -> set[Path]:
        """Return the set of existing relative paths under the root directory."""
        paths: set[Path] = set()
        for dir_root, dirs, files in os.walk(root):
            root_path = Path(dir_root)
            rel_root = root_path.relative_to(root)
            paths.add(rel_root)
            for name in dirs:
                paths.add(rel_root / name)
            for name in files:
                paths.add(rel_root / name)
        return paths

    @staticmethod
    def _find_existing_parent(path: Path) -> Path | None:
        """Return the nearest existing parent directory for a path."""
        current = path
        while True:
            parent = current.parent
            if parent == current:
                return None
            if parent.exists():
                return parent
            current = parent

    def _remove_root(self) -> None:
        """Remove the extraction path if it was created during this context."""
        if self.extraction_path.is_dir():
            shutil.rmtree(self.extraction_path)
        elif self.extraction_path.is_file():
            os.remove(self.extraction_path)

    def _cleanup_parents(self) -> None:
        """Remove created parent directories up to the first preexisting parent."""
        parent = self.extraction_path.parent
        while self._keep_until and parent != self._keep_until:
            if not parent.exists():
                parent = parent.parent
                continue
            try:
                parent.rmdir()
            except OSError:
                break
            parent = parent.parent

    def _remove_new_entries(self) -> None:
        """Remove entries created during this context under an existing root."""
        paths = sorted(
            self.extraction_path.rglob("*"),
            key=lambda path: len(path.parts),
            reverse=True,
        )
        for path in paths:
            rel_path = path.relative_to(self.extraction_path)
            if rel_path in self._preexisting_paths:
                continue
            if path.is_dir():
                path.rmdir()
            else:
                path.unlink()


class TemporaryPath(TemporaryTemplatedPath):
    """Temporary path that cleans up only what it created, preserving preexisting content."""

    def __init__(self, path: PathLikeT, remove_after_completion: bool = True):
        super().__init__(None, path if isinstance(path, Path) else Path(path), remove_after_completion)


def run_module(path_to_script: Path):
    """Run a Python script by its path, temporarily switching the working directory."""
    original_cwd = Path.cwd()
    try:
        os.chdir(path_to_script)
        runpy.run_path(str(path_to_script))
    finally:
        os.chdir(original_cwd)


def get_project_metadata(root_project_directory: Path) -> tuple[str, str]:
    """Return (name, version) from pyproject.toml, defaulting to "unknown"."""
    try:
        data = tomllib.loads((root_project_directory / "pyproject.toml").read_text())
    except FileNotFoundError:
        data = {}
    project = data.get("project", {})
    return project.get("name", "unknown"), project.get("version", "unknown")
