"""
Tests for basic-shit.

Because even basic shit needs tests.
"""

import pytest
from pathlib import Path
import tempfile
import os
from basic_shit import get_project_root, ProjectRootNotFoundError


def test_find_project_root_with_project_root_marker(tmp_path):
    """Test finding project root with .project_root marker."""
    # Create structure:
    # tmp_path/
    #   .project_root
    #   subdir/
    #     subsubdir/
    #       test_file.py

    marker = tmp_path / ".project_root"
    marker.touch()

    subdir = tmp_path / "subdir" / "subsubdir"
    subdir.mkdir(parents=True)

    test_file = subdir / "test_file.py"
    test_file.touch()

    # Should find tmp_path as root
    root = get_project_root(start_path=test_file)
    assert root == tmp_path


def test_find_project_root_with_git_marker(tmp_path):
    """Test finding project root with .git marker."""
    git_dir = tmp_path / ".git"
    git_dir.mkdir()

    subdir = tmp_path / "src" / "module"
    subdir.mkdir(parents=True)

    test_file = subdir / "code.py"
    test_file.touch()

    root = get_project_root(start_path=test_file)
    assert root == tmp_path


def test_find_project_root_with_pyproject_toml(tmp_path):
    """Test finding project root with pyproject.toml."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.touch()

    deep_dir = tmp_path / "a" / "b" / "c" / "d"
    deep_dir.mkdir(parents=True)

    test_file = deep_dir / "deep.py"
    test_file.touch()

    root = get_project_root(start_path=test_file)
    assert root == tmp_path


def test_find_project_root_with_requirements_txt(tmp_path):
    """Test finding project root with requirements.txt."""
    requirements = tmp_path / "requirements.txt"
    requirements.touch()

    subdir = tmp_path / "lib"
    subdir.mkdir()

    test_file = subdir / "module.py"
    test_file.touch()

    root = get_project_root(start_path=test_file)
    assert root == tmp_path


def test_custom_marker_files(tmp_path):
    """Test with custom marker files."""
    custom_marker = tmp_path / ".mymarker"
    custom_marker.touch()

    subdir = tmp_path / "code"
    subdir.mkdir()

    test_file = subdir / "app.py"
    test_file.touch()

    root = get_project_root(
        marker_files=(".mymarker",),
        start_path=test_file
    )
    assert root == tmp_path


def test_multiple_markers_chooses_closest(tmp_path):
    """Test that it finds the closest marker when multiple exist."""
    # Create nested structure with multiple markers
    outer_marker = tmp_path / ".git"
    outer_marker.mkdir()

    inner_dir = tmp_path / "project"
    inner_dir.mkdir()

    inner_marker = inner_dir / ".project_root"
    inner_marker.touch()

    deep_dir = inner_dir / "src"
    deep_dir.mkdir()

    test_file = deep_dir / "code.py"
    test_file.touch()

    # Should find inner_dir (closest marker)
    root = get_project_root(start_path=test_file)
    assert root == inner_dir


def test_no_marker_found_raises_error(tmp_path):
    """Test that exception is raised when no marker is found."""
    subdir = tmp_path / "nowhere"
    subdir.mkdir()

    test_file = subdir / "lost.py"
    test_file.touch()

    with pytest.raises(ProjectRootNotFoundError) as exc_info:
        get_project_root(
            marker_files=(".nonexistent",),
            start_path=test_file
        )

    assert "Could not find project root" in str(exc_info.value)


def test_start_from_directory(tmp_path):
    """Test starting from a directory instead of a file."""
    marker = tmp_path / "pyproject.toml"
    marker.touch()

    subdir = tmp_path / "src" / "package"
    subdir.mkdir(parents=True)

    # Start from directory, not file
    root = get_project_root(start_path=subdir)
    assert root == tmp_path


def test_marker_priority_order(tmp_path):
    """Test that marker files are checked in order."""
    # Create all markers
    (tmp_path / ".project_root").touch()
    (tmp_path / ".git").mkdir()
    (tmp_path / "pyproject.toml").touch()

    subdir = tmp_path / "code"
    subdir.mkdir()

    test_file = subdir / "app.py"
    test_file.touch()

    # Should find .project_root first (it's first in default tuple)
    root = get_project_root(start_path=test_file)
    assert root == tmp_path
    assert (root / ".project_root").exists()


def test_works_with_pathlib_path(tmp_path):
    """Test that it works with pathlib.Path objects."""
    marker = tmp_path


def test_get_project_root_uses_caller_location():
    """Test that get_project_root() finds root from caller's location."""
    # Call WITHOUT start_path - uses inspect magic
    root = get_project_root()

    # Should find the basic-shit project root
    assert root.exists()
    assert root.is_dir()


def test_fallback_to_cwd_when_no_caller_file(monkeypatch, tmp_path):
    """Test fallback to cwd() when caller has no __file__ attribute."""
    import basic_shit

    # Create a marker in tmp_path
    marker = tmp_path / ".project_root"
    marker.touch()

    # Change to that directory
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Mock inspect.currentframe to return frame without __file__
        class MockFrame:
            f_back = type('obj', (object,), {
                'f_globals': {}  # No __file__ key!
            })()

        def mock_currentframe():
            return MockFrame()

        monkeypatch.setattr('inspect.currentframe', mock_currentframe)

        # Now should fallback to cwd()
        root = basic_shit.get_project_root()
        assert root == tmp_path

    finally:
        os.chdir(original_cwd)
