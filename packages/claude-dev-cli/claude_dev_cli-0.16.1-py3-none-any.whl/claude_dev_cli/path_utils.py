"""Path expansion and git change detection utilities."""

import subprocess
from pathlib import Path
from typing import List, Set, Optional

# Common code file extensions
CODE_EXTENSIONS = {
    '.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.rs', '.java', '.cpp', '.c',
    '.h', '.hpp', '.cs', '.rb', '.php', '.swift', '.kt', '.scala', '.r',
    '.m', '.mm', '.sh', '.bash', '.zsh', '.fish', '.lua', '.pl', '.sql',
    '.html', '.css', '.scss', '.sass', '.less', '.vue', '.svelte'
}


def is_code_file(path: Path) -> bool:
    """Check if file is a code file based on extension."""
    return path.suffix.lower() in CODE_EXTENSIONS


def expand_paths(
    paths: List[str],
    max_files: Optional[int] = None,
    recursive: bool = True
) -> List[Path]:
    """Expand paths (files, directories, globs) to list of code files.
    
    Args:
        paths: List of file/directory paths
        max_files: Maximum number of files to return (None = unlimited)
        recursive: Whether to recursively search directories
    
    Returns:
        List of Path objects for code files
    """
    result_files: Set[Path] = set()
    
    for path_str in paths:
        path = Path(path_str).resolve()
        
        if not path.exists():
            continue
        
        if path.is_file():
            # Add single file
            result_files.add(path)
        elif path.is_dir():
            # Expand directory
            if recursive:
                # Recursively find all code files
                for file_path in path.rglob('*'):
                    if file_path.is_file() and is_code_file(file_path):
                        result_files.add(file_path)
                        if max_files and len(result_files) >= max_files:
                            break
            else:
                # Only direct children
                for file_path in path.glob('*'):
                    if file_path.is_file() and is_code_file(file_path):
                        result_files.add(file_path)
                        if max_files and len(result_files) >= max_files:
                            break
        
        if max_files and len(result_files) >= max_files:
            break
    
    # Sort for consistent ordering
    return sorted(result_files)


def get_git_changes(
    staged_only: bool = False,
    include_untracked: bool = False,
    commit_range: Optional[str] = None
) -> List[Path]:
    """Get list of changed files from git.
    
    Args:
        staged_only: Only return staged files
        include_untracked: Include untracked files
        commit_range: Git commit range (e.g., "main..HEAD")
    
    Returns:
        List of Path objects for changed files
    """
    files: Set[Path] = set()
    
    try:
        if commit_range:
            # Get files changed in commit range
            result = subprocess.run(
                ['git', 'diff', '--name-only', commit_range],
                capture_output=True,
                text=True,
                check=True
            )
            for line in result.stdout.strip().split('\n'):
                if line:
                    path = Path(line)
                    if path.exists():
                        files.add(path)
        elif staged_only:
            # Get only staged files
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only'],
                capture_output=True,
                text=True,
                check=True
            )
            for line in result.stdout.strip().split('\n'):
                if line:
                    path = Path(line)
                    if path.exists():
                        files.add(path)
        else:
            # Get all modified files (staged + unstaged)
            result = subprocess.run(
                ['git', 'diff', '--name-only', 'HEAD'],
                capture_output=True,
                text=True,
                check=True
            )
            for line in result.stdout.strip().split('\n'):
                if line:
                    path = Path(line)
                    if path.exists():
                        files.add(path)
            
            if include_untracked:
                # Add untracked files
                result = subprocess.run(
                    ['git', 'ls-files', '--others', '--exclude-standard'],
                    capture_output=True,
                    text=True,
                    check=True
                )
                for line in result.stdout.strip().split('\n'):
                    if line:
                        path = Path(line)
                        if path.exists():
                            files.add(path)
    except subprocess.CalledProcessError:
        # Not a git repo or git command failed
        return []
    
    return sorted(files)


def auto_detect_files(cwd: Optional[Path] = None) -> List[Path]:
    """Auto-detect files to process based on git status.
    
    Priority:
    1. Staged files
    2. Modified files (staged + unstaged)
    3. All code files in current directory
    
    Returns:
        List of Path objects, empty list if none found
    """
    if cwd is None:
        cwd = Path.cwd()
    
    # Try staged files first
    files = get_git_changes(staged_only=True)
    if files:
        return files
    
    # Try all modified files
    files = get_git_changes(staged_only=False)
    if files:
        return files
    
    # Fallback: all code files in current directory (non-recursive)
    return expand_paths([str(cwd)], recursive=False)
