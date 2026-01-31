"""
Utility functions for S3Hero.

Includes formatters, progress bars, and helper functions.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator, List, Optional, Tuple

import humanize
from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree


console = Console()


def format_size(size_bytes: int) -> str:
    """Format bytes to human-readable size."""
    return humanize.naturalsize(size_bytes, binary=True)


def format_date(dt: datetime) -> str:
    """Format datetime to human-readable string."""
    return humanize.naturaltime(dt)


def format_date_full(dt: datetime) -> str:
    """Format datetime to full string."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def truncate_string(s: str, max_length: int = 50) -> str:
    """Truncate string with ellipsis."""
    if len(s) <= max_length:
        return s
    return s[:max_length - 3] + "..."


class ProgressCallback:
    """Callback class for boto3 upload/download progress."""
    
    def __init__(
        self,
        progress: Progress,
        task_id: TaskID,
        total_size: int
    ):
        self.progress = progress
        self.task_id = task_id
        self.total_size = total_size
        self._seen = 0

    def __call__(self, bytes_amount: int) -> None:
        self._seen += bytes_amount
        self.progress.update(self.task_id, completed=self._seen)


def create_progress_bar() -> Progress:
    """Create a rich progress bar for file transfers."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console,
    )


def create_simple_progress() -> Progress:
    """Create a simple progress bar for counting operations."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("({task.completed}/{task.total})"),
        console=console,
    )


def create_bucket_table(buckets: List[Any]) -> Table:
    """Create a table for displaying buckets."""
    table = Table(
        title="S3 Buckets",
        show_header=True,
        header_style="bold magenta"
    )
    
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Created", style="green")
    
    for bucket in buckets:
        table.add_row(
            bucket.name,
            format_date_full(bucket.creation_date)
        )
    
    return table


def create_objects_table(objects: List[Any], show_size: bool = True) -> Table:
    """Create a table for displaying objects."""
    table = Table(
        show_header=True,
        header_style="bold magenta"
    )
    
    table.add_column("Key", style="cyan")
    if show_size:
        table.add_column("Size", style="yellow", justify="right")
    table.add_column("Last Modified", style="green")
    table.add_column("Storage Class", style="blue")
    
    for obj in objects:
        row = [truncate_string(obj.key, 60)]
        if show_size:
            row.append(format_size(obj.size))
        row.extend([
            format_date(obj.last_modified),
            obj.storage_class or "STANDARD"
        ])
        table.add_row(*row)
    
    return table


def create_object_tree(objects: List[Any], bucket_name: str) -> Tree:
    """Create a tree view of objects."""
    tree = Tree(f"[bold cyan]s3://{bucket_name}/[/bold cyan]")
    
    # Build directory structure
    dirs: dict = {}
    
    for obj in objects:
        parts = obj.key.split('/')
        current = dirs
        
        for i, part in enumerate(parts[:-1]):
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Add file
        filename = parts[-1]
        if filename:
            current[filename] = obj
    
    def add_to_tree(node: Tree, items: dict) -> None:
        for name, value in sorted(items.items()):
            if isinstance(value, dict):
                folder = node.add(f"[bold blue]📁 {name}/[/bold blue]")
                add_to_tree(folder, value)
            else:
                size = format_size(value.size)
                node.add(f"📄 {name} [dim]({size})[/dim]")
    
    add_to_tree(tree, dirs)
    return tree


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[bold green]✓[/bold green] {message}")


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[bold red]✗[/bold red] {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[bold yellow]⚠[/bold yellow] {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[bold blue]ℹ[/bold blue] {message}")


def confirm_action(message: str, default: bool = False) -> bool:
    """Ask for confirmation."""
    from rich.prompt import Confirm
    return Confirm.ask(message, default=default)


def print_stats(stats: dict, title: str = "Statistics") -> None:
    """Print statistics in a panel."""
    content = "\n".join(
        f"[bold]{key}:[/bold] {value}"
        for key, value in stats.items()
    )
    console.print(Panel(content, title=title, border_style="cyan"))


def walk_directory(
    path: str,
    include_hidden: bool = False
) -> Iterator[Tuple[str, int]]:
    """Walk a directory and yield (relative_path, size) tuples."""
    base_path = Path(path)
    
    for file_path in base_path.rglob('*'):
        if file_path.is_file():
            # Skip hidden files unless requested
            if not include_hidden:
                parts = file_path.relative_to(base_path).parts
                if any(part.startswith('.') for part in parts):
                    continue
            
            relative = str(file_path.relative_to(base_path))
            size = file_path.stat().st_size
            yield relative, size


def get_file_count(path: str, include_hidden: bool = False) -> int:
    """Count files in a directory."""
    return sum(1 for _ in walk_directory(path, include_hidden))


def calculate_directory_size(path: str, include_hidden: bool = False) -> int:
    """Calculate total size of a directory."""
    return sum(size for _, size in walk_directory(path, include_hidden))


def parse_s3_uri(uri: str) -> Tuple[str, str]:
    """
    Parse an S3 URI into bucket and key.
    
    Examples:
        s3://bucket/key -> ('bucket', 'key')
        bucket/key -> ('bucket', 'key')
    """
    if uri.startswith('s3://'):
        uri = uri[5:]
    
    parts = uri.split('/', 1)
    bucket = parts[0]
    key = parts[1] if len(parts) > 1 else ''
    
    return bucket, key


def build_s3_uri(bucket: str, key: str = "") -> str:
    """Build an S3 URI from bucket and key."""
    if key:
        return f"s3://{bucket}/{key}"
    return f"s3://{bucket}"


def validate_bucket_name(name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate S3 bucket name.
    
    Returns (is_valid, error_message).
    """
    if len(name) < 3:
        return False, "Bucket name must be at least 3 characters"
    
    if len(name) > 63:
        return False, "Bucket name must be at most 63 characters"
    
    if not name[0].isalnum():
        return False, "Bucket name must start with a letter or number"
    
    if not name[-1].isalnum():
        return False, "Bucket name must end with a letter or number"
    
    allowed = set('abcdefghijklmnopqrstuvwxyz0123456789-.')
    if not set(name.lower()).issubset(allowed):
        return False, "Bucket name can only contain lowercase letters, numbers, hyphens, and periods"
    
    if '..' in name:
        return False, "Bucket name cannot contain consecutive periods"
    
    if '-.' in name or '.-' in name:
        return False, "Bucket name cannot contain period adjacent to hyphen"
    
    # Check if it looks like an IP address
    parts = name.split('.')
    if len(parts) == 4:
        if all(part.isdigit() for part in parts):
            return False, "Bucket name cannot be formatted as an IP address"
    
    return True, None


def get_content_type(filename: str) -> str:
    """Get content type based on file extension."""
    import mimetypes
    content_type, _ = mimetypes.guess_type(filename)
    return content_type or 'application/octet-stream'
