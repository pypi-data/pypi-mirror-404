"""Intelligent context gathering for AI operations."""

import ast
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field


@dataclass
class ContextItem:
    """A single piece of context information."""
    type: str  # 'file', 'git', 'dependency', 'error'
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def truncate(self, max_lines: Optional[int] = None) -> 'ContextItem':
        """Truncate content to specified number of lines."""
        if max_lines is None:
            return self
        
        lines = self.content.split('\n')
        if len(lines) <= max_lines:
            return self
        
        truncated_lines = lines[:max_lines]
        truncated_lines.append(f"\n... (truncated {len(lines) - max_lines} more lines)")
        
        return ContextItem(
            type=self.type,
            content='\n'.join(truncated_lines),
            metadata={**self.metadata, 'truncated': True, 'original_lines': len(lines)}
        )
    
    def format_for_prompt(self) -> str:
        """Format this context item for inclusion in a prompt."""
        if self.type == 'file':
            path = self.metadata.get('path', 'unknown')
            truncated_note = " (truncated)" if self.metadata.get('truncated') else ""
            return f"# File: {path}{truncated_note}\n\n{self.content}\n"
        elif self.type == 'git':
            return f"# Git Context\n\n{self.content}\n"
        elif self.type == 'dependency':
            return f"# Dependencies\n\n{self.content}\n"
        elif self.type == 'error':
            return f"# Error Context\n\n{self.content}\n"
        else:
            return self.content


@dataclass
class Context:
    """Collection of context items."""
    items: List[ContextItem] = field(default_factory=list)
    
    def add(self, item: ContextItem) -> None:
        """Add a context item."""
        self.items.append(item)
    
    def format_for_prompt(self) -> str:
        """Format all context items for inclusion in a prompt."""
        if not self.items:
            return ""
        
        parts = ["# Context Information\n"]
        for item in self.items:
            parts.append(item.format_for_prompt())
        
        return "\n".join(parts)
    
    def get_by_type(self, context_type: str) -> List[ContextItem]:
        """Get all context items of a specific type."""
        return [item for item in self.items if item.type == context_type]


