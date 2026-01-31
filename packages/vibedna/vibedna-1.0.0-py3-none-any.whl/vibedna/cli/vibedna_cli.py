"""
VibeDNA Command Line Interface

Full-featured CLI for DNA encoding/decoding and file management.

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

BANNER = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║     ██╗   ██╗██╗██████╗ ███████╗██████╗ ███╗   ██╗ █████╗    ║
║     ██║   ██║██║██╔══██╗██╔════╝██╔══██╗████╗  ██║██╔══██╗   ║
║     ██║   ██║██║██████╔╝█████╗  ██║  ██║██╔██╗ ██║███████║   ║
║     ╚██╗ ██╔╝██║██╔══██╗██╔══╝  ██║  ██║██║╚██╗██║██╔══██║   ║
║      ╚████╔╝ ██║██████╔╝███████╗██████╔╝██║ ╚████║██║  ██║   ║
║       ╚═══╝  ╚═╝╚═════╝ ╚══════╝╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝   ║
║                                                               ║
║          Where Digital Meets Biological                       ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"""

COPYRIGHT = "© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC."


def print_banner():
    """Print the VibeDNA banner."""
    console.print(BANNER, style="cyan")
    console.print(f"    {COPYRIGHT}\n", style="dim")


@click.group()
@click.version_option(version="1.0.0", prog_name="VibeDNA")
@click.option("--quiet", "-q", is_flag=True, help="Suppress banner and verbose output")
@click.pass_context
def cli(ctx, quiet):
    """VibeDNA - Binary ↔ DNA Encoding System

    Convert files to DNA sequences, perform computations on DNA,
    and manage files in a DNA-based virtual file system.
    """
    ctx.ensure_object(dict)
    ctx.obj["quiet"] = quiet

    if not quiet:
        print_banner()


# ═══════════════════════════════════════════════════════════════
# ENCODING COMMANDS
# ═══════════════════════════════════════════════════════════════

@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("-o", "--output", type=click.Path(), help="Output file path")
@click.option("-s", "--scheme",
              type=click.Choice(["quaternary", "balanced_gc", "rll", "triplet"]),
              default="quaternary", help="Encoding scheme")
@click.option("-e", "--error-correction/--no-error-correction",
              default=True, help="Enable Reed-Solomon error correction")
@click.option("-f", "--format",
              type=click.Choice(["fasta", "raw", "json"]),
              default="fasta", help="Output format")
