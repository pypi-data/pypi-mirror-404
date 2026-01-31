"""Tests for context module."""

import json
import subprocess
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock, patch, MagicMock

import pytest

from claude_dev_cli.context import (
    ContextItem,
    Context,
    GitContext,
    DependencyAnalyzer,
    ErrorContext,
    ContextGatherer
)


class TestContextItem:
    """Tests for ContextItem dataclass."""
    
    def test_create_context_item(self) -> None:
        """Test creating a context item."""
        item = ContextItem(
            type="file",
            content="def hello(): pass",
            metadata={"path": "/test/file.py"}
        )
        
        assert item.type == "file"
        assert item.content == "def hello(): pass"
        assert item.metadata["path"] == "/test/file.py"
    
    def test_format_file_context(self) -> None:
        """Test formatting file context for prompt."""
        item = ContextItem(
            type="file",
            content="print('hello')",
            metadata={"path": "test.py"}
        )
        
        formatted = item.format_for_prompt()
        assert "# File: test.py" in formatted
        assert "print('hello')" in formatted
    
    def test_format_git_context(self) -> None:
        """Test formatting git context for prompt."""
        item = ContextItem(
            type="git",
            content="Branch: main\nModified: file.py"
        )
        
        formatted = item.format_for_prompt()
        assert "# Git Context" in formatted
        assert "Branch: main" in formatted
    
    def test_format_dependency_context(self) -> None:
        """Test formatting dependency context for prompt."""
        item = ContextItem(
            type="dependency",
            content="Dependencies: requests, flask"
        )
        
        formatted = item.format_for_prompt()
        assert "# Dependencies" in formatted
        assert "requests" in formatted
    
    def test_format_error_context(self) -> None:
        """Test formatting error context for prompt."""
        item = ContextItem(
            type="error",
            content="TypeError: invalid type"
        )
        
        formatted = item.format_for_prompt()
        assert "# Error Context" in formatted
        assert "TypeError" in formatted


class TestContext:
    """Tests for Context collection class."""
    
    def test_create_empty_context(self) -> None:
        """Test creating empty context."""
        context = Context()
        
        assert context.items == []
        assert context.format_for_prompt() == ""
    
    def test_add_context_item(self) -> None:
        """Test adding items to context."""
        context = Context()
        item = ContextItem(type="file", content="test")
        
        context.add(item)
        
        assert len(context.items) == 1
        assert context.items[0] == item
    
    def test_get_by_type(self) -> None:
        """Test filtering context items by type."""
        context = Context()
        context.add(ContextItem(type="file", content="file1"))
        context.add(ContextItem(type="git", content="git1"))
        context.add(ContextItem(type="file", content="file2"))
        
        file_items = context.get_by_type("file")
        git_items = context.get_by_type("git")
        
        assert len(file_items) == 2
        assert len(git_items) == 1
        assert all(item.type == "file" for item in file_items)
    
    def test_format_for_prompt_with_items(self) -> None:
        """Test formatting multiple context items."""
        context = Context()
        context.add(ContextItem(type="file", content="code", metadata={"path": "test.py"}))
        context.add(ContextItem(type="git", content="Branch: main"))
        
        formatted = context.format_for_prompt()
        
        assert "# Context Information" in formatted
        assert "# File: test.py" in formatted
        assert "# Git Context" in formatted


