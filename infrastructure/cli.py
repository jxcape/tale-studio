"""
CLI entry point for Tale video generation pipeline.
"""
import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from infrastructure.settings import Settings, get_settings
from infrastructure.api_key_pool import APIKeyPool, RotationStrategy

app = typer.Typer(
    name="tale",
    help="AI Video Generation Pipeline - Generate videos from stories",
    add_completion=False,
)
console = Console()


@app.command()
def generate(
    story: str = typer.Argument(..., help="Story text or path to story file"),
    genre: str = typer.Option("drama", help="Genre (drama, action, comedy, etc.)"),
    duration: float = typer.Option(3.0, help="Target duration in minutes"),
    output: Optional[Path] = typer.Option(None, help="Output directory"),
    path: str = typer.Option("template", help="Shot composition path (template or llm)"),
    dry_run: bool = typer.Option(False, help="Plan without generating videos"),
):
    """
    Generate a video from a story.

    Example:
        tale generate "A lonely scientist discovers..." --duration 3 --genre drama
    """
    try:
        settings = get_settings()
    except Exception as e:
        console.print(f"[red]Error loading settings:[/red] {e}")
        console.print("Make sure .env file exists with required API keys.")
        raise typer.Exit(1)

    # Check if story is a file path
    story_text = story
    if Path(story).exists():
        story_text = Path(story).read_text()
        console.print(f"[green]Loaded story from:[/green] {story}")

    console.print(f"\n[bold]Tale Video Generation[/bold]")
    console.print(f"Genre: {genre}")
    console.print(f"Duration: {duration} minutes")
    console.print(f"Path: {path}")

    if dry_run:
        console.print("\n[yellow]Dry run mode - no videos will be generated[/yellow]")
        # TODO: Run pipeline in dry-run mode
        console.print("[green]Pipeline would execute here...[/green]")
        return

    # TODO: Run full pipeline
    console.print("\n[yellow]Full pipeline not yet implemented[/yellow]")
    console.print("Use --dry-run to test planning.")


@app.command()
def status():
    """
    Show API key status and remaining quotas.
    """
    try:
        settings = get_settings()
    except Exception as e:
        console.print(f"[red]Error loading settings:[/red] {e}")
        raise typer.Exit(1)

    keys = settings.google_api_keys_list
    pool = APIKeyPool(
        keys=keys,
        strategy=RotationStrategy.from_string(settings.veo.rotation_strategy),
        daily_limit=settings.veo.daily_limit_per_key,
        max_concurrent_per_key=settings.veo.max_concurrent_per_key,
    )

    table = Table(title="API Key Status")
    table.add_column("Key", style="cyan")
    table.add_column("Used Today", justify="right")
    table.add_column("Remaining", justify="right")
    table.add_column("Status", justify="center")

    status = pool.get_status()
    for i, (key, info) in enumerate(status.items(), 1):
        # Mask key for security
        masked_key = f"Key {i} ({key[:8]}...)"
        used = str(info["used"])
        remaining = str(info["remaining"])
        status_icon = "[green]✓[/green]" if info["available"] else "[red]✗[/red]"
        table.add_row(masked_key, used, remaining, status_icon)

    console.print(table)
    console.print(f"\n[bold]Total remaining:[/bold] {pool.get_total_remaining()} videos")
    console.print(f"[bold]Rotation strategy:[/bold] {settings.veo.rotation_strategy}")


@app.command()
def init():
    """
    Initialize project directories and validate configuration.
    """
    try:
        settings = get_settings()
    except Exception as e:
        console.print(f"[red]Error loading settings:[/red] {e}")
        console.print("\nCreate a .env file with the following keys:")
        console.print("  OPENAI_API_KEY=sk-...")
        console.print("  GOOGLE_API_KEYS=key1,key2,...")
        console.print("  GOOGLE_PROJECT_ID=your-project")
        raise typer.Exit(1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Creating directories...", total=None)

        settings.ensure_directories()

        progress.update(task, description="Validating API keys...")
        # TODO: Validate API keys with test calls

        progress.update(task, description="Done!")

    console.print("\n[green]✓[/green] Project initialized successfully!")
    console.print(f"  Output directory: {settings.output_dir}")
    console.print(f"  Assets directory: {settings.assets_dir}")
    console.print(f"  Google API keys: {len(settings.google_api_keys_list)} configured")


@app.command()
def plan(
    story: str = typer.Argument(..., help="Story text or path to story file"),
    genre: str = typer.Option("drama", help="Genre"),
    duration: float = typer.Option(3.0, help="Target duration in minutes"),
    output: Optional[Path] = typer.Option(None, help="Output path for plan JSON"),
):
    """
    Generate a production plan without creating videos.

    Shows scenes, shots, and prompts that would be generated.
    """
    console.print("[bold]Generating production plan...[/bold]")

    # Check if story is a file path
    story_text = story
    if Path(story).exists():
        story_text = Path(story).read_text()

    console.print(f"\nStory length: {len(story_text)} characters")
    console.print(f"Target duration: {duration} minutes")
    console.print(f"Genre: {genre}")

    # TODO: Run Level 1-3 planning without video generation
    console.print("\n[yellow]Planning pipeline not yet implemented[/yellow]")


@app.command()
def version():
    """Show version information."""
    console.print("[bold]Tale[/bold] - AI Video Generation Pipeline")
    console.print("Version: 0.1.0")
    console.print("Architecture: 3-Level (Scene → Shot → Prompt)")


def main():
    """Entry point for CLI."""
    app()


if __name__ == "__main__":
    main()