class GitContext:
    """Gather Git-related context."""
    
    def __init__(self, cwd: Optional[Path] = None):
        self.cwd = cwd or Path.cwd()
    
    def is_git_repo(self) -> bool:
        """Check if current directory is a git repository."""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=self.cwd,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def get_current_branch(self) -> Optional[str]:
        """Get the current git branch."""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=self.cwd,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except Exception:
            return None
    
    def get_recent_commits(self, count: int = 5) -> List[Dict[str, str]]:
        """Get recent commit messages."""
        try:
            result = subprocess.run(
                ['git', '--no-pager', 'log', f'-{count}', '--pretty=format:%h|%s|%an|%ar'],
                cwd=self.cwd,
                capture_output=True,
                text=True,
                check=True
            )
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('|', 3)
                    if len(parts) == 4:
                        commits.append({
                            'hash': parts[0],
                            'message': parts[1],
                            'author': parts[2],
                            'date': parts[3]
                        })
            return commits
        except Exception:
            return []
    
    def get_staged_diff(self) -> Optional[str]:
        """Get diff of staged changes."""
        try:
            result = subprocess.run(
                ['git', '--no-pager', 'diff', '--cached'],
                cwd=self.cwd,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout if result.stdout else None
        except Exception:
            return None
    
    def get_unstaged_diff(self) -> Optional[str]:
        """Get diff of unstaged changes."""
        try:
            result = subprocess.run(
                ['git', '--no-pager', 'diff'],
                cwd=self.cwd,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout if result.stdout else None
        except Exception:
            return None
    
    def get_modified_files(self) -> List[str]:
        """Get list of modified files."""
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.cwd,
                capture_output=True,
                text=True,
                check=True
            )
            
            files = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    # Format: "XY filename"
                    parts = line.strip().split(maxsplit=1)
                    if len(parts) == 2:
                        files.append(parts[1])
            return files
        except Exception:
            return []
    
    def gather(self, include_diff: bool = False, max_diff_lines: int = 200) -> ContextItem:
        """Gather all git context.
        
        Args:
            include_diff: Include staged diff in context
            max_diff_lines: Maximum lines of diff to include
        """
        parts = []
        
        branch = self.get_current_branch()
        if branch:
            parts.append(f"Branch: {branch}")
        
        commits = self.get_recent_commits(5)
        if commits:
            parts.append("\nRecent commits:")
            for commit in commits:
                parts.append(f"  {commit['hash']} - {commit['message']} ({commit['date']})")
        
        modified = self.get_modified_files()
        if modified:
            parts.append(f"\nModified files: {', '.join(modified[:10])}")
        
        if include_diff:
            staged = self.get_staged_diff()
            if staged:
                diff_lines = staged.split('\n')
                if len(diff_lines) > max_diff_lines:
                    truncated_diff = '\n'.join(diff_lines[:max_diff_lines])
                    parts.append(f"\nStaged changes (truncated {len(diff_lines) - max_diff_lines} lines):\n{truncated_diff}\n... (diff truncated)")
                else:
                    parts.append(f"\nStaged changes:\n{staged}")
        
        content = "\n".join(parts) if parts else "No git context available"
        
        return ContextItem(
            type='git',
            content=content,
            metadata={'branch': branch, 'modified_count': len(modified)}
        )


class DependencyAnalyzer:
    """Analyze project dependencies and imports."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
    
    def find_python_imports(self, file_path: Path) -> Set[str]:
        """Extract imports from a Python file."""
        imports = set()
        
        try:
            with open(file_path, 'r') as f:
                tree = ast.parse(f.read())
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        imports.add(name.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split('.')[0])
        except Exception:
            pass
        
        return imports
    
    def find_related_files(self, file_path: Path, max_depth: int = 2) -> List[Path]:
        """Find files related to the given file through imports."""
        if not file_path.suffix == '.py':
            return []
        
        related = []
        imports = self.find_python_imports(file_path)
        
        # Look for local modules
        for imp in imports:
            # Try as module file
            module_file = self.project_root / f"{imp}.py"
            if module_file.exists() and module_file != file_path:
                related.append(module_file)
            
            # Try as package
            package_init = self.project_root / imp / "__init__.py"
            if package_init.exists():
                related.append(package_init)
        
        return related[:5]  # Limit to avoid too many files
    
    def get_dependency_files(self) -> List[Path]:
        """Find dependency configuration files."""
        files = []
        
        # Python
        for name in ['requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile']:
            file = self.project_root / name
            if file.exists():
                files.append(file)
        
        # Node.js
        for name in ['package.json', 'package-lock.json']:
            file = self.project_root / name
            if file.exists():
                files.append(file)
        
        # Other
        for name in ['Gemfile', 'go.mod', 'Cargo.toml']:
            file = self.project_root / name
            if file.exists():
                files.append(file)
        
        return files
    
    def gather(self, target_file: Optional[Path] = None) -> ContextItem:
        """Gather dependency context."""
        parts = []
        
        # Include dependency files
        dep_files = self.get_dependency_files()
        if dep_files:
            parts.append("Dependency files:")
            for file in dep_files[:3]:  # Limit
                parts.append(f"  - {file.name}")
                try:
                    content = file.read_text()
                    # Include only relevant parts
                    if file.suffix == '.json':
                        data = json.loads(content)
                        if 'dependencies' in data:
                            parts.append(f"    Dependencies: {', '.join(list(data['dependencies'].keys())[:10])}")
                    elif file.suffix == '.txt':
                        lines = content.split('\n')[:20]
                        parts.append(f"    Requirements: {', '.join([l.split('==')[0] for l in lines if l and not l.startswith('#')])}")
                except Exception:
                    pass
        
        # Related files if target specified
        if target_file and target_file.exists():
            related = self.find_related_files(target_file)
            if related:
                parts.append(f"\nRelated files for {target_file.name}:")
                for file in related:
                    parts.append(f"  - {file.relative_to(self.project_root)}")
        
        content = "\n".join(parts) if parts else "No dependency context found"
        
        return ContextItem(
            type='dependency',
            content=content,
            metadata={'dependency_files': [str(f) for f in dep_files]}
        )


class ErrorContext:
    """Parse and format error context for multiple languages."""
    
    @staticmethod
    def detect_language(error_text: str) -> str:
        """Detect programming language from error format."""
        if 'Traceback (most recent call last):' in error_text or 'File "' in error_text:
            return 'python'
        elif 'at ' in error_text and ('.js:' in error_text or '.ts:' in error_text):
            return 'javascript'
        elif 'panic:' in error_text and '.go:' in error_text:
            return 'go'
        elif 'thread' in error_text and 'panicked at' in error_text and '.rs:' in error_text:
            return 'rust'
        elif 'at ' in error_text and '.java:' in error_text:
            return 'java'
        return 'unknown'
    
    @staticmethod
    def parse_python_traceback(error_text: str) -> Dict[str, Any]:
        """Parse Python traceback into structured data."""
        lines = error_text.split('\n')
        
        # Find traceback start
        traceback_start = -1
        for i, line in enumerate(lines):
            if 'Traceback' in line:
                traceback_start = i
                break
        
        if traceback_start == -1:
            return {'raw': error_text}
        
        # Extract frames
        frames = []
        current_frame = {}
        
        for line in lines[traceback_start + 1:]:
            if line.startswith('  File '):
                if current_frame:
                    frames.append(current_frame)
                
                # Parse: File "path", line X, in function
                match = re.match(r'\s*File "([^"]+)", line (\d+), in (.+)', line)
                if match:
                    current_frame = {
                        'file': match.group(1),
                        'line': int(match.group(2)),
                        'function': match.group(3)
                    }
            elif line.startswith('    ') and current_frame:
                current_frame['code'] = line.strip()
            elif line and not line.startswith(' '):
                # Error message
                if current_frame:
                    frames.append(current_frame)
                    current_frame = {}
                
                error_type = line.split(':')[0] if ':' in line else line
                error_message = line.split(':', 1)[1].strip() if ':' in line else ''
                
                return {
                    'frames': frames,
                    'error_type': error_type,
                    'error_message': error_message,
                    'raw': error_text
                }
        
        return {'frames': frames, 'raw': error_text, 'language': 'python'}
    
    @staticmethod
    def parse_javascript_stack(error_text: str) -> Dict[str, Any]:
        """Parse JavaScript/TypeScript stack trace."""
        lines = error_text.split('\n')
        frames = []
        error_type = None
        error_message = None
        
        for line in lines:
            # Error message usually first: "Error: message" or "TypeError: message"
            if not error_type and (':' in line and not line.strip().startswith('at')):
                parts = line.split(':', 1)
                error_type = parts[0].strip()
                error_message = parts[1].strip() if len(parts) > 1 else ''
            # Stack frame: "at functionName (file.js:line:col)" or "at file.js:line:col"
            elif line.strip().startswith('at '):
                match = re.search(r'at\s+(?:(.+?)\s+)?\(([^)]+)\)|(\S+)$', line)
                if match:
                    function = match.group(1) or 'anonymous'
                    location = match.group(2) or match.group(3)
                    if location and ':' in location:
                        parts = location.rsplit(':', 2)
                        frames.append({
                            'file': parts[0],
                            'line': int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None,
                            'column': int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else None,
                            'function': function
                        })
        
        return {
            'frames': frames,
            'error_type': error_type,
            'error_message': error_message,
            'raw': error_text,
            'language': 'javascript'
        }
    
    @staticmethod
    def parse_go_panic(error_text: str) -> Dict[str, Any]:
        """Parse Go panic trace."""
        lines = error_text.split('\n')
        frames = []
        error_message = None
        
        for line in lines:
            # Panic message: "panic: message"
            if line.startswith('panic:'):
                error_message = line.replace('panic:', '').strip()
            # Stack frame: "function(args)" followed by "\tfile.go:line +0xhex"
            elif '\t' in line and '.go:' in line:
                match = re.search(r'([^/\s]+\.go):(\d+)', line)
                if match:
                    frames.append({
                        'file': match.group(1),
                        'line': int(match.group(2)),
                        'function': 'goroutine'
                    })
        
        return {
            'frames': frames,
            'error_type': 'panic',
            'error_message': error_message,
            'raw': error_text,
            'language': 'go'
        }
    
    @staticmethod
    def parse_rust_panic(error_text: str) -> Dict[str, Any]:
        """Parse Rust panic message."""
        lines = error_text.split('\n')
        frames = []
        error_message = None
        
        for line in lines:
            # Panic message: "thread 'main' panicked at 'message', file.rs:line:col"
            if 'panicked at' in line:
                match = re.search(r"panicked at '([^']+)', ([^:]+):(\d+):(\d+)", line)
                if match:
                    error_message = match.group(1)
                    frames.append({
                        'file': match.group(2),
                        'line': int(match.group(3)),
                        'column': int(match.group(4)),
                        'function': 'panic'
                    })
            # Stack backtrace frames
            elif '.rs:' in line:
                match = re.search(r'([^/\s]+\.rs):(\d+):(\d+)', line)
                if match:
                    frames.append({
                        'file': match.group(1),
                        'line': int(match.group(2)),
                        'column': int(match.group(3)),
                        'function': 'unknown'
                    })
        
        return {
            'frames': frames,
            'error_type': 'panic',
            'error_message': error_message,
            'raw': error_text,
            'language': 'rust'
        }
    
    @staticmethod
    def parse_java_stack(error_text: str) -> Dict[str, Any]:
        """Parse Java stack trace."""
        lines = error_text.split('\n')
        frames = []
        error_type = None
        error_message = None
        
        for line in lines:
            # Exception message: "java.lang.NullPointerException: message"
            if not error_type and 'Exception' in line or 'Error' in line:
                parts = line.split(':', 1)
                error_type = parts[0].strip().split('.')[-1]  # Get last part of package
                error_message = parts[1].strip() if len(parts) > 1 else ''
            # Stack frame: "at package.Class.method(File.java:line)"
            elif line.strip().startswith('at '):
                match = re.search(r'at\s+([^(]+)\(([^:]+\.java):(\d+)\)', line)
                if match:
                    frames.append({
                        'function': match.group(1),
                        'file': match.group(2),
                        'line': int(match.group(3))
                    })
        
        return {
            'frames': frames,
            'error_type': error_type,
            'error_message': error_message,
            'raw': error_text,
            'language': 'java'
        }
    
    @staticmethod
    def parse_traceback(error_text: str) -> Dict[str, Any]:
        """Parse error/traceback with language auto-detection."""
        language = ErrorContext.detect_language(error_text)
        
        if language == 'python':
            return ErrorContext.parse_python_traceback(error_text)
        elif language == 'javascript':
            return ErrorContext.parse_javascript_stack(error_text)
        elif language == 'go':
            return ErrorContext.parse_go_panic(error_text)
        elif language == 'rust':
            return ErrorContext.parse_rust_panic(error_text)
        elif language == 'java':
            return ErrorContext.parse_java_stack(error_text)
        else:
            return {'raw': error_text, 'language': 'unknown'}
    
    @staticmethod
    def format_for_ai(error_text: str) -> str:
        """Format error for AI consumption with language detection."""
        parsed = ErrorContext.parse_traceback(error_text)
        
        if 'error_type' not in parsed:
            return error_text
        
        language = parsed.get('language', 'unknown')
        parts = [
            f"Language: {language.title()}",
            f"Error Type: {parsed['error_type']}",
            f"Error Message: {parsed.get('error_message', 'N/A')}",
            "\nStack Trace:"
        ]
        
        for i, frame in enumerate(parsed.get('frames', []), 1):
            file_loc = f"{frame.get('file', 'unknown')}:{frame.get('line', '?')}"
            if 'column' in frame:
                file_loc += f":{frame.get('column', '?')}"
            parts.append(f"  {i}. {file_loc} in {frame.get('function', 'unknown')}")
            if 'code' in frame:
                parts.append(f"     > {frame['code']}")
        
        return "\n".join(parts)
    
    def gather(self, error_text: str) -> ContextItem:
        """Gather error context."""
        formatted = self.format_for_ai(error_text)
        parsed = self.parse_traceback(error_text)
        
        return ContextItem(
            type='error',
            content=formatted,
            metadata=parsed
        )


class ContextGatherer:
    """Main context gathering coordinator."""
    
    def __init__(self, project_root: Optional[Path] = None, max_file_lines: int = 1000, max_related_files: int = 5):
        self.project_root = project_root or Path.cwd()
        self.git = GitContext(self.project_root)
        self.dependencies = DependencyAnalyzer(self.project_root)
        self.error_parser = ErrorContext()
        self.max_file_lines = max_file_lines
        self.max_related_files = max_related_files
    
    def gather_for_file(
        self,
        file_path: Path,
        include_git: bool = True,
        include_dependencies: bool = True,
        include_related: bool = True,
        max_lines: Optional[int] = None
    ) -> Context:
        """Gather context for a specific file operation.
        
        Args:
            file_path: Path to the file to gather context for
            include_git: Include git context
            include_dependencies: Include dependency information
            include_related: Include related files
            max_lines: Maximum lines per file (uses instance default if None)
        """
        context = Context()
        max_lines = max_lines or self.max_file_lines
        
        # Add the file itself
        if file_path.exists():
            item = ContextItem(
                type='file',
                content=file_path.read_text(),
                metadata={'path': str(file_path)}
            )
            context.add(item.truncate(max_lines))
        
        # Add git context
        if include_git and self.git.is_git_repo():
            context.add(self.git.gather(include_diff=False))
        
        # Add dependency context
        if include_dependencies:
            context.add(self.dependencies.gather(target_file=file_path if include_related else None))
        
        return context
    
    def gather_for_error(
        self,
        error_text: str,
        file_path: Optional[Path] = None,
        include_git: bool = True,
        max_lines: Optional[int] = None
    ) -> Context:
        """Gather context for error debugging.
        
        Args:
            error_text: The error message or traceback
            file_path: Optional file path related to the error
            include_git: Include git context
            max_lines: Maximum lines per file (uses instance default if None)
        """
        context = Context()
        max_lines = max_lines or self.max_file_lines
        
        # Add error context
        context.add(self.error_parser.gather(error_text))
        
        # Add file if provided
        if file_path and file_path.exists():
            item = ContextItem(
                type='file',
                content=file_path.read_text(),
                metadata={'path': str(file_path)}
            )
            context.add(item.truncate(max_lines))
        
        # Add git context
        if include_git and self.git.is_git_repo():
            context.add(self.git.gather(include_diff=False))
        
        return context
    
    def gather_for_review(
        self,
        file_path: Path,
        include_git: bool = True,
        include_tests: bool = True,
        max_lines: Optional[int] = None
    ) -> Context:
        """Gather context for code review.
        
        Args:
            file_path: Path to the file to review
            include_git: Include git context
            include_tests: Try to find and include test files
            max_lines: Maximum lines per file (uses instance default if None)
        """
        context = self.gather_for_file(
            file_path,
            include_git=include_git,
            include_dependencies=True,
            include_related=True,
            max_lines=max_lines
        )
        
        max_lines = max_lines or self.max_file_lines
        
        # Try to find test file
        if include_tests:
            test_patterns = [
                self.project_root / "tests" / f"test_{file_path.name}",
                self.project_root / f"test_{file_path.name}",
                file_path.parent / f"test_{file_path.name}"
            ]
            
            for test_file in test_patterns:
                if test_file.exists():
                    item = ContextItem(
                        type='file',
                        content=test_file.read_text(),
                        metadata={'path': str(test_file), 'is_test': True}
                    )
                    context.add(item.truncate(max_lines))
                    break
        
        return context
    
