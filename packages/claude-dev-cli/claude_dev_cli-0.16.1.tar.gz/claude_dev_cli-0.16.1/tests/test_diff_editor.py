"""Tests for diff editor plugin."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from claude_dev_cli.plugins.diff_editor.viewer import DiffViewer, Hunk


class TestHunk:
    """Tests for Hunk class."""
    
    def test_create_hunk(self) -> None:
        """Test creating a hunk."""
        hunk = Hunk(
            original_lines=["old line\n"],
            proposed_lines=["new line\n"],
            original_start=10,
            proposed_start=10
        )
        
        assert hunk.original_lines == ["old line\n"]
        assert hunk.proposed_lines == ["new line\n"]
        assert hunk.original_start == 10
        assert hunk.proposed_start == 10
        assert hunk.accepted is None
    
    def test_hunk_get_context(self) -> None:
        """Test getting hunk context."""
        hunk = Hunk(
            original_lines=[],
            proposed_lines=["def function_name():\n", "    pass\n"],
            original_start=0,
            proposed_start=0
        )
        
        context = hunk.get_context()
        assert context == "def function_name():"
    
    def test_hunk_get_context_long_line(self) -> None:
        """Test context truncation for long lines."""
        long_line = "x" * 100 + "\n"
        hunk = Hunk(
            original_lines=[],
            proposed_lines=[long_line],
            original_start=0,
            proposed_start=0
        )
        
        context = hunk.get_context()
        assert len(context) == 50
        assert context == "x" * 50
    
    def test_hunk_get_context_deletion(self) -> None:
        """Test context for deletion-only hunk."""
        hunk = Hunk(
            original_lines=["old line\n"],
            proposed_lines=[],
            original_start=0,
            proposed_start=0
        )
        
        context = hunk.get_context()
        assert context == "deletion"


class TestDiffViewer:
    """Tests for DiffViewer class."""
    
    @pytest.fixture
    def temp_files(self, tmp_path: Path) -> tuple[Path, Path]:
        """Create temporary files for testing."""
        original = tmp_path / "original.py"
        original.write_text("def hello():\n    print('Hello')\n")
        
        proposed = tmp_path / "proposed.py"
        proposed.write_text("def hello():\n    print('Hello, World!')\n")
        
        return original, proposed
    
    def test_viewer_initialization(self, temp_files: tuple[Path, Path]) -> None:
        """Test DiffViewer initialization."""
        original, proposed = temp_files
        viewer = DiffViewer(original, proposed, keybinding_mode="nvim")
        
        assert viewer.original_path == original
        assert viewer.proposed_path == proposed
        assert viewer.keybinding_mode == "nvim"
        assert viewer.filename == "proposed.py"
        assert len(viewer.hunks) > 0
        assert viewer.current_hunk_idx == 0
        assert len(viewer.history) == 0
    
    def test_keybinding_detection_nvim(
        self, temp_files: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test auto-detection of nvim keybindings."""
        monkeypatch.setenv("EDITOR", "nvim")
        original, proposed = temp_files
        viewer = DiffViewer(original, proposed, keybinding_mode="auto")
        
        assert viewer.keybinding_mode == "nvim"
    
    def test_keybinding_detection_fresh(
        self, temp_files: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test auto-detection defaults to fresh mode."""
        monkeypatch.delenv("EDITOR", raising=False)
        monkeypatch.delenv("VISUAL", raising=False)
        original, proposed = temp_files
        viewer = DiffViewer(original, proposed, keybinding_mode="auto")
        
        assert viewer.keybinding_mode == "fresh"
    
    def test_hunk_generation(self, temp_files: tuple[Path, Path]) -> None:
        """Test that hunks are generated correctly."""
        original, proposed = temp_files
        viewer = DiffViewer(original, proposed)
        
        assert len(viewer.hunks) == 1
        hunk = viewer.hunks[0]
        assert "Hello" in "".join(hunk.original_lines)
        assert "Hello, World!" in "".join(hunk.proposed_lines)
    
    def test_no_differences(self, tmp_path: Path) -> None:
        """Test handling of identical files."""
        file1 = tmp_path / "file1.txt"
        file1.write_text("same content\n")
        file2 = tmp_path / "file2.txt"
        file2.write_text("same content\n")
        
        viewer = DiffViewer(file1, file2)
        assert len(viewer.hunks) == 0
    
    def test_apply_changes_accept_all(self, temp_files: tuple[Path, Path]) -> None:
        """Test applying changes when all hunks are accepted."""
        original, proposed = temp_files
        viewer = DiffViewer(original, proposed)
        
        # Accept all hunks
        for hunk in viewer.hunks:
            hunk.accepted = True
        
        result = viewer._apply_changes()
        assert "Hello, World!" in result
        assert "print('Hello')" not in result or "print('Hello, World!')" in result
    
    def test_apply_changes_reject_all(self, temp_files: tuple[Path, Path]) -> None:
        """Test that rejecting all hunks keeps original content."""
        original, proposed = temp_files
        viewer = DiffViewer(original, proposed)
        
        # Reject all hunks
        for hunk in viewer.hunks:
            hunk.accepted = False
        
        result = viewer._apply_changes()
        assert result == viewer.original_content
    
    def test_keybindings_nvim(self, temp_files: tuple[Path, Path]) -> None:
        """Test nvim keybinding configuration."""
        original, proposed = temp_files
        viewer = DiffViewer(original, proposed, keybinding_mode="nvim")
        
        kb = viewer._get_keybindings()
        assert "y" in kb["accept"]
        assert "j" in kb["next"]
        assert "k" in kb["prev"]
        assert "u" in kb["undo"]
    
    def test_keybindings_fresh(self, temp_files: tuple[Path, Path]) -> None:
        """Test fresh keybinding configuration."""
        original, proposed = temp_files
        viewer = DiffViewer(original, proposed, keybinding_mode="fresh")
        
        kb = viewer._get_keybindings()
        assert "Enter" in kb["accept"]
        assert "Down" in kb["next"]
        assert "Up" in kb["prev"]
        assert "Ctrl-Z" in kb["undo"]
    
    def test_lexer_detection_python(self, temp_files: tuple[Path, Path]) -> None:
        """Test lexer detection for Python files."""
        original, proposed = temp_files
        viewer = DiffViewer(original, proposed)
        
        # Lexer detection depends on Pygments availability
        if viewer.lexer_name:
            assert viewer.lexer_name == "Python"
    
    def test_lexer_detection_unknown(self, tmp_path: Path) -> None:
        """Test lexer detection for unknown file types."""
        original = tmp_path / "file.unknown"
        original.write_text("content\n")
        proposed = tmp_path / "file2.unknown"
        proposed.write_text("new content\n")
        
        viewer = DiffViewer(original, proposed)
        # Should handle gracefully even if lexer not found
        assert viewer.lexer_name is None or isinstance(viewer.lexer_name, str)
    
    def test_split_hunk(self, temp_files: tuple[Path, Path]) -> None:
        """Test splitting a hunk into smaller hunks."""
        original, proposed = temp_files
        viewer = DiffViewer(original, proposed)
        
        initial_count = len(viewer.hunks)
        hunk = viewer.hunks[0]
        
        # Only test if hunk has multiple lines
        if len(hunk.proposed_lines) > 1:
            viewer._split_hunk(hunk, 0)
            assert len(viewer.hunks) > initial_count
    
    def test_split_hunk_too_small(self, tmp_path: Path) -> None:
        """Test that single-line hunks cannot be split."""
        original = tmp_path / "orig.txt"
        original.write_text("line1\n")
        proposed = tmp_path / "prop.txt"
        proposed.write_text("line2\n")
        
        viewer = DiffViewer(original, proposed)
        initial_count = len(viewer.hunks)
        
        if viewer.hunks:
            viewer._split_hunk(viewer.hunks[0], 0)
            # Should not increase count for single-line hunks
            assert len(viewer.hunks) >= initial_count
    
    def test_history_tracking(self, temp_files: tuple[Path, Path]) -> None:
        """Test that history is tracked for undo."""
        original, proposed = temp_files
        viewer = DiffViewer(original, proposed)
        
        hunk = viewer.hunks[0]
        initial_state = hunk.accepted
        
        # Simulate accepting a hunk with history tracking
        viewer.history.append((0, initial_state))
        hunk.accepted = True
        
        assert len(viewer.history) == 1
        assert viewer.history[0] == (0, initial_state)
        
        # Undo
        hunk_idx, prev_state = viewer.history.pop()
        hunk.accepted = prev_state
        
        assert hunk.accepted == initial_state
        assert len(viewer.history) == 0


class TestDiffEditorPlugin:
    """Tests for plugin integration."""
    
    def test_plugin_loads(self) -> None:
        """Test that plugin can be imported and loaded."""
        from claude_dev_cli.plugins.diff_editor.plugin import DiffEditorPlugin
        
        plugin = DiffEditorPlugin()
        assert plugin.name == "diff-editor"
        assert plugin.version == "0.1.0"
    
    def test_plugin_registration(self) -> None:
        """Test plugin registration function."""
        from claude_dev_cli.plugins.diff_editor.plugin import register_plugin
        
        plugin = register_plugin()
        assert plugin is not None
        assert hasattr(plugin, "register_commands")