class TestGitContext:
    """Tests for GitContext class."""
    
    def test_is_git_repo_true(self, tmp_path: Path) -> None:
        """Test detecting git repository."""
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        
        git_ctx = GitContext(tmp_path)
        assert git_ctx.is_git_repo() is True
    
    def test_is_git_repo_false(self, tmp_path: Path) -> None:
        """Test detecting non-git directory."""
        git_ctx = GitContext(tmp_path)
        assert git_ctx.is_git_repo() is False
    
    def test_get_current_branch(self, tmp_path: Path) -> None:
        """Test getting current branch name."""
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True, capture_output=True)
        
        # Create initial commit so branch exists
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial"], cwd=tmp_path, check=True, capture_output=True)
        
        git_ctx = GitContext(tmp_path)
        branch = git_ctx.get_current_branch()
        
        # Default branch could be 'master' or 'main' depending on git config
        assert branch in ["master", "main"]
    
    def test_get_current_branch_non_repo(self, tmp_path: Path) -> None:
        """Test getting branch from non-repo returns None."""
        git_ctx = GitContext(tmp_path)
        branch = git_ctx.get_current_branch()
        
        assert branch is None
    
    def test_get_recent_commits(self, tmp_path: Path) -> None:
        """Test getting recent commit history."""
        # Initialize git repo and create commits
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True, capture_output=True)
        
        # Create a file and commit
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=tmp_path, check=True, capture_output=True)
        
        git_ctx = GitContext(tmp_path)
        commits = git_ctx.get_recent_commits(5)
        
        assert len(commits) == 1
        assert commits[0]["message"] == "Initial commit"
        assert commits[0]["author"] == "Test User"
        assert "hash" in commits[0]
        assert "date" in commits[0]
    
    def test_get_recent_commits_non_repo(self, tmp_path: Path) -> None:
        """Test getting commits from non-repo returns empty list."""
        git_ctx = GitContext(tmp_path)
        commits = git_ctx.get_recent_commits()
        
        assert commits == []
    
    def test_get_staged_diff(self, tmp_path: Path) -> None:
        """Test getting staged changes diff."""
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True, capture_output=True)
        
        # Create and stage a file
        test_file = tmp_path / "test.txt"
        test_file.write_text("staged content")
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
        
        git_ctx = GitContext(tmp_path)
        diff = git_ctx.get_staged_diff()
        
        assert diff is not None
        assert "staged content" in diff
    
    def test_get_unstaged_diff(self, tmp_path: Path) -> None:
        """Test getting unstaged changes diff."""
        # Initialize git repo and create initial commit
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True, capture_output=True)
        
        test_file = tmp_path / "test.txt"
        test_file.write_text("original")
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial"], cwd=tmp_path, check=True, capture_output=True)
        
        # Modify file without staging
        test_file.write_text("modified")
        
        git_ctx = GitContext(tmp_path)
        diff = git_ctx.get_unstaged_diff()
        
        assert diff is not None
        assert "modified" in diff
    
    def test_get_modified_files(self, tmp_path: Path) -> None:
        """Test getting list of modified files."""
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True, capture_output=True)
        
        # Create files
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.txt").write_text("content2")
        
        git_ctx = GitContext(tmp_path)
        modified = git_ctx.get_modified_files()
        
        assert len(modified) == 2
        assert "file1.txt" in modified
        assert "file2.txt" in modified
    
    def test_gather_context(self, tmp_path: Path) -> None:
        """Test gathering complete git context."""
        # Initialize git repo with commits
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True, capture_output=True)
        
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Test commit"], cwd=tmp_path, check=True, capture_output=True)
        
        # Modify file
        test_file.write_text("modified content")
        
        git_ctx = GitContext(tmp_path)
        context_item = git_ctx.gather(include_diff=False)
        
        assert context_item.type == "git"
        assert "Branch:" in context_item.content
        assert "Test commit" in context_item.content
        assert "test.txt" in context_item.content