@click.pass_context
def encode(ctx, input_file, output, scheme, error_correction, format):
    """
    Encode a file to DNA sequence.

    Examples:

        vibedna encode document.pdf

        vibedna encode image.png -o image.dna -s balanced_gc

        vibedna encode data.bin --scheme triplet --format fasta
    """
    from vibedna.core.encoder import DNAEncoder, EncodingConfig, EncodingScheme

    input_path = Path(input_file)

    # Determine output path
    if output:
        output_path = Path(output)
    else:
        output_path = input_path.with_suffix(".dna")

    # Read input file
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task("Reading input file...", total=None)
        with open(input_path, "rb") as f:
            data = f.read()

    # Configure encoder
    encoding_scheme = EncodingScheme(scheme)
    config = EncodingConfig(
        scheme=encoding_scheme,
        error_correction=error_correction,
    )
    encoder = DNAEncoder(config)

    # Encode
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task("Encoding to DNA...", total=None)
        dna_sequence = encoder.encode(
            data,
            filename=input_path.name,
            mime_type=_get_mime_type(input_path),
        )

    # Format output
    if format == "fasta":
        output_content = f">VibeDNA:{input_path.name}\n"
        # Wrap at 80 characters
        for i in range(0, len(dna_sequence), 80):
            output_content += dna_sequence[i:i + 80] + "\n"
    elif format == "json":
        import json
        output_content = json.dumps({
            "filename": input_path.name,
            "scheme": scheme,
            "sequence": dna_sequence,
            "length": len(dna_sequence),
            "original_size": len(data),
        }, indent=2)
    else:
        output_content = dna_sequence

    # Write output
    with open(output_path, "w") as f:
        f.write(output_content)

    # Report
    console.print(Panel(f"""
[green]✓ Encoded successfully![/green]

Input:  {input_path} ({len(data):,} bytes)
Output: {output_path} ({len(dna_sequence):,} nucleotides)
Scheme: {scheme}
Format: {format}
Ratio:  {len(dna_sequence) / len(data):.2f}x
    """, title="Encoding Complete"))

    console.print(f"\n{COPYRIGHT}", style="dim")


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("-o", "--output", type=click.Path(), help="Output file path")
@click.option("--verify/--no-verify", default=True, help="Verify checksum")
@click.pass_context
def decode(ctx, input_file, output, verify):
    """
    Decode a DNA sequence back to binary.

    Examples:

        vibedna decode document.dna

        vibedna decode sequence.fasta -o recovered.pdf
    """
    from vibedna.core.decoder import DNADecoder

    input_path = Path(input_file)

    # Read and parse input
    with open(input_path, "r") as f:
        content = f.read()

    # Extract sequence from FASTA format if needed
    dna_sequence = _parse_dna_input(content)

    # Decode
    decoder = DNADecoder()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task("Decoding DNA sequence...", total=None)
        result = decoder.decode(dna_sequence)

    # Determine output path
    if output:
        output_path = Path(output)
    else:
        output_path = Path(result.filename) if result.filename != "untitled" else input_path.with_suffix("")

    # Write output
    with open(output_path, "wb") as f:
        f.write(result.data)

    # Report
    status = "[green]✓[/green]" if result.integrity_valid else "[yellow]⚠[/yellow]"

    console.print(Panel(f"""
{status} Decoded successfully!

Input:    {input_path} ({len(dna_sequence):,} nucleotides)
Output:   {output_path} ({len(result.data):,} bytes)
Filename: {result.filename}
MIME:     {result.mime_type}
Scheme:   {result.encoding_scheme}
Errors:   {result.errors_detected} detected, {result.errors_corrected} corrected
Valid:    {"Yes" if result.integrity_valid else "No"}
    """, title="Decoding Complete"))

    console.print(f"\n{COPYRIGHT}", style="dim")


# ═══════════════════════════════════════════════════════════════
# FILE SYSTEM COMMANDS
# ═══════════════════════════════════════════════════════════════

@cli.group()
def fs():
    """DNA file system operations."""
    pass


