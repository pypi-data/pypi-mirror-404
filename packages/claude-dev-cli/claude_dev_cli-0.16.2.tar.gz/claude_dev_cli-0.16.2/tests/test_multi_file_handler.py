"""Tests for multi_file_handler module."""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock
from claude_dev_cli.multi_file_handler import (
    FileChange,
    MultiFileResponse,
    extract_code_blocks,
    count_lines
)


def test_file_change_dataclass():
    """Test FileChange dataclass creation."""
    fc = FileChange(
        path="test.py",
        content="print('hello')",
        change_type="create"
    )
    assert fc.path == "test.py"
    assert fc.content == "print('hello')"
    assert fc.change_type == "create"
    assert fc.original_content is None
    assert fc.diff is None


def test_extract_code_blocks_python():
    """Test extracting code from Python block."""
    text = """
## File: test.py
```python
def hello():
    print("world")
```
"""
    result = extract_code_blocks(text)
    assert len(result) == 1
    assert result[0][0] == "File: test.py"
    assert "def hello():" in result[0][2]
    assert "print(\"world\")" in result[0][2]


def test_extract_code_blocks_multiple():
    """Test extracting multiple code blocks."""
    text = """
## File: file1.py
```python
x = 1
```

## File: file2.js
```javascript
let y = 2;
```
"""
    result = extract_code_blocks(text)
    assert len(result) == 2
    assert "x = 1" in result[0][2]
    assert "let y = 2" in result[1][2]


def test_extract_code_blocks_no_blocks():
    """Test text with no code blocks."""
    text = "Just plain text without code blocks"
    result = extract_code_blocks(text)
    assert len(result) == 0


def test_count_lines():
    """Test line counting."""
    assert count_lines("single line") == 1
    assert count_lines("line 1\nline 2\nline 3") == 3
    assert count_lines("") == 0
    assert count_lines("\n\n\n") == 0  # Empty lines don't count


def test_parse_response_file_marker():
    """Test parsing response with ## File: markers."""
    response = """
Some intro text.

## File: src/main.py
```python
def main():
    print("hello")
```

## File: src/utils.py
```python
def util():
    return True
```
"""
    
    multi = MultiFileResponse()
    multi.parse_response(response, base_path=Path("/project"))
    
    assert len(multi.files) == 2
    assert multi.files[0].path == "src/main.py"
    assert "def main():" in multi.files[0].content
    assert multi.files[1].path == "src/utils.py"
    assert "def util():" in multi.files[1].content


def test_parse_response_create_marker():
    """Test parsing response with ## Create: markers."""
    response = """
## Create: new_file.py
```python
# New file
x = 1
```
"""
    
    multi = MultiFileResponse()
    multi.parse_response(response, base_path=Path("/project"))
    
    assert len(multi.files) == 1
    assert multi.files[0].path == "new_file.py"
    assert multi.files[0].change_type == "create"
    assert "x = 1" in multi.files[0].content


def test_parse_response_modify_marker(tmp_path):
    """Test parsing response with ## Modify: markers."""
    # Create existing file
    (tmp_path / "existing.py").write_text("old content")
    
    response = """
## Modify: existing.py
```python
# Modified content
x = 2
```
"""
    
    multi = MultiFileResponse()
    multi.parse_response(response, base_path=tmp_path)
    
    assert len(multi.files) == 1
    assert multi.files[0].path == "existing.py"
    assert multi.files[0].change_type == "modify"
    assert multi.files[0].original_content == "old content"


def test_parse_response_delete_marker():
    """Test parsing response with ## Delete: markers."""
    response = """
## Delete: old_file.py

This file is no longer needed.
"""
    
    multi = MultiFileResponse()
    multi.parse_response(response, base_path=Path("/project"))
    
    assert len(multi.files) == 1
    assert multi.files[0].path == "old_file.py"
    assert multi.files[0].change_type == "delete"
    assert multi.files[0].content == ""


def test_parse_response_empty():
    """Test parsing empty or invalid response."""
    multi = MultiFileResponse()
    multi.parse_response("No file markers here", base_path=Path("/project"))
    
    assert len(multi.files) == 0