class TestDependencyAnalyzer:
    """Tests for DependencyAnalyzer class."""
    
    def test_find_python_imports(self, tmp_path: Path) -> None:
        """Test extracting Python imports from file."""
        code = """
import os
import sys
from pathlib import Path
from typing import List, Dict
import json.decoder
"""
        file_path = tmp_path / "test.py"
        file_path.write_text(code)
        
        analyzer = DependencyAnalyzer(tmp_path)
        imports = analyzer.find_python_imports(file_path)
        
        assert "os" in imports
        assert "sys" in imports
        assert "pathlib" in imports
        assert "typing" in imports
        assert "json" in imports
    
    def test_find_python_imports_invalid_syntax(self, tmp_path: Path) -> None:
        """Test handling invalid Python syntax."""
        file_path = tmp_path / "invalid.py"
        file_path.write_text("this is not valid python {{{")
        
        analyzer = DependencyAnalyzer(tmp_path)
        imports = analyzer.find_python_imports(file_path)
        
        # Should return empty set on parse error
        assert imports == set()
    
    def test_find_related_files(self, tmp_path: Path) -> None:
        """Test finding related files through imports."""
        # Create module files
        (tmp_path / "utils.py").write_text("def helper(): pass")
        (tmp_path / "models.py").write_text("class Model: pass")
        
        # Create main file that imports them
        main_file = tmp_path / "main.py"
        main_file.write_text("import utils\nfrom models import Model")
        
        analyzer = DependencyAnalyzer(tmp_path)
        related = analyzer.find_related_files(main_file)
        
        assert len(related) == 2
        assert tmp_path / "utils.py" in related
        assert tmp_path / "models.py" in related
    
    def test_find_related_files_non_python(self, tmp_path: Path) -> None:
        """Test finding related files for non-Python file."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("not python")
        
        analyzer = DependencyAnalyzer(tmp_path)
        related = analyzer.find_related_files(file_path)
        
        assert related == []
    
    def test_get_dependency_files_python(self, tmp_path: Path) -> None:
        """Test finding Python dependency files."""
        (tmp_path / "requirements.txt").write_text("requests==2.28.0")
        (tmp_path / "setup.py").write_text("from setuptools import setup")
        (tmp_path / "pyproject.toml").write_text("[tool.poetry]")
        
        analyzer = DependencyAnalyzer(tmp_path)
        dep_files = analyzer.get_dependency_files()
        
        assert len(dep_files) == 3
        assert tmp_path / "requirements.txt" in dep_files
        assert tmp_path / "setup.py" in dep_files
        assert tmp_path / "pyproject.toml" in dep_files
    
    def test_get_dependency_files_nodejs(self, tmp_path: Path) -> None:
        """Test finding Node.js dependency files."""
        (tmp_path / "package.json").write_text('{"name": "test"}')
        (tmp_path / "package-lock.json").write_text('{"lockfileVersion": 2}')
        
        analyzer = DependencyAnalyzer(tmp_path)
        dep_files = analyzer.get_dependency_files()
        
        assert len(dep_files) == 2
        assert tmp_path / "package.json" in dep_files
        assert tmp_path / "package-lock.json" in dep_files
    
    def test_get_dependency_files_multiple_languages(self, tmp_path: Path) -> None:
        """Test finding dependency files from multiple languages."""
        (tmp_path / "requirements.txt").write_text("flask==2.0.0")
        (tmp_path / "package.json").write_text('{"dependencies": {}}')
        (tmp_path / "Cargo.toml").write_text('[package]\nname = "test"')
        (tmp_path / "go.mod").write_text("module test")
        
        analyzer = DependencyAnalyzer(tmp_path)
        dep_files = analyzer.get_dependency_files()
        
        assert len(dep_files) == 4
    
    def test_gather_dependency_context(self, tmp_path: Path) -> None:
        """Test gathering dependency context."""
        # Create requirements file
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("requests==2.28.0\nflask==2.0.0\npytest==7.0.0")
        
        analyzer = DependencyAnalyzer(tmp_path)
        context_item = analyzer.gather()
        
        assert context_item.type == "dependency"
        assert "requirements.txt" in context_item.content
        assert "requests" in context_item.content or "Requirements:" in context_item.content
    
    def test_gather_with_target_file(self, tmp_path: Path) -> None:
        """Test gathering dependency context with target file."""
        # Create related files
        (tmp_path / "utils.py").write_text("def util(): pass")
        
        main_file = tmp_path / "main.py"
        main_file.write_text("import utils\nfrom pathlib import Path")
        
        analyzer = DependencyAnalyzer(tmp_path)
        context_item = analyzer.gather(target_file=main_file)
        
        assert context_item.type == "dependency"
        # Should include related files section
        assert "main.py" in context_item.content or "Related files" in context_item.content


class TestErrorContext:
    """Tests for ErrorContext class."""
    
    def test_detect_language_python(self) -> None:
        """Test Python language detection."""
        error_text = "Traceback (most recent call last):\n  File \"test.py\", line 10"
        assert ErrorContext.detect_language(error_text) == 'python'
    
    def test_detect_language_javascript(self) -> None:
        """Test JavaScript language detection."""
        error_text = "Error: test\n    at func (app.js:10:5)"
        assert ErrorContext.detect_language(error_text) == 'javascript'
    
    def test_detect_language_go(self) -> None:
        """Test Go language detection."""
        error_text = "panic: test\n\tmain.go:15"
        assert ErrorContext.detect_language(error_text) == 'go'
    
    def test_detect_language_rust(self) -> None:
        """Test Rust language detection."""
        error_text = "thread 'main' panicked at 'test', main.rs:10:5"
        assert ErrorContext.detect_language(error_text) == 'rust'
    
    def test_detect_language_java(self) -> None:
        """Test Java language detection."""
        error_text = "Exception in thread\nat Test.java:10"
        assert ErrorContext.detect_language(error_text) == 'java'
    
    def test_parse_simple_traceback(self) -> None:
        """Test parsing a simple Python traceback."""
        error_text = """
