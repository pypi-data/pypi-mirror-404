"""Analyze command for mixref CLI.

This module provides the analyze command that calculates loudness metrics
for audio files and compares them against platform and genre targets.
"""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from mixref.audio import load_audio
from mixref.meters import (
    Genre,
    LoudnessResult,
    Platform,
    calculate_lufs,
    compare_to_target,
    get_target,
)

console = Console()


def analyze_command(
    file: Path = typer.Argument(..., help="Path to audio file to analyze"),
    platform: Platform | None = typer.Option(
        None,
        "--platform",
        "-p",
        help="Platform target (e.g., spotify, youtube, club)",
    ),
    genre: Genre | None = typer.Option(
        None,
        "--genre",
        "-g",
        help="Genre target (e.g., dnb, techno, house)",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output results as JSON",
    ),
) -> None:
    """Analyze audio file and calculate loudness metrics.

    Examples:
        # Analyze for Spotify streaming
        $ mixref analyze my_track.wav --platform spotify

        # Analyze for DnB club play
        $ mixref analyze club_banger.wav --genre dnb

        # Get JSON output
        $ mixref analyze track.wav --platform youtube --json

    Args:
        file: Path to audio file
        platform: Platform target for comparison
        genre: Genre target for comparison
        json_output: Output as JSON instead of Rich table

    Raises:
        typer.Exit: If file not found or processing fails
    """
    # Check file exists
    if not file.exists():
        console.print(f"[red]Error: File not found: {file}[/red]")
        raise typer.Exit(code=1)

    try:
        # Load audio (only show progress for table output)
        if not json_output:
            console.print(f"[dim]Loading {file.name}...[/dim]")
        audio, sr = load_audio(file)

        # Transpose for LUFS calculation (load_audio returns (samples, channels))
        # but calculate_lufs expects (channels, samples)
        if audio.ndim == 2:
            audio = audio.T

        # Calculate LUFS (only show progress for table output)
        if not json_output:
            console.print("[dim]Calculating loudness...[/dim]")
        result = calculate_lufs(audio, sr)

        # Display results
        if json_output:
            _display_json(file, result, platform, genre)
        else:
            _display_table(file, result, platform, genre)

    except Exception as e:
        console.print(f"[red]Error analyzing file: {e}[/red]")
        raise typer.Exit(code=1) from None


def _display_table(
    file: Path,
    result: LoudnessResult,
    platform: Platform | None,
    genre: Genre | None,
) -> None:
    """Display results as Rich table.

    Args:
        file: Audio file path
        result: LoudnessResult from calculate_lufs
        platform: Platform target (optional)
        genre: Genre target (optional)
    """
    # Main results table
    table = Table(title=f"Analysis: {file.name}", show_header=True, header_style="bold")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")
    table.add_column("Status", justify="center")

    # Integrated LUFS
    lufs_str = f"{result.integrated_lufs:.1f} LUFS"
    table.add_row("Integrated Loudness", lufs_str, _lufs_status(result.integrated_lufs))

    # True Peak
    peak_str = f"{result.true_peak_db:.1f} dBTP"
    peak_status = _peak_status(result.true_peak_db)
    table.add_row("True Peak", peak_str, peak_status)

    # LRA
    lra_str = f"{result.loudness_range_lu:.1f} LU"
    table.add_row("Loudness Range", lra_str, "ℹ️")

    console.print(table)

    # Platform comparison
    if platform:
        target = get_target(platform=platform)
        is_ok, diff, message = compare_to_target(result.integrated_lufs, target)
        _display_comparison(message, is_ok, "Platform", platform.value)

    # Genre comparison
    if genre:
        target = get_target(genre=genre)
        is_ok, diff, message = compare_to_target(result.integrated_lufs, target)
        _display_comparison(message, is_ok, "Genre", genre.value)


def _display_comparison(message: str, is_ok: bool, target_type: str, target_name: str) -> None:
    """Display target comparison.

    Args:
        message: Message from compare_to_target
        is_ok: Whether within acceptable range
        target_type: "Platform" or "Genre"
        target_name: Name of target (e.g., "spotify", "dnb")
    """
    console.print()
    console.print(f"[bold]{target_type} Target: {target_name.upper()}[/bold]")

    if is_ok and "Perfect" in message:
        console.print(f"[green]{message}[/green]")
    elif "above" in message or "below" in message:
        console.print(f"[yellow]{message}[/yellow]")
    else:
        console.print(f"[cyan]{message}[/cyan]")


def _lufs_status(lufs: float) -> str:
    """Get status emoji for LUFS value.

    Args:
        lufs: Integrated LUFS value

    Returns:
        Status emoji
    """
    if lufs > -6:
        return "🔴"  # Very loud
    elif lufs > -10:
        return "🟡"  # Loud
    elif lufs > -16:
        return "🟢"  # Normal
    else:
        return "🔵"  # Quiet


def _peak_status(peak: float) -> str:
    """Get status emoji for true peak value.

    Args:
        peak: True peak in dBTP

    Returns:
        Status emoji
    """
    if peak > -0.1:
        return "🔴"  # Clipping danger
    elif peak > -1.0:
        return "🟡"  # Close to clipping
    else:
        return "🟢"  # Safe


def _display_json(
    file: Path,
    result: LoudnessResult,
    platform: Platform | None,
    genre: Genre | None,
) -> None:
    """Display results as JSON.

    Args:
        file: Audio file path
        result: LoudnessResult from calculate_lufs
        platform: Platform target (optional)
        genre: Genre target (optional)
    """
    import json

    output = {
        "file": str(file),
        "loudness": {
            "integrated_lufs": round(result.integrated_lufs, 2),
            "true_peak_db": round(result.true_peak_db, 2),
            "loudness_range_lu": round(result.loudness_range_lu, 2),
            "short_term_max_lufs": round(result.short_term_max_lufs, 2),
            "short_term_min_lufs": round(result.short_term_min_lufs, 2),
        },
    }

    # Add platform comparison
    if platform:
        target = get_target(platform=platform)
        is_ok, diff, message = compare_to_target(result.integrated_lufs, target)
        output["platform"] = {
            "name": platform.value,
            "target_lufs": target.target_lufs,
            "difference": round(diff, 2),
            "is_acceptable": is_ok,
            "message": message,
        }

    # Add genre comparison
    if genre:
        target = get_target(genre=genre)
        is_ok, diff, message = compare_to_target(result.integrated_lufs, target)
        output["genre"] = {
            "name": genre.value,
            "target_lufs": target.target_lufs,
            "difference": round(diff, 2),
            "is_acceptable": is_ok,
            "message": message,
        }

    console.print_json(json.dumps(output))