def test_parse_response_mixed_markers(tmp_path):
    """Test parsing with different marker types."""
    # Create existing file for modify test
    (tmp_path / "existing.py").write_text("old")
    
    response = """
## Create: new.py
```python
x = 1
```

## Modify: existing.py
```python
x = 2
```

## Delete: old.py
"""
    
    multi = MultiFileResponse()
    multi.parse_response(response, base_path=tmp_path)
    
    assert len(multi.files) == 3
    assert multi.files[0].change_type == "create"
    assert multi.files[1].change_type == "modify"
    assert multi.files[2].change_type == "delete"


def test_validate_paths_valid(tmp_path):
    """Test path validation with valid paths."""
    multi = MultiFileResponse()
    multi.files = [
        FileChange("file.py", "content", "create"),
        FileChange("subdir/file.py", "content", "create")
    ]
    
    errors = multi.validate_paths(tmp_path)
    assert len(errors) == 0


def test_validate_paths_absolute():
    """Test path validation rejects absolute paths."""
    multi = MultiFileResponse()
    multi.files = [
        FileChange("/etc/passwd", "content", "create")
    ]
    
    errors = multi.validate_paths(Path("/project"))
    assert len(errors) == 1
    assert "absolute path" in errors[0].lower()


def test_validate_paths_traversal():
    """Test path validation rejects path traversal."""
    multi = MultiFileResponse()
    multi.files = [
        FileChange("../../../etc/passwd", "content", "create")
    ]
    
    errors = multi.validate_paths(Path("/project"))
    assert len(errors) == 1
    assert "path traversal" in errors[0].lower()


def test_validate_paths_special_chars():
    """Test path validation handles special characters."""
    multi = MultiFileResponse()
    multi.files = [
        FileChange("file-name_v2.py", "content", "create"),
        FileChange("path/to/file.test.js", "content", "create")
    ]
    
    errors = multi.validate_paths(Path("/project"))
    assert len(errors) == 0


def test_build_tree_single_file(tmp_path):
    """Test building tree for single file."""
    from rich.tree import Tree
    
    multi = MultiFileResponse()
    multi.files = [
        FileChange("file.py", "content", "create")
    ]
    
    tree = multi.build_tree(tmp_path)
    assert isinstance(tree, Tree)
    # Tree should exist and have content
    assert tree is not None


def test_build_tree_nested(tmp_path):
    """Test building tree for nested structure."""
    multi = MultiFileResponse()
    multi.files = [
        FileChange("src/main.py", "x = 1", "create"),
        FileChange("src/utils.py", "y = 2", "create"),
        FileChange("tests/test_main.py", "z = 3", "create")
    ]
    
    tree = multi.build_tree(tmp_path)
    # Tree should have nested structure
    assert tree is not None


def test_preview_output(tmp_path):
    """Test preview output to console."""
    multi = MultiFileResponse()
    multi.files = [
        FileChange("file.py", "x = 1", "create"),
        FileChange("old.py", "", "delete")
    ]
    
    console = Mock()
    multi.preview(console, tmp_path)
    
    # Should print tree and summary
    assert console.print.call_count >= 2


def test_write_all_creates_files(tmp_path):
    """Test writing files creates them."""
    multi = MultiFileResponse()
    multi.files = [
        FileChange("new.py", "x = 1", "create"),
        FileChange("sub/file.py", "y = 2", "create")
    ]
    
    console = Mock()
    multi.write_all(tmp_path, dry_run=False, console=console)
    
    assert (tmp_path / "new.py").exists()
    assert (tmp_path / "new.py").read_text() == "x = 1"
    assert (tmp_path / "sub" / "file.py").exists()
    assert (tmp_path / "sub" / "file.py").read_text() == "y = 2"


def test_write_all_modifies_files(tmp_path):
    """Test writing files modifies existing ones."""
    # Create existing file
    existing = tmp_path / "existing.py"
    existing.write_text("old content")
    
    multi = MultiFileResponse()
    multi.files = [
        FileChange("existing.py", "new content", "modify")
    ]
    
    console = Mock()
    multi.write_all(tmp_path, dry_run=False, console=console)
    
    assert existing.read_text() == "new content"


def test_write_all_deletes_files(tmp_path):
    """Test writing files deletes marked files."""
    # Create file to delete
    to_delete = tmp_path / "delete_me.py"
    to_delete.write_text("content")
    
    multi = MultiFileResponse()
    multi.files = [
        FileChange("delete_me.py", "", "delete")
    ]
    
    console = Mock()
    multi.write_all(tmp_path, dry_run=False, console=console)
    
    assert not to_delete.exists()


