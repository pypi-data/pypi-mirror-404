"""
VibeDNA CLI Formatters

Output formatting utilities for the command-line interface.

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
"""

from typing import List, Any, Optional
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.tree import Tree


console = Console()


@dataclass
class FormatOptions:
    """Formatting options."""
    color: bool = True
    wrap_width: int = 80
    show_headers: bool = True
    style: str = "default"


def format_dna_sequence(
    sequence: str,
    wrap_width: int = 80,
    colorize: bool = True,
    show_position: bool = True
) -> str:
    """
    Format DNA sequence for display.

    Args:
        sequence: DNA sequence
        wrap_width: Characters per line
        colorize: Whether to add color
        show_position: Whether to show position numbers

    Returns:
        Formatted sequence string
    """
    lines = []
    position = 0

    # Color mapping
    colors = {
        "A": "[red]A[/red]",
        "T": "[green]T[/green]",
        "C": "[blue]C[/blue]",
        "G": "[yellow]G[/yellow]",
    }

    for i in range(0, len(sequence), wrap_width):
        chunk = sequence[i:i + wrap_width]

        if colorize:
            colored_chunk = "".join(colors.get(n, n) for n in chunk.upper())
        else:
            colored_chunk = chunk

        if show_position:
            line = f"{position + 1:>8}  {colored_chunk}"
        else:
            line = colored_chunk

        lines.append(line)
        position += wrap_width

    return "\n".join(lines)


def format_file_info(file_info: dict) -> Panel:
    """
    Format file information as a panel.

    Args:
        file_info: Dictionary with file information

    Returns:
        Rich Panel object
    """
    content = "\n".join([
        f"[cyan]Name:[/cyan]     {file_info.get('name', 'Unknown')}",
        f"[cyan]Path:[/cyan]     {file_info.get('path', '/')}",
        f"[cyan]Size:[/cyan]     {file_info.get('original_size', 0):,} bytes",
        f"[cyan]DNA:[/cyan]      {file_info.get('dna_length', 0):,} nucleotides",
        f"[cyan]MIME:[/cyan]     {file_info.get('mime_type', 'unknown')}",
        f"[cyan]Scheme:[/cyan]   {file_info.get('encoding_scheme', 'quaternary')}",
        f"[cyan]Created:[/cyan]  {file_info.get('created_at', 'Unknown')}",
    ])

    return Panel(content, title="File Information")


def format_stats_table(stats: dict, title: str = "Statistics") -> Table:
    """
    Format statistics as a table.

    Args:
        stats: Dictionary of statistics
        title: Table title

    Returns:
        Rich Table object
    """
    table = Table(title=title)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")

    for key, value in stats.items():
        if isinstance(value, float):
            formatted_value = f"{value:.4f}"
        elif isinstance(value, int):
            formatted_value = f"{value:,}"
        else:
            formatted_value = str(value)

        table.add_row(key.replace("_", " ").title(), formatted_value)

    return table


def format_encoding_comparison(schemes: List[dict]) -> Table:
    """
    Format encoding scheme comparison.

    Args:
        schemes: List of scheme information dictionaries

    Returns:
        Rich Table object
    """
    table = Table(title="Encoding Schemes Comparison")

    table.add_column("Scheme", style="cyan")
    table.add_column("Bits/nt", justify="right")
    table.add_column("GC Balanced", justify="center")
    table.add_column("Homopolymer Safe", justify="center")
    table.add_column("Error Tolerance", justify="center")

    for scheme in schemes:
        table.add_row(
            scheme["name"],
            f"{scheme['bits_per_nucleotide']:.2f}",
            "✓" if scheme["gc_balanced"] else "✗",
            "✓" if scheme["homopolymer_safe"] else "✗",
            scheme["error_tolerance"],
        )

    return table


def format_directory_tree(root_path: str, contents: List[Any]) -> Tree:
    """
    Format directory contents as a tree.

    Args:
        root_path: Root directory path
        contents: List of files and directories

    Returns:
        Rich Tree object
    """
    tree = Tree(f"[bold]{root_path}[/bold]")

    for item in contents:
        if hasattr(item, "dna_sequence"):
            # It's a file
            size_str = f"({item.original_size:,} bytes)"
            tree.add(f"📄 [green]{item.name}[/green] {size_str}")
        else:
            # It's a directory
            tree.add(f"📁 [cyan]{item.name}/[/cyan]")

    return tree


def format_error(message: str, details: Optional[str] = None) -> Panel:
    """
    Format an error message.

    Args:
        message: Main error message
        details: Optional additional details

    Returns:
        Rich Panel object
    """
    content = f"[red]✗ {message}[/red]"
    if details:
        content += f"\n\n[dim]{details}[/dim]"

    return Panel(content, title="Error", border_style="red")


def format_success(message: str, details: Optional[str] = None) -> Panel:
    """
    Format a success message.

    Args:
        message: Main success message
        details: Optional additional details

    Returns:
        Rich Panel object
    """
    content = f"[green]✓ {message}[/green]"
    if details:
        content += f"\n\n{details}"

    return Panel(content, title="Success", border_style="green")


def format_warning(message: str, details: Optional[str] = None) -> Panel:
    """
    Format a warning message.

    Args:
        message: Main warning message
        details: Optional additional details

    Returns:
        Rich Panel object
    """
    content = f"[yellow]⚠ {message}[/yellow]"
    if details:
        content += f"\n\n{details}"

    return Panel(content, title="Warning", border_style="yellow")


def format_json_output(data: dict) -> Syntax:
    """
    Format JSON output with syntax highlighting.

    Args:
        data: Dictionary to format as JSON

    Returns:
        Rich Syntax object
    """
    import json
    json_str = json.dumps(data, indent=2)
    return Syntax(json_str, "json", theme="monokai")


# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
