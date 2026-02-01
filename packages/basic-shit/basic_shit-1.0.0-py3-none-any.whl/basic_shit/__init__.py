"""
basic-shit: Finding your project root in Python. You know, basic shit.

Because apparently in 2026, Python still can't do this out of the box.
"""

from pathlib import Path
from typing import Optional, Tuple

__version__ = "1.0.0"
__all__ = ["get_project_root", "ProjectRootNotFoundError"]


class ProjectRootNotFoundError(Exception):
    """Raised when project root cannot be found."""
    pass


def get_project_root(
        marker_files: Tuple[str, ...] = (".project_root", ".git", "pyproject.toml", "requirements.txt", "setup.py"),
        start_path: Optional[Path] = None
) -> Path:
    """
    Find the project root by looking for marker files.

    Args:
        marker_files: Tuple of filenames to search for (default: common project markers)
        start_path: Path to start searching from (default: location of calling file)

    Returns:
        Path object pointing to project root

    Raises:
        ProjectRootNotFoundError: If no marker file is found in any parent directory

    Example:
        >>> from basic_shit import get_project_root
        >>> root = get_project_root()
        >>> data_dir = root / "data"
    """
    if start_path is None:
        # Get the caller's file location
        import inspect
        frame = inspect.currentframe()
        caller_frame = frame.f_back
        caller_file = caller_frame.f_globals.get("__file__")
        if caller_file:
            start_path = Path(caller_file).resolve()
        else:
            start_path = Path.cwd()

    current = start_path if start_path.is_dir() else start_path.parent

    # Walk up the directory tree
    for parent in [current, *current.parents]:
        for marker in marker_files:
            if (parent / marker).exists():
                return parent

    raise ProjectRootNotFoundError(
        f"Could not find project root. Searched for markers: {marker_files}"
    )