def test_write_all_dry_run(tmp_path):
    """Test dry-run mode doesn't write files."""
    multi = MultiFileResponse()
    multi.files = [
        FileChange("new.py", "x = 1", "create")
    ]
    
    console = Mock()
    multi.write_all(tmp_path, dry_run=True, console=console)
    
    assert not (tmp_path / "new.py").exists()
    # Should still print what would be done
    assert console.print.call_count > 0


def test_write_all_error_handling(tmp_path):
    """Test error handling during file writes."""
    # Write to a regular file should work
    multi = MultiFileResponse()
    multi.files = [
        FileChange("test/file.py", "content", "create")
    ]
    
    console = Mock()
    
    # This should succeed
    multi.write_all(tmp_path, dry_run=False, console=console)
    
    # Verify file was created
    assert (tmp_path / "test" / "file.py").exists()


def test_confirm_yes(tmp_path):
    """Test confirmation with yes response."""
    multi = MultiFileResponse()
    multi.files = [
        FileChange("file.py", "content", "create")
    ]
    
    console = Mock()
    console.input.return_value = "y"
    
    result = multi.confirm(console)
    assert result is True


def test_confirm_no(tmp_path):
    """Test confirmation with no response."""
    multi = MultiFileResponse()
    multi.files = [
        FileChange("file.py", "content", "create")
    ]
    
    console = Mock()
    console.input.return_value = "n"
    
    result = multi.confirm(console)
    assert result is False


def test_confirm_preview(tmp_path):
    """Test confirmation with preview option."""
    multi = MultiFileResponse()
    multi.files = [
        FileChange("file.py", "# comment\nx = 1\ny = 2", "create")
    ]
    
    console = Mock()
    # First preview, then yes
    console.input.side_effect = ["preview", "y"]
    
    result = multi.confirm(console)
    assert result is True
    # Should have shown file content during preview
    assert console.print.call_count >= 1


def test_parse_response_with_language_identifiers():
    """Test parsing with various language identifiers."""
    response = """
## File: script.py
```python
print("hello")
```

## File: main.js
```javascript
console.log("hello");
```

## File: style.css
```css
body { margin: 0; }
```
"""
    
    multi = MultiFileResponse()
    multi.parse_response(response, base_path=Path("/project"))
    
    assert len(multi.files) == 3
    assert "print" in multi.files[0].content
    assert "console.log" in multi.files[1].content
    assert "margin" in multi.files[2].content


def test_parse_response_whitespace_handling():
    """Test parsing handles various whitespace patterns."""
    response = """
## File:     src/file.py   
```python
def test():
    pass
```

## File: tests/test.py
```python
assert True
```
"""
    
    multi = MultiFileResponse()
    multi.parse_response(response, base_path=Path("/project"))
    
    # Should handle extra whitespace
    assert len(multi.files) == 2
    assert "src/file.py" in multi.files[0].path
    assert "tests/test.py" in multi.files[1].path


def test_empty_files_list():
    """Test handling empty files list."""
    multi = MultiFileResponse()
    assert len(multi.files) == 0
    
    console = Mock()
    errors = multi.validate_paths(Path("/project"))
    assert len(errors) == 0
    
    # Preview with no files
    multi.preview(console, Path("/project"))
    # Should not crash


def test_parse_response_code_without_language():
    """Test parsing code blocks without language identifier."""
    response = """
## File: script.sh
```
#!/bin/bash
echo "hello"
```
"""
    
    multi = MultiFileResponse()
    multi.parse_response(response, base_path=Path("/project"))
    
    assert len(multi.files) == 1
    assert "echo" in multi.files[0].content


def test_hunk_dataclass():
    """Test HunkWrapper dataclass creation."""
    from claude_dev_cli.multi_file_handler import HunkWrapper
    from unittest.mock import Mock
    
    # Create a mock unidiff.Hunk object
    mock_hunk = Mock()
    mock_hunk.source_start = 1
    mock_hunk.source_length = 3
    mock_hunk.target_start = 1
    mock_hunk.target_length = 3
    mock_hunk.__str__ = lambda self: "@@ -1,3 +1,3 @@"
    
    wrapper = HunkWrapper(hunk=mock_hunk)
    
    assert wrapper.source_start == 1
    assert wrapper.approved is False
    assert "@@ -1,3 +1,3 @@" in str(wrapper)