@fs.command("ls")
@click.argument("path", default="/")
def fs_ls(path):
    """List directory contents."""
    from vibedna.storage.dna_file_system import DNAFileSystem, DNAFile, DNADirectory

    fs = DNAFileSystem()

    try:
        contents = fs.list_directory(path)

        table = Table(title=f"Contents of {path}")
        table.add_column("Type", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Size", justify="right")
        table.add_column("DNA Length", justify="right")
        table.add_column("Created", style="dim")

        for item in contents:
            if isinstance(item, DNADirectory):
                table.add_row(
                    "📁 dir",
                    item.name,
                    "-",
                    "-",
                    item.created_at.strftime("%Y-%m-%d %H:%M"),
                )
            else:
                table.add_row(
                    "📄 file",
                    item.name,
                    f"{item.original_size:,}",
                    f"{item.dna_length:,}",
                    item.created_at.strftime("%Y-%m-%d %H:%M"),
                )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

    console.print(f"\n{COPYRIGHT}", style="dim")


@fs.command("cp")
@click.argument("source", type=click.Path(exists=True))
@click.argument("destination")
def fs_cp(source, destination):
    """Copy file to DNA storage."""
    from vibedna.storage.dna_file_system import DNAFileSystem

    fs = DNAFileSystem()
    source_path = Path(source)

    with open(source_path, "rb") as f:
        data = f.read()

    file = fs.create_file(destination, data)

    console.print(f"[green]✓ Copied {source} → {destination}[/green]")
    console.print(f"  Size: {file.original_size:,} bytes → {file.dna_length:,} nucleotides")
    console.print(f"\n{COPYRIGHT}", style="dim")


@fs.command("export")
@click.argument("source")
@click.argument("destination", type=click.Path())
def fs_export(source, destination):
    """Export file from DNA storage."""
    from vibedna.storage.dna_file_system import DNAFileSystem

    fs = DNAFileSystem()
    fs.export_to_filesystem(source, destination)

    console.print(f"[green]✓ Exported {source} → {destination}[/green]")
    console.print(f"\n{COPYRIGHT}", style="dim")


@fs.command("stats")
def fs_stats():
    """Show storage statistics."""
    from vibedna.storage.dna_file_system import DNAFileSystem

    fs = DNAFileSystem()
    stats = fs.get_storage_stats()

    table = Table(title="DNA File System Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")

    table.add_row("Total Files", str(stats["total_files"]))
    table.add_row("Total Directories", str(stats["total_directories"]))
    table.add_row("Binary Size", f"{stats['total_binary_size']:,} bytes")
    table.add_row("DNA Length", f"{stats['total_dna_length']:,} nucleotides")
    table.add_row("Expansion Ratio", f"{stats['expansion_ratio']:.2f}x")
    table.add_row("Backend", stats["backend"])

    console.print(table)
    console.print(f"\n{COPYRIGHT}", style="dim")


# ═══════════════════════════════════════════════════════════════
# COMPUTATION COMMANDS
# ═══════════════════════════════════════════════════════════════

@cli.group()
def compute():
    """DNA computation operations."""
    pass


@compute.command("gate")
@click.argument("gate", type=click.Choice(["AND", "OR", "XOR", "NOT", "NAND", "NOR", "XNOR"]))
@click.argument("seq_a")
@click.argument("seq_b", required=False)
def compute_gate(gate, seq_a, seq_b):
    """
    Apply logic gate to DNA sequences.

    Example:

        vibedna compute gate XOR ATCG GCTA
    """
    from vibedna.compute.dna_logic_gates import DNAComputeEngine, DNALogicGate

    engine = DNAComputeEngine()

    try:
        gate_enum = DNALogicGate(gate.lower())
        result = engine.apply_gate(gate_enum, seq_a, seq_b)

        console.print(Panel(f"""
[cyan]{seq_a}[/cyan]
  {gate}
[cyan]{seq_b or '(unary)'}[/cyan]
  =
[green]{result}[/green]
        """, title=f"DNA {gate} Gate"))

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

    console.print(f"\n{COPYRIGHT}", style="dim")


@compute.command("math")
@click.argument("operation", type=click.Choice(["add", "sub", "mul", "div"]))
@click.argument("seq_a")
@click.argument("seq_b")
def compute_math(operation, seq_a, seq_b):
    """
    Perform arithmetic on DNA sequences.

    Example:

        vibedna compute math add ATCGATCG GCTAGCTA
    """
    from vibedna.compute.dna_logic_gates import DNAComputeEngine

    engine = DNAComputeEngine()

    try:
        if operation == "add":
            result, overflow = engine.add(seq_a, seq_b)
            flag = " (overflow)" if overflow else ""
        elif operation == "sub":
            result, underflow = engine.subtract(seq_a, seq_b)
            flag = " (underflow)" if underflow else ""
        elif operation == "mul":
            result = engine.multiply(seq_a, seq_b)
            flag = ""
        elif operation == "div":
            quotient, remainder = engine.divide(seq_a, seq_b)
            result = f"{quotient} R {remainder}"
            flag = ""

        console.print(Panel(f"""
[cyan]{seq_a}[/cyan]
  {operation.upper()}
[cyan]{seq_b}[/cyan]
  =
[green]{result}{flag}[/green]
        """, title=f"DNA {operation.upper()}"))

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

    console.print(f"\n{COPYRIGHT}", style="dim")


# ═══════════════════════════════════════════════════════════════
# UTILITY COMMANDS
# ═══════════════════════════════════════════════════════════════

@cli.command()
@click.argument("sequence")
def validate(sequence):
    """Validate DNA sequence format and integrity."""
    from vibedna.utils.validators import validate_dna_sequence

    is_valid, issues = validate_dna_sequence(
        sequence,
        require_header=True,
        require_footer=True,
    )

    if is_valid:
        console.print("[green]✓ Sequence is valid[/green]")
    else:
        console.print("[red]✗ Sequence has issues:[/red]")
        for issue in issues:
            console.print(f"  • {issue}")

    console.print(f"\n{COPYRIGHT}", style="dim")


@cli.command()
@click.argument("sequence")
def info(sequence):
    """Display information about a DNA sequence."""
    from vibedna.core.decoder import DNADecoder

    # Check if it's a file
    if Path(sequence).exists():
        with open(sequence, "r") as f:
            sequence = _parse_dna_input(f.read())

    decoder = DNADecoder()

    try:
        # Try to detect scheme and parse header
        scheme = decoder.detect_encoding_scheme(sequence)

        # Calculate statistics
        gc_count = sum(1 for n in sequence.upper() if n in "GC")
        gc_ratio = gc_count / len(sequence) if sequence else 0

        table = Table(title="DNA Sequence Information")
        table.add_column("Property", style="cyan")
        table.add_column("Value", justify="right")

        table.add_row("Length", f"{len(sequence):,} nucleotides")
        table.add_row("Detected Scheme", scheme)
        table.add_row("GC Content", f"{gc_ratio:.2%}")
        table.add_row("A count", f"{sequence.upper().count('A'):,}")
        table.add_row("T count", f"{sequence.upper().count('T'):,}")
        table.add_row("C count", f"{sequence.upper().count('C'):,}")
        table.add_row("G count", f"{sequence.upper().count('G'):,}")

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

    console.print(f"\n{COPYRIGHT}", style="dim")


@cli.command()
@click.argument("text")
def quick(text):
    """
    Quick encode text to DNA (no headers).

    Example:

        vibedna quick "Hello World"
    """
    from vibedna.core.encoder import DNAEncoder

    encoder = DNAEncoder()
    dna = encoder.encode_raw(text)

    console.print(f"[green]{dna}[/green]")
    console.print(f"\nLength: {len(dna)} nucleotides")
    console.print(f"\n{COPYRIGHT}", style="dim")


@cli.command()
@click.argument("dna_sequence")
def quickdecode(dna_sequence):
    """
    Quick decode DNA to text (no headers).

    Example:

        vibedna quickdecode GCTAGCTACGATCGAT
    """
    from vibedna.core.decoder import DNADecoder

    decoder = DNADecoder()
    data = decoder.decode_raw(dna_sequence)

    try:
        text = data.decode("utf-8")
        console.print(f"[green]{text}[/green]")
    except UnicodeDecodeError:
        console.print(f"[yellow]Binary data ({len(data)} bytes)[/yellow]")
        console.print(data.hex())

    console.print(f"\n{COPYRIGHT}", style="dim")


# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def _parse_dna_input(content: str) -> str:
    """Parse DNA from various formats."""
    lines = content.strip().split("\n")

    # Check for FASTA format
    if lines[0].startswith(">"):
        return "".join(line.strip() for line in lines[1:] if not line.startswith(">"))

    # Check for JSON format
    if content.strip().startswith("{"):
        import json
        data = json.loads(content)
        return data.get("sequence", "")

    # Raw format
    return "".join(content.split())


def _get_mime_type(path: Path) -> str:
    """Get MIME type for a file."""
    import mimetypes
    mime, _ = mimetypes.guess_type(str(path))
    return mime or "application/octet-stream"


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()

# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
