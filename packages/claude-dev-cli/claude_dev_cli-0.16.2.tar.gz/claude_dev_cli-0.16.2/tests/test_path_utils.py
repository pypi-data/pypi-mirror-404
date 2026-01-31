"""Tests for path_utils module."""

import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from claude_dev_cli.path_utils import (
    is_code_file,
    expand_paths,
    get_git_changes,
    auto_detect_files,
    CODE_EXTENSIONS
)


class TestIsCodeFile:
    """Tests for is_code_file function."""
    
    def test_python_file(self) -> None:
        """Test Python files are recognized."""
        assert is_code_file(Path("test.py"))
        assert is_code_file(Path("/path/to/module.py"))
    
    def test_javascript_files(self) -> None:
        """Test JavaScript/TypeScript files are recognized."""
        assert is_code_file(Path("app.js"))
        assert is_code_file(Path("component.jsx"))
        assert is_code_file(Path("module.ts"))
        assert is_code_file(Path("component.tsx"))
    
    def test_various_code_files(self) -> None:
        """Test various code file types."""
        assert is_code_file(Path("main.go"))
        assert is_code_file(Path("lib.rs"))
        assert is_code_file(Path("App.java"))
        assert is_code_file(Path("script.sh"))
    
    def test_non_code_files(self) -> None:
        """Test non-code files are not recognized."""
        assert not is_code_file(Path("image.png"))
        assert not is_code_file(Path("document.pdf"))
        assert not is_code_file(Path("data.json"))
        assert not is_code_file(Path("README.md"))
    
    def test_case_insensitive(self) -> None:
        """Test file extension matching is case-insensitive."""
        assert is_code_file(Path("TEST.PY"))
        assert is_code_file(Path("App.JS"))


class TestExpandPaths:
    """Tests for expand_paths function."""
    
    def test_single_file(self, tmp_path: Path) -> None:
        """Test expanding a single file."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')")
        
        result = expand_paths([str(test_file)])
        assert len(result) == 1
        assert result[0] == test_file
    
    def test_multiple_files(self, tmp_path: Path) -> None:
        """Test expanding multiple files."""
        file1 = tmp_path / "file1.py"
        file2 = tmp_path / "file2.js"
        file1.write_text("# file1")
        file2.write_text("// file2")
        
        result = expand_paths([str(file1), str(file2)])
        assert len(result) == 2
        assert file1 in result
        assert file2 in result
    
    def test_directory_recursive(self, tmp_path: Path) -> None:
        """Test expanding directory recursively."""
        # Create directory structure
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "module1.py").write_text("# module1")
        (tmp_path / "src" / "subdir").mkdir()
        (tmp_path / "src" / "subdir" / "module2.py").write_text("# module2")
        (tmp_path / "src" / "README.md").write_text("# docs")  # Non-code file
        
        result = expand_paths([str(tmp_path / "src")], recursive=True)
        
        # Should include both Python files but not README
        assert len(result) == 2
        assert (tmp_path / "src" / "module1.py") in result
        assert (tmp_path / "src" / "subdir" / "module2.py") in result
    
    def test_directory_non_recursive(self, tmp_path: Path) -> None:
        """Test expanding directory non-recursively."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "module1.py").write_text("# module1")
        (tmp_path / "src" / "subdir").mkdir()
        (tmp_path / "src" / "subdir" / "module2.py").write_text("# module2")
        
        result = expand_paths([str(tmp_path / "src")], recursive=False)
        
        # Should only include module1, not module2 in subdir
        assert len(result) == 1
        assert (tmp_path / "src" / "module1.py") in result
    
    def test_max_files_limit(self, tmp_path: Path) -> None:
        """Test max_files limit."""
        (tmp_path / "src").mkdir()
        for i in range(10):
            (tmp_path / "src" / f"file{i}.py").write_text(f"# file{i}")
        
        result = expand_paths([str(tmp_path / "src")], max_files=5)
        assert len(result) == 5
    
    def test_nonexistent_path(self) -> None:
        """Test handling nonexistent paths."""
        result = expand_paths(["/nonexistent/path.py"])
        assert len(result) == 0
    
    def test_mixed_paths(self, tmp_path: Path) -> None:
        """Test expanding mixed files and directories."""
        file1 = tmp_path / "file1.py"
        file1.write_text("# file1")
        
        (tmp_path / "dir").mkdir()
        (tmp_path / "dir" / "file2.py").write_text("# file2")
        
        result = expand_paths([str(file1), str(tmp_path / "dir")])
        assert len(result) == 2


