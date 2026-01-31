"""Multi-file handler for parsing and applying AI-generated file changes."""

import re
import difflib
from pathlib import Path
from typing import List, Tuple, Optional, Literal, Dict, Any
from dataclasses import dataclass, field
from rich.console import Console
from rich.tree import Tree
from rich.panel import Panel
from rich.syntax import Syntax
from io import StringIO

try:
    from unidiff import PatchSet
    UNIDIFF_AVAILABLE = True
except ImportError:
    UNIDIFF_AVAILABLE = False


@dataclass
class HunkWrapper:
    """Wrapper around unidiff.Hunk with approval state."""
    hunk: Any  # unidiff.Hunk
    approved: bool = False
    
    @property
    def source_start(self) -> int:
        """Get source start line number."""
        return self.hunk.source_start if hasattr(self.hunk, 'source_start') else 0
    
    @property
    def source_length(self) -> int:
        """Get source length."""
        return self.hunk.source_length if hasattr(self.hunk, 'source_length') else 0
    
    @property
    def target_start(self) -> int:
        """Get target start line number."""
        return self.hunk.target_start if hasattr(self.hunk, 'target_start') else 0
    
    @property
    def target_length(self) -> int:
        """Get target length."""
        return self.hunk.target_length if hasattr(self.hunk, 'target_length') else 0
    
    def __str__(self) -> str:
        """Format hunk as unified diff text."""
        return str(self.hunk)


@dataclass
class FileChange:
    """Represents a single file change."""
    path: str
    content: str
    change_type: Literal["create", "modify", "delete"]
    original_content: Optional[str] = None
    hunks: List[HunkWrapper] = field(default_factory=list)
    
    @property
    def line_count(self) -> int:
        """Count lines in content."""
        return len(self.content.splitlines()) if self.content else 0
    
    @property
    def diff(self) -> Optional[str]:
        """Generate unified diff for modifications."""
        if self.change_type != "modify" or not self.original_content:
            return None
        
        original_lines = self.original_content.splitlines(keepends=True)
        new_lines = self.content.splitlines(keepends=True)
        
        diff_lines = list(difflib.unified_diff(
            original_lines,
            new_lines,
            fromfile=f"a/{self.path}",
            tofile=f"b/{self.path}"
        ))
        
        return ''.join(diff_lines) if diff_lines else None
    
    def parse_hunks(self) -> None:
        """Parse diff into individual hunks using unidiff library."""
        if self.change_type != "modify" or not self.diff:
            return
        
        if not UNIDIFF_AVAILABLE:
            # Fallback: no hunk parsing available
            self.hunks = []
            return
        
        self.hunks = []
        
        try:
            # Parse the diff with unidiff
            patch = PatchSet(StringIO(self.diff))
            
            # Extract all hunks from all patched files
            for patched_file in patch:
                for hunk in patched_file:
                    self.hunks.append(HunkWrapper(hunk=hunk, approved=False))
                    
        except Exception:
            # If unidiff fails, fall back to empty hunks list
            self.hunks = []
    
    def apply_approved_hunks(self) -> str:
        """Apply only approved hunks using unidiff's line access methods."""
        if self.change_type != "modify" or not self.original_content:
            return self.content
        
        # If no hunks parsed, caller decides what to do
        # In write_all, we check if hunks exist before calling this
        if not self.hunks:
            return self.content
        
        # If no hunks approved, return original
        if not any(h.approved for h in self.hunks):
            return self.original_content
        
        # If all hunks approved, return new content
        if all(h.approved for h in self.hunks):
            return self.content
        
        # Apply only approved hunks
        original_lines = self.original_content.splitlines(keepends=True)
        result_lines = original_lines.copy()
        
        # Sort hunks by position (reversed for bottom-up application)
        sorted_hunks = sorted(
            [h for h in self.hunks if h.approved],
            key=lambda h: h.source_start,
            reverse=True
        )
        
        for wrapper in sorted_hunks:
            hunk = wrapper.hunk
            
            # Calculate indices for replacement
            start_idx = wrapper.source_start - 1
            end_idx = start_idx + wrapper.source_length
            
            # Extract new lines using unidiff's line iteration
            new_lines = []
            for line in hunk:
                if line.is_added or line.is_context:
                    # Get line value (already includes newline)
                    new_lines.append(line.value)
            
            # Replace section
            result_lines[start_idx:end_idx] = new_lines
        
        return ''.join(result_lines)