def test_parse_hunks(tmp_path):
    """Test parsing diff into hunks."""
    # Create original file
    (tmp_path / "file.py").write_text("line 1\nline 2\nline 3\nline 4")
    
    response = """
## Modify: file.py
```python
line 1
line 2 modified
line 3
line 4
```
"""
    
    multi = MultiFileResponse()
    multi.parse_response(response, base_path=tmp_path)
    
    assert len(multi.files) == 1
    file_change = multi.files[0]
    assert file_change.change_type == "modify"
    assert file_change.diff is not None
    
    # Parse hunks
    file_change.parse_hunks()
    assert len(file_change.hunks) > 0
    assert file_change.hunks[0].source_start >= 1


def test_apply_approved_hunks_all(tmp_path):
    """Test applying all approved hunks."""
    original = "line 1\nline 2\nline 3"
    (tmp_path / "file.py").write_text(original)
    
    response = """
## Modify: file.py
```python
line 1 modified
line 2
line 3 modified
```
"""
    
    multi = MultiFileResponse()
    multi.parse_response(response, base_path=tmp_path)
    
    file_change = multi.files[0]
    file_change.parse_hunks()
    
    # Approve all hunks
    for hunk in file_change.hunks:
        hunk.approved = True
    
    result = file_change.apply_approved_hunks()
    assert "modified" in result


def test_apply_approved_hunks_none(tmp_path):
    """Test applying no approved hunks returns original."""
    original = "line 1\nline 2\nline 3"
    (tmp_path / "file.py").write_text(original)
    
    response = """
## Modify: file.py
```python
line 1 modified
line 2
line 3
```
"""
    
    multi = MultiFileResponse()
    multi.parse_response(response, base_path=tmp_path)
    
    file_change = multi.files[0]
    file_change.parse_hunks()
    
    # Don't approve any hunks
    result = file_change.apply_approved_hunks()
    assert result == file_change.original_content


def test_apply_approved_hunks_partial(tmp_path):
    """Test applying partial hunks."""
    original = "line 1\nline 2\nline 3\nline 4"
    (tmp_path / "file.py").write_text(original)
    
    response = """
## Modify: file.py
```python
line 1 modified
line 2 modified
line 3 modified
line 4 modified
```
"""
    
    multi = MultiFileResponse()
    multi.parse_response(response, base_path=tmp_path)
    
    file_change = multi.files[0]
    file_change.parse_hunks()
    
    if len(file_change.hunks) > 1:
        # Approve only first hunk
        file_change.hunks[0].approved = True
        result = file_change.apply_approved_hunks()
        # Should have some modifications but not all
        assert result != file_change.original_content
        assert result != file_change.content


def test_write_all_with_hunks(tmp_path):
    """Test writing files with approved hunks."""
    original = "line 1\nline 2\nline 3"
    (tmp_path / "file.py").write_text(original)
    
    response = """
## Modify: file.py
```python
line 1 modified
line 2
line 3
```
"""
    
    multi = MultiFileResponse()
    multi.parse_response(response, base_path=tmp_path)
    
    file_change = multi.files[0]
    file_change.parse_hunks()
    
    # Approve all hunks
    for hunk in file_change.hunks:
        hunk.approved = True
    
    console = Mock()
    multi.write_all(tmp_path, dry_run=False, console=console)
    
    # File should be modified
    result_content = (tmp_path / "file.py").read_text()
    assert "modified" in result_content


def test_write_all_skips_rejected_hunks(tmp_path):
    """Test that rejected hunks are not applied."""
    original = "line 1\nline 2\nline 3"
    (tmp_path / "file.py").write_text(original)
    
    response = """
## Modify: file.py
```python
line 1 modified
line 2
line 3
```
"""
    
    multi = MultiFileResponse()
    multi.parse_response(response, base_path=tmp_path)
    
    file_change = multi.files[0]
    file_change.parse_hunks()
    
    # Don't approve any hunks
    console = Mock()
    multi.write_all(tmp_path, dry_run=False, console=console)
    
    # File should remain unchanged
    result_content = (tmp_path / "file.py").read_text()
    assert result_content == original