Traceback (most recent call last):
  File "/path/to/file.py", line 42, in main
    result = divide(10, 0)
  File "/path/to/utils.py", line 15, in divide
    return a / b
ZeroDivisionError: division by zero
"""
        
        parsed = ErrorContext.parse_traceback(error_text)
        
        assert parsed["error_type"] == "ZeroDivisionError"
        assert parsed["error_message"] == "division by zero"
        assert len(parsed["frames"]) == 2
        
        frame1 = parsed["frames"][0]
        assert frame1["file"] == "/path/to/file.py"
        assert frame1["line"] == 42
        assert frame1["function"] == "main"
        
        frame2 = parsed["frames"][1]
        assert frame2["file"] == "/path/to/utils.py"
        assert frame2["line"] == 15
        assert frame2["function"] == "divide"
    
    def test_parse_traceback_with_code(self) -> None:
        """Test parsing traceback that includes code lines."""
        error_text = """
Traceback (most recent call last):
  File "test.py", line 10, in test_function
    x = int("invalid")
ValueError: invalid literal for int() with base 10: 'invalid'
"""
        
        parsed = ErrorContext.parse_traceback(error_text)
        
        assert parsed["error_type"] == "ValueError"
        assert "invalid literal" in parsed["error_message"]
        assert len(parsed["frames"]) >= 1
    
    def test_parse_non_traceback(self) -> None:
        """Test parsing non-traceback error text."""
        error_text = "Simple error message without traceback"
        
        parsed = ErrorContext.parse_traceback(error_text)
        
        assert "raw" in parsed
        assert parsed["raw"] == error_text
    
    def test_format_for_ai(self) -> None:
        """Test formatting error for AI consumption."""
        error_text = """
Traceback (most recent call last):
  File "script.py", line 5, in main
    process_data()
  File "script.py", line 10, in process_data
    raise ValueError("Invalid data")
ValueError: Invalid data
"""
        
        formatted = ErrorContext.format_for_ai(error_text)
        
        assert "Error Type: ValueError" in formatted
        assert "Error Message: Invalid data" in formatted
        assert "Stack Trace:" in formatted
        assert "script.py:5" in formatted
        assert "script.py:10" in formatted
    
    def test_format_for_ai_non_traceback(self) -> None:
        """Test formatting non-traceback error."""
        error_text = "Simple error"
        
        formatted = ErrorContext.format_for_ai(error_text)
        
        # Should return original if not a traceback
        assert formatted == error_text
    
    def test_gather_error_context(self) -> None:
        """Test gathering error context."""
        error_text = """
Traceback (most recent call last):
  File "main.py", line 20, in run
    execute()
TypeError: execute() missing 1 required positional argument
"""
        
        error_ctx = ErrorContext()
        context_item = error_ctx.gather(error_text)
        
        assert context_item.type == "error"
        assert "TypeError" in context_item.content
        assert "main.py" in context_item.content
        assert "error_type" in context_item.metadata
    
    def test_parse_javascript_stack(self) -> None:
        """Test JavaScript stack trace parsing."""
        error_text = """
TypeError: Cannot read property 'foo' of undefined
    at myFunction (app.js:42:15)
    at main (index.js:10:5)
    at startup.js:100:1