class MultiFileResponse:
    """Parses and handles multi-file AI responses."""
    
    def __init__(self):
        self.files: List[FileChange] = []
    
    def parse_response(self, text: str, base_path: Optional[Path] = None) -> None:
        """Parse AI response to extract file changes.
        
        Supports formats:
        - ## File: path/to/file.ext
        - ## Create: path/to/file.ext
        - ## Modify: path/to/file.ext  
        - ## Delete: path/to/file.ext
        
        Args:
            text: AI response text
            base_path: Base directory to check for existing files (for modifications)
        """
        self.files = []
        
        # Pattern to match file markers and code blocks
        # Matches: ## File: path or ## Create: path or ## Modify: path or ## Delete: path
        file_pattern = r'^##\s+(File|Create|Modify|Delete):\s*(.+?)$'
        code_block_pattern = r'```(\w+)?\n(.*?)```'
        
        lines = text.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            match = re.match(file_pattern, line, re.IGNORECASE)
            
            if match:
                action = match.group(1).lower()
                file_path = match.group(2).strip()
                
                # Map actions to change types
                if action in ('file', 'create'):
                    change_type = 'create'
                elif action == 'modify':
                    change_type = 'modify'
                elif action == 'delete':
                    change_type = 'delete'
                else:
                    change_type = 'create'
                
                # For delete, no content needed
                if change_type == 'delete':
                    self.files.append(FileChange(
                        path=file_path,
                        content='',
                        change_type='delete'
                    ))
                    i += 1
                    continue
                
                # Extract code block following the file marker
                remaining_text = '\n'.join(lines[i+1:])
                code_match = re.search(code_block_pattern, remaining_text, re.DOTALL)
                
                if code_match:
                    content = code_match.group(2).strip()
                    
                    # Check if file exists for modifications
                    original_content = None
                    if change_type == 'modify' and base_path:
                        file_full_path = base_path / file_path
                        if file_full_path.exists():
                            original_content = file_full_path.read_text()
                            change_type = 'modify'
                        else:
                            # File doesn't exist, treat as create
                            change_type = 'create'
                    
                    self.files.append(FileChange(
                        path=file_path,
                        content=content,
                        change_type=change_type,
                        original_content=original_content
                    ))
                    
                    # Skip past the code block
                    lines_used = code_match.group(0).count('\n')
                    i += lines_used + 1
                else:
                    # No code block found, skip this line
                    i += 1
            else:
                i += 1
    
    def validate_paths(self, base_path: Path) -> List[str]:
        """Validate file paths for security.
        
        Returns list of validation errors, empty if all valid.
        """
        errors = []
        base_path = base_path.resolve()
        
        for file_change in self.files:
            # Check for absolute paths
            if Path(file_change.path).is_absolute():
                errors.append(f"Absolute path not allowed: {file_change.path}")
                continue
            
            # Resolve the path
            try:
                full_path = (base_path / file_change.path).resolve()
                
                # Check if resolved path is within base_path
                if not str(full_path).startswith(str(base_path)):
                    errors.append(f"Path traversal detected: {file_change.path}")
                    
            except Exception as e:
                errors.append(f"Invalid path {file_change.path}: {str(e)}")
        
        return errors
    
    def build_tree(self, base_path: Path) -> str:
        """Generate visual directory tree.
        
        Returns formatted tree string with colors and status indicators.
        """
        if not self.files:
            return "No files"
        
        # Build tree structure
        tree = Tree(f"[bold cyan]{base_path.name or base_path}/[/bold cyan]")
        
        # Group files by directory
        dirs = {}
        for file_change in self.files:
            parts = Path(file_change.path).parts
            current = dirs
            
            for i, part in enumerate(parts[:-1]):
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            # Store file info at leaf
            filename = parts[-1]
            current[filename] = file_change
        
        def add_to_tree(node, items):
            """Recursively add items to tree."""
            for name, value in sorted(items.items()):
                if isinstance(value, dict):
                    # Directory
                    branch = node.add(f"[bold blue]{name}/[/bold blue]")
                    add_to_tree(branch, value)
                elif isinstance(value, FileChange):
                    # File
                    if value.change_type == 'create':
                        status = "[green](new)[/green]"
                    elif value.change_type == 'modify':
                        status = "[yellow](modified)[/yellow]"
                    elif value.change_type == 'delete':
                        status = "[red](deleted)[/red]"
                    else:
                        status = ""
                    
                    lines = f"{value.line_count} lines" if value.line_count > 0 else ""
                    node.add(f"{name} {status} [dim]{lines}[/dim]")
        
        add_to_tree(tree, dirs)
        
        return tree
    
    def preview(self, console: Console, base_path: Path) -> None:
        """Show formatted preview with tree and summary."""
        if not self.files:
            console.print("[yellow]No files to change[/yellow]")
            return
        
        # Show tree
        console.print("\n[bold]File Structure:[/bold]")
        console.print(self.build_tree(base_path))
        
        # Summary
        creates = sum(1 for f in self.files if f.change_type == 'create')
        modifies = sum(1 for f in self.files if f.change_type == 'modify')
        deletes = sum(1 for f in self.files if f.change_type == 'delete')
        total_lines = sum(f.line_count for f in self.files)
        
        summary_parts = []
        if creates:
            summary_parts.append(f"[green]{creates} created[/green]")
        if modifies:
            summary_parts.append(f"[yellow]{modifies} modified[/yellow]")
        if deletes:
            summary_parts.append(f"[red]{deletes} deleted[/red]")
        
        summary = ", ".join(summary_parts)
        console.print(f"\n[bold]Summary:[/bold] {summary} ({total_lines} total lines)\n")
    
    def write_all(self, base_path: Path, dry_run: bool = False, console: Optional[Console] = None) -> None:
        """Write all file changes to disk.
        
        Args:
            base_path: Base directory for file operations
            dry_run: If True, don't actually write files
            console: Rich console for output
        """
        if console is None:
            console = Console()
        
        base_path = base_path.resolve()
        base_path.mkdir(parents=True, exist_ok=True)
        
        for file_change in self.files:
            # Skip files marked for skipping
            if hasattr(file_change, 'change_type') and file_change.change_type == 'skip':
                continue
            
            # Skip empty content for create (marked as rejected)
            if file_change.change_type == 'create' and not file_change.content:
                continue
            
            full_path = base_path / file_change.path
            
            if dry_run:
                if file_change.change_type == 'create':
                    console.print(f"[dim]Would create: {file_change.path}[/dim]")
                elif file_change.change_type == 'modify':
                    if file_change.hunks and any(h.approved for h in file_change.hunks):
                        approved_count = sum(1 for h in file_change.hunks if h.approved)
                        console.print(f"[dim]Would modify: {file_change.path} ({approved_count}/{len(file_change.hunks)} hunks)[/dim]")
                    else:
                        console.print(f"[dim]Would modify: {file_change.path}[/dim]")
                elif file_change.change_type == 'delete':
                    console.print(f"[dim]Would delete: {file_change.path}[/dim]")
                continue
            
            # Actual file operations
            if file_change.change_type == 'delete':
                if full_path.exists():
                    full_path.unlink()
                    console.print(f"[red]✗[/red] Deleted: {file_change.path}")
            else:
                # Create parent directories
                full_path.parent.mkdir(parents=True, exist_ok=True)
                
                # For modify with hunks, apply only approved hunks
                if file_change.change_type == 'modify' and file_change.hunks:
                    # Only write if at least one hunk is approved
                    if not any(h.approved for h in file_change.hunks):
                        console.print(f"[dim]Skipped: {file_change.path} (no hunks approved)[/dim]")
                        continue
                    
                    content_to_write = file_change.apply_approved_hunks()
                    full_path.write_text(content_to_write)
                    approved_count = sum(1 for h in file_change.hunks if h.approved)
                    console.print(f"[yellow]✓[/yellow] Modified: {file_change.path} ({approved_count}/{len(file_change.hunks)} hunks)")
                else:
                    # Write file normally (no hunks or create operation)
                    full_path.write_text(file_change.content)
                    
                    if file_change.change_type == 'create':
                        console.print(f"[green]✓[/green] Created: {file_change.path}")
                    elif file_change.change_type == 'modify':
                        console.print(f"[yellow]✓[/yellow] Modified: {file_change.path}")
    
    def confirm(self, console: Console, base_path: Optional[Path] = None) -> bool:
        """Interactive confirmation prompt.
        
        Args:
            console: Rich console for output
            base_path: Base directory for file operations (needed for edit/save)
        
        Returns True if user confirms, False otherwise.
        """
        if not self.files:
            return False
        
        while True:
            response = console.input("\n[cyan]Continue?[/cyan] [dim](Y/n/preview/patch/edit/save/help)[/dim] ").strip().lower()
            
            if response in ('y', 'yes', ''):
                return True
            elif response in ('n', 'no'):
                return False
            elif response == 'patch':
                # Use hunk-by-hunk confirmation
                return self.confirm_with_hunks(console)
            elif response == 'edit':
                # Open files in editor for manual editing
                if base_path:
                    self._edit_files(console, base_path)
                else:
                    console.print("[red]Edit not available (no base path provided)[/red]")
            elif response == 'save':
                # Save to custom location
                if base_path:
                    return self._save_to_location(console, base_path)
                else:
                    console.print("[red]Save not available (no base path provided)[/red]")
            elif response == 'preview':
                # Show individual file contents
                for i, file_change in enumerate(self.files, 1):
                    console.print(f"\n[bold]File {i}/{len(self.files)}:[/bold] {file_change.path}")
                    
                    if file_change.change_type == 'delete':
                        console.print("[red]This file will be deleted[/red]")
                    elif file_change.change_type == 'modify' and file_change.diff:
                        console.print("[yellow]Diff:[/yellow]")
                        console.print(Panel(file_change.diff, border_style="yellow"))
                    else:
                        preview = file_change.content[:500]
                        if len(file_change.content) > 500:
                            preview += "\n... (truncated)"
                        console.print(Panel(preview, border_style="green"))
            elif response == 'help':
                console.print("""
[bold]Options:[/bold]
  y, yes    - Proceed with all changes
  n, no     - Cancel all changes
  patch     - Review changes hunk-by-hunk (like git add -p)
  edit      - Open files in $EDITOR before applying
  save      - Save to custom location/filename
  preview   - Show file contents/diffs
  help      - Show this help
""")
            else:
                console.print("[red]Invalid response. Type 'help' for options.[/red]")
    
    def confirm_with_hunks(self, console: Console) -> bool:
        """Interactive hunk-by-hunk confirmation (like git add -p).
        
        Returns True if at least some changes approved, False if all cancelled.
        """
        if not self.files:
            return False
        
        # Parse hunks for all modify operations
        for file_change in self.files:
            if file_change.change_type == 'modify':
                file_change.parse_hunks()
        
        has_any_approval = False
        
        for file_change in self.files:
            console.print(f"\n[bold cyan]File:[/bold cyan] {file_change.path}")
            
            if file_change.change_type == 'create':
                console.print(f"[green]Create new file ({file_change.line_count} lines)[/green]")
                response = self._ask_file_action(console, "create")
                if response == 'y':
                    # Mark as approved (keep as-is)
                    has_any_approval = True
                elif response == 'n':
                    # Remove from files list
                    file_change.content = ''  # Mark for skip
                elif response == 'q':
                    return has_any_approval
                    
            elif file_change.change_type == 'delete':
                console.print("[red]Delete file[/red]")
                response = self._ask_file_action(console, "delete")
                if response == 'y':
                    has_any_approval = True
                elif response == 'n':
                    file_change.change_type = 'skip'  # Mark for skip
                elif response == 'q':
                    return has_any_approval
                    
            elif file_change.change_type == 'modify':
                if not file_change.hunks:
                    console.print("[yellow]No hunks to review[/yellow]")
                    continue
                
                console.print(f"[yellow]Modify file ({len(file_change.hunks)} hunk(s))[/yellow]")
                
                for hunk_idx, hunk in enumerate(file_change.hunks, 1):
                    console.print(f"\n[bold]Hunk {hunk_idx}/{len(file_change.hunks)}:[/bold]")
                    
                    # Show hunk with syntax highlighting
                    hunk_text = str(hunk)
                    console.print(Panel(
                        Syntax(hunk_text, "diff", theme="monokai", line_numbers=False),
                        border_style="yellow",
                        title=f"[bold]{file_change.path}[/bold]"
                    ))
                    
                    while True:
                        response = console.input(
                            "[cyan]Apply this hunk?[/cyan] [dim](y/n/s=skip file/q=quit/help)[/dim] "
                        ).strip().lower()
                        
                        if response in ('y', 'yes', ''):
                            hunk.approved = True
                            has_any_approval = True
                            break
                        elif response in ('n', 'no'):
                            hunk.approved = False
                            break
                        elif response in ('s', 'skip'):
                            # Skip remaining hunks in this file
                            break
                        elif response in ('q', 'quit'):
                            return has_any_approval
                        elif response == 'help':
                            console.print("""
[bold]Hunk Options:[/bold]
  y, yes   - Apply this hunk
  n, no    - Skip this hunk
  s, skip  - Skip remaining hunks in this file
  q, quit  - Quit and apply approved hunks so far
  help     - Show this help
""")
                        else:
                            console.print("[red]Invalid response. Type 'help' for options.[/red]")
                    
                    if response in ('s', 'skip'):
                        break
        
        return has_any_approval
    
    def _ask_file_action(self, console: Console, action: str) -> str:
        """Ask for confirmation on file-level action.
        
        Returns: 'y' (yes), 'n' (no), 's' (skip), 'q' (quit)
        """
        while True:
            response = console.input(
                f"[cyan]{action.capitalize()} this file?[/cyan] [dim](y/n/s=skip/q=quit)[/dim] "
            ).strip().lower()
            
            if response in ('y', 'yes', 'n', 'no', 's', 'skip', 'q', 'quit', ''):
                if response == '':
                    return 'y'
                if response in ('skip',):
                    return 's'
                if response in ('quit',):
                    return 'q'
                return response[0]  # Return first character
            else:
                console.print("[red]Invalid response. Use y/n/s/q[/red]")
    
    def _edit_files(self, console: Console, base_path: Path) -> None:
        """Open files in editor for manual editing before applying.
        
        Args:
            console: Rich console for output
            base_path: Base directory for file operations
        """
        import os
        import subprocess
        import tempfile
        
        editor = os.environ.get('EDITOR', 'vi')
        
        console.print(f"\n[cyan]Opening files in {editor}...[/cyan]")
        console.print("[dim]Save and close editor to continue[/dim]\n")
        
        for file_change in self.files:
            if file_change.change_type == 'delete':
                console.print(f"[dim]Skipping delete operation: {file_change.path}[/dim]")
                continue
            
            # Write content to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix=f'_{Path(file_change.path).name}', delete=False) as tf:
                tf.write(file_change.content)
                temp_path = tf.name
            
            try:
                console.print(f"[bold]Editing:[/bold] {file_change.path}")
                
                # Open in editor
                result = subprocess.run([editor, temp_path])
                
                if result.returncode == 0:
                    # Read edited content
                    with open(temp_path, 'r') as f:
                        edited_content = f.read()
                    
                    # Update file change with edited content
                    file_change.content = edited_content
                    console.print(f"[green]✓[/green] Updated: {file_change.path}")
                else:
                    console.print(f"[yellow]Editor exited with error, keeping original content[/yellow]")
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_path)
                except:
                    pass
        
        console.print("\n[green]Editing complete![/green]")
    
    def _save_to_location(self, console: Console, base_path: Path) -> bool:
        """Save files to custom location.
        
        Args:
            console: Rich console for output
            base_path: Base directory for file operations
        
        Returns: True if saved successfully, False otherwise
        """
        console.print("\n[cyan]Save options:[/cyan]")
        
        if len(self.files) == 1:
            # Single file - ask for filename
            console.print("[dim]Enter filename (or path) to save to:[/dim]")
            filename = console.input("[cyan]Filename:[/cyan] ").strip()
            
            if not filename:
                console.print("[yellow]Cancelled[/yellow]")
                return False
            
            save_path = Path(filename)
            if not save_path.is_absolute():
                save_path = base_path / save_path
            
            # Create parent directories
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            file_change = self.files[0]
            save_path.write_text(file_change.content)
            console.print(f"[green]✓[/green] Saved to: {save_path}")
            return False  # Don't continue with original write
        else:
            # Multiple files - ask for directory
            console.print(f"[dim]Enter directory to save {len(self.files)} file(s) to:[/dim]")
            dirname = console.input("[cyan]Directory:[/cyan] ").strip()
            
            if not dirname:
                console.print("[yellow]Cancelled[/yellow]")
                return False
            
            save_dir = Path(dirname)
            if not save_dir.is_absolute():
                save_dir = base_path / save_dir
            
            # Create directory
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # Write all files
            for file_change in self.files:
                if file_change.change_type == 'delete':
                    console.print(f"[dim]Skipping delete operation: {file_change.path}[/dim]")
                    continue
                
                file_path = save_dir / file_change.path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(file_change.content)
                console.print(f"[green]✓[/green] Saved: {file_path}")
            
            console.print(f"\n[green]All files saved to: {save_dir}[/green]")
            return False  # Don't continue with original write


def extract_code_blocks(text: str) -> List[Tuple[str, str, str]]:
    """Extract code blocks from markdown text.
    
    Returns list of (file_marker, language, code) tuples.
    """
    pattern = r'^##\s+(File|Create|Modify|Delete):\s*(.+?)$.*?```(\w+)?\n(.*?)```'
    matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
    
    results = []
    for match in matches:
        action = match[0]
        path = match[1].strip()
        language = match[2] if match[2] else ''
        code = match[3].strip()
        results.append((f"{action}: {path}", language, code))
    
    return results


def count_lines(content: str) -> int:
    """Count non-empty lines in content."""
    return len([line for line in content.splitlines() if line.strip()])