class TestGetGitChanges:
    """Tests for get_git_changes function."""
    
    @patch('subprocess.run')
    def test_staged_only(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test getting only staged files."""
        # Create test files
        (tmp_path / "file1.py").write_text("# file1")
        (tmp_path / "file2.py").write_text("# file2")
        
        # Mock git diff output
        mock_run.return_value = MagicMock(
            stdout=f"{tmp_path / 'file1.py'}\n{tmp_path / 'file2.py'}",
            returncode=0
        )
        
        result = get_git_changes(staged_only=True)
        
        # Verify git command was called correctly
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args == ['git', 'diff', '--cached', '--name-only']
    
    @patch('subprocess.run')
    def test_all_changes(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test getting all modified files."""
        (tmp_path / "file1.py").write_text("# file1")
        
        mock_run.return_value = MagicMock(
            stdout=f"{tmp_path / 'file1.py'}",
            returncode=0
        )
        
        result = get_git_changes(staged_only=False, include_untracked=False)
        
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args == ['git', 'diff', '--name-only', 'HEAD']
    
    @patch('subprocess.run')
    def test_commit_range(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test getting files in commit range."""
        (tmp_path / "file1.py").write_text("# file1")
        
        mock_run.return_value = MagicMock(
            stdout=f"{tmp_path / 'file1.py'}",
            returncode=0
        )
        
        result = get_git_changes(commit_range="main..HEAD")
        
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args == ['git', 'diff', '--name-only', 'main..HEAD']
    
    @patch('subprocess.run')
    def test_include_untracked(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test including untracked files."""
        (tmp_path / "file1.py").write_text("# file1")
        (tmp_path / "file2.py").write_text("# file2")
        
        # First call for modified files, second for untracked
        mock_run.side_effect = [
            MagicMock(stdout=f"{tmp_path / 'file1.py'}", returncode=0),
            MagicMock(stdout=f"{tmp_path / 'file2.py'}", returncode=0)
        ]
        
        result = get_git_changes(staged_only=False, include_untracked=True)
        
        assert mock_run.call_count == 2
    
    @patch('subprocess.run')
    def test_git_error(self, mock_run: MagicMock) -> None:
        """Test handling git command errors."""
        mock_run.side_effect = subprocess.CalledProcessError(1, 'git')
        
        result = get_git_changes()
        assert result == []
    
    @patch('subprocess.run')
    def test_empty_output(self, mock_run: MagicMock) -> None:
        """Test handling empty git output."""
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        
        result = get_git_changes()
        assert result == []
    
    @patch('subprocess.run')
    def test_filters_nonexistent_files(self, mock_run: MagicMock) -> None:
        """Test that nonexistent files are filtered out."""
        mock_run.return_value = MagicMock(
            stdout="/nonexistent/file.py\n/another/missing.py",
            returncode=0
        )
        
        result = get_git_changes()
        # Files don't exist, so should be empty
        assert result == []


class TestAutoDetectFiles:
    """Tests for auto_detect_files function."""
    
    @patch('claude_dev_cli.path_utils.get_git_changes')
    def test_uses_staged_first(self, mock_git: MagicMock) -> None:
        """Test that staged files are checked first."""
        mock_git.return_value = [Path("file1.py"), Path("file2.py")]
        
        result = auto_detect_files()
        
        # Should call with staged_only=True first
        mock_git.assert_called_with(staged_only=True)
        assert len(result) == 2
    
    @patch('claude_dev_cli.path_utils.get_git_changes')
    def test_falls_back_to_modified(self, mock_git: MagicMock) -> None:
        """Test fallback to all modified files."""
        # First call (staged) returns empty, second call (all changes) returns files
        mock_git.side_effect = [
            [],  # No staged files
            [Path("file1.py")]  # Modified files
        ]
        
        result = auto_detect_files()
        
        assert mock_git.call_count == 2
        assert len(result) == 1
    
    @patch('claude_dev_cli.path_utils.get_git_changes')
    @patch('claude_dev_cli.path_utils.expand_paths')
    def test_falls_back_to_current_dir(
        self,
        mock_expand: MagicMock,
        mock_git: MagicMock,
        tmp_path: Path
    ) -> None:
        """Test fallback to current directory."""
        # Both git calls return empty
        mock_git.return_value = []
        mock_expand.return_value = [Path("file.py")]
        
        result = auto_detect_files(cwd=tmp_path)
        
        # Should call expand_paths with current directory
        mock_expand.assert_called_once()
        call_args = mock_expand.call_args[0][0]
        assert str(tmp_path) in call_args


class TestCodeExtensions:
    """Tests for CODE_EXTENSIONS constant."""
    
    def test_common_languages_included(self) -> None:
        """Test that common language extensions are included."""
        assert '.py' in CODE_EXTENSIONS
        assert '.js' in CODE_EXTENSIONS
        assert '.ts' in CODE_EXTENSIONS
        assert '.go' in CODE_EXTENSIONS
        assert '.rs' in CODE_EXTENSIONS
        assert '.java' in CODE_EXTENSIONS
    
    def test_all_lowercase(self) -> None:
        """Test that all extensions are lowercase."""
        assert all(ext.islower() for ext in CODE_EXTENSIONS)
    
    def test_all_start_with_dot(self) -> None:
        """Test that all extensions start with a dot."""
        assert all(ext.startswith('.') for ext in CODE_EXTENSIONS)