"""
        
        parsed = ErrorContext.parse_javascript_stack(error_text)
        
        assert parsed['language'] == 'javascript'
        assert parsed['error_type'] == 'TypeError'
        assert "Cannot read property" in parsed['error_message']
        assert len(parsed['frames']) == 3
        
        frame1 = parsed['frames'][0]
        assert frame1['file'] == 'app.js'
        assert frame1['line'] == 42
        assert frame1['column'] == 15
        assert frame1['function'] == 'myFunction'
    
    def test_parse_go_panic(self) -> None:
        """Test Go panic trace parsing."""
        error_text = """
panic: runtime error: index out of range

goroutine 1 [running]:
main.process()
	/path/to/main.go:45 +0x1a3
main.main()
	/path/to/main.go:20 +0x2e
"""
        
        parsed = ErrorContext.parse_go_panic(error_text)
        
        assert parsed['language'] == 'go'
        assert parsed['error_type'] == 'panic'
        assert 'index out of range' in parsed['error_message']
        assert len(parsed['frames']) >= 2
        
        # Check that we found the files
        files = [f['file'] for f in parsed['frames']]
        assert any('main.go' in f for f in files)
    
    def test_parse_rust_panic(self) -> None:
        """Test Rust panic message parsing."""
        error_text = """
thread 'main' panicked at 'called `Result::unwrap()` on an `Err` value', src/main.rs:42:9
stack backtrace:
   0: rust_begin_unwind
             at /rustc/lib.rs:1:1
   1: core::panicking::panic_fmt
             at src/panicking.rs:50:5
   2: myapp::process
             at ./src/lib.rs:100:13
"""
        
        parsed = ErrorContext.parse_rust_panic(error_text)
        
        assert parsed['language'] == 'rust'
        assert parsed['error_type'] == 'panic'
        assert 'Result::unwrap()' in parsed['error_message']
        assert len(parsed['frames']) >= 1
        
        # First frame should be from the panic location
        frame1 = parsed['frames'][0]
        assert 'main.rs' in frame1['file']
        assert frame1['line'] == 42
        assert frame1['column'] == 9
    
    def test_parse_java_stack(self) -> None:
        """Test Java stack trace parsing."""
        error_text = """
java.lang.NullPointerException: Cannot invoke method on null object
	at com.example.MyClass.doSomething(MyClass.java:45)
	at com.example.Main.run(Main.java:20)
	at com.example.Main.main(Main.java:10)
"""
        
        parsed = ErrorContext.parse_java_stack(error_text)
        
        assert parsed['language'] == 'java'
        assert parsed['error_type'] == 'NullPointerException'
        assert 'Cannot invoke' in parsed['error_message']
        assert len(parsed['frames']) == 3
        
        frame1 = parsed['frames'][0]
        assert 'MyClass.java' in frame1['file']
        assert frame1['line'] == 45
        assert 'doSomething' in frame1['function']
    
    def test_parse_traceback_auto_detects_language(self) -> None:
        """Test that parse_traceback auto-detects language."""
        js_error = "Error: test\n    at func (app.js:10:5)"
        parsed = ErrorContext.parse_traceback(js_error)
        assert parsed['language'] == 'javascript'
        
        go_error = "panic: test\n\tmain.go:15"
        parsed = ErrorContext.parse_traceback(go_error)
        assert parsed['language'] == 'go'
    
    def test_format_for_ai_includes_language(self) -> None:
        """Test that formatted output includes language."""
        error_text = "TypeError: test\n    at func (app.js:10:5)"
        formatted = ErrorContext.format_for_ai(error_text)
        
        assert 'Language: Javascript' in formatted
        assert 'Error Type: TypeError' in formatted
        assert 'app.js:10:5' in formatted


class TestContextGatherer:
    """Tests for ContextGatherer coordinator class."""
    
    def test_init_with_default_path(self) -> None:
        """Test initializing with default path."""
        gatherer = ContextGatherer()
        
        assert gatherer.project_root == Path.cwd()
        assert isinstance(gatherer.git, GitContext)
        assert isinstance(gatherer.dependencies, DependencyAnalyzer)
        assert isinstance(gatherer.error_parser, ErrorContext)
    
    def test_init_with_custom_path(self, tmp_path: Path) -> None:
        """Test initializing with custom path."""
        gatherer = ContextGatherer(tmp_path)
        
        assert gatherer.project_root == tmp_path
    
    def test_gather_for_file(self, tmp_path: Path) -> None:
        """Test gathering context for a file."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def hello(): pass")
        
        gatherer = ContextGatherer(tmp_path)
        context = gatherer.gather_for_file(
            test_file,
            include_git=False,
            include_dependencies=False
        )
        
        assert len(context.items) >= 1
        file_items = context.get_by_type("file")
        assert len(file_items) == 1
        assert "def hello()" in file_items[0].content
    
    def test_gather_for_file_with_git(self, tmp_path: Path) -> None:
        """Test gathering context with git information."""
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True, capture_output=True)
        
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')")
        
        gatherer = ContextGatherer(tmp_path)
        context = gatherer.gather_for_file(test_file, include_git=True, include_dependencies=False)
        
        # Should have file + git context
        assert len(context.items) >= 2
        git_items = context.get_by_type("git")
        assert len(git_items) == 1
    
    def test_gather_for_file_with_dependencies(self, tmp_path: Path) -> None:
        """Test gathering context with dependency information."""
        (tmp_path / "requirements.txt").write_text("requests==2.28.0")
        
        test_file = tmp_path / "test.py"
        test_file.write_text("import requests")
        
        gatherer = ContextGatherer(tmp_path)
        context = gatherer.gather_for_file(
            test_file,
            include_git=False,
            include_dependencies=True
        )
        
        # Should have file + dependency context
        assert len(context.items) >= 2
        dep_items = context.get_by_type("dependency")
        assert len(dep_items) == 1
    
    def test_gather_for_nonexistent_file(self, tmp_path: Path) -> None:
        """Test gathering context for nonexistent file."""
        nonexistent = tmp_path / "nonexistent.py"
        
        gatherer = ContextGatherer(tmp_path)
        context = gatherer.gather_for_file(nonexistent, include_git=False, include_dependencies=False)
        
        # Should still return context object, but no file item
        file_items = context.get_by_type("file")
        assert len(file_items) == 0
    
    def test_gather_for_error(self, tmp_path: Path) -> None:
        """Test gathering context for error debugging."""
        error_text = """
Traceback (most recent call last):
  File "test.py", line 10, in main
    raise ValueError("Test error")
ValueError: Test error
"""
        
        gatherer = ContextGatherer(tmp_path)
        context = gatherer.gather_for_error(error_text, include_git=False)
        
        error_items = context.get_by_type("error")
        assert len(error_items) == 1
        assert "ValueError" in error_items[0].content
    
    def test_gather_for_error_with_file(self, tmp_path: Path) -> None:
        """Test gathering error context with associated file."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def broken(): raise ValueError()")
        
        error_text = "ValueError: something broke"
        
        gatherer = ContextGatherer(tmp_path)
        context = gatherer.gather_for_error(error_text, file_path=test_file, include_git=False)
        
        # Should have error + file context
        assert len(context.items) >= 2
        error_items = context.get_by_type("error")
        file_items = context.get_by_type("file")
        assert len(error_items) == 1
        assert len(file_items) == 1
    
    def test_gather_for_review(self, tmp_path: Path) -> None:
        """Test gathering context for code review."""
        test_file = tmp_path / "module.py"
        test_file.write_text("def feature(): return 42")
        
        gatherer = ContextGatherer(tmp_path)
        context = gatherer.gather_for_review(test_file, include_git=False, include_tests=False)
        
        # Should have file + dependency context
        file_items = context.get_by_type("file")
        assert len(file_items) >= 1
    
    def test_gather_for_review_with_tests(self, tmp_path: Path) -> None:
        """Test gathering review context with test file."""
        # Create module and test file
        module_file = tmp_path / "module.py"
        module_file.write_text("def feature(): return 42")
        
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / "test_module.py"
        test_file.write_text("def test_feature(): assert feature() == 42")
        
        gatherer = ContextGatherer(tmp_path)
        context = gatherer.gather_for_review(module_file, include_git=False, include_tests=True)
        
        file_items = context.get_by_type("file")
        # Should find the test file
        test_metadata = [item.metadata for item in file_items if item.metadata.get("is_test")]
        assert len(test_metadata) >= 1
