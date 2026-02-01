"""Main CLI for bcpractice."""

from __future__ import annotations

import asyncio
from pathlib import Path

import questionary
import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import (
    Config,
    LENGTH_PRESETS,
    clear_config,
    load_config,
    save_config,
)
from .generator import (
    generate_problems,
    generate_topics_header,
    generate_topics_subtitle,
)
from .latex import render_template_manual, Section
from .pdf import check_pdflatex_available, compile_pdf
from .topics import UNITS, Topic, Unit, format_topic_display, format_unit_display

app = typer.Typer(
    name="bcpractice",
    help="Generate AP BC Calculus practice problems using AI.",
    no_args_is_help=True,
)
console = Console()


@app.command()
def setup():
    """Configure your AI provider and API key."""
    console.print(Panel.fit(
        "[bold blue]BC Practice Setup[/bold blue]\n"
        "Configure your AI provider for generating problems.",
        border_style="blue",
    ))

    # Select provider
    provider = questionary.select(
        "Select your AI provider:",
        choices=[
            questionary.Choice("OpenAI (GPT-4)", value="openai"),
            questionary.Choice("Anthropic (Claude)", value="anthropic"),
        ],
    ).ask()

    if provider is None:
        console.print("[yellow]Setup cancelled.[/yellow]")
        raise typer.Exit(1)

    # Get API key
    if provider == "openai":
        api_key = questionary.password(
            "Enter your OpenAI API key (sk-...):"
        ).ask()
    else:
        api_key = questionary.password(
            "Enter your Anthropic API key (sk-ant-...):"
        ).ask()

    if not api_key:
        console.print("[yellow]Setup cancelled.[/yellow]")
        raise typer.Exit(1)

    # Save config
    config = Config(provider=provider)
    if provider == "openai":
        config.openai_api_key = api_key
    else:
        config.anthropic_api_key = api_key

    save_config(config)
    console.print("[green]Configuration saved successfully![/green]")


@app.command()
def generate(
    output: Path = typer.Option(
        None,
        "--output", "-o",
        help="Output directory for the PDF",
    ),
    length: str = typer.Option(
        None,
        "--length", "-l",
        help="Problem set length: quick, medium, or full",
    ),
):
    """Generate a practice problem set."""
    # Load config
    config = load_config()

    if not config.is_configured():
        console.print("[red]Not configured. Run 'bcpractice setup' first.[/red]")
        raise typer.Exit(1)

    # Check pdflatex
    if not check_pdflatex_available():
        console.print(
            "[yellow]Warning: pdflatex not found. "
            "PDF compilation may fail.[/yellow]"
        )

    console.print(Panel.fit(
        "[bold blue]BC Practice Generator[/bold blue]",
        border_style="blue",
    ))

    # Selection mode
    mode = questionary.select(
        "How would you like to select topics?",
        choices=[
            questionary.Choice("By Unit (select entire units)", value="unit"),
            questionary.Choice("By Topic (select specific topics)", value="topic"),
        ],
    ).ask()

    if mode is None:
        raise typer.Exit(1)

    selected_topics: list[tuple[Unit, Topic]] = []

    if mode == "unit":
        # Select units
        unit_choices = [
            questionary.Choice(
                format_unit_display(unit),
                value=unit.number,
            )
            for unit in UNITS
        ]

        selected_units = questionary.checkbox(
            "Select units (space to toggle, enter to confirm):",
            choices=unit_choices,
        ).ask()

        if not selected_units:
            console.print("[yellow]No units selected. Exiting.[/yellow]")
            raise typer.Exit(1)

        # Get all topics from selected units
        for unit in UNITS:
            if unit.number in selected_units:
                for topic in unit.topics:
                    selected_topics.append((unit, topic))

    else:
        # Select specific topics
        # Group by unit for better UX
        all_choices = []
        for unit in UNITS:
            # Add unit as a separator (disabled choice)
            all_choices.append(questionary.Separator(f"── Unit {unit.number}: {unit.name} ──"))
            for topic in unit.topics:
                all_choices.append(questionary.Choice(
                    format_topic_display(unit, topic),
                    value=(unit.number, topic.id),
                ))

        selected = questionary.checkbox(
            "Select topics (space to toggle, enter to confirm):",
            choices=all_choices,
        ).ask()

        if not selected:
            console.print("[yellow]No topics selected. Exiting.[/yellow]")
            raise typer.Exit(1)

        # Convert selections to (Unit, Topic) tuples
        for unit_num, topic_id in selected:
            for unit in UNITS:
                if unit.number == unit_num:
                    for topic in unit.topics:
                        if topic.id == topic_id:
                            selected_topics.append((unit, topic))
                            break

    console.print(f"\n[green]Selected {len(selected_topics)} topics.[/green]")

    # Select length
    if length is None:
        length_choices = [
            questionary.Choice(
                f"Quick ({LENGTH_PRESETS['quick'][0]}-{LENGTH_PRESETS['quick'][1]} problems)",
                value="quick",
            ),
            questionary.Choice(
                f"Medium ({LENGTH_PRESETS['medium'][0]}-{LENGTH_PRESETS['medium'][1]} problems) - Recommended",
                value="medium",
            ),
            questionary.Choice(
                f"Full ({LENGTH_PRESETS['full'][0]}-{LENGTH_PRESETS['full'][1]} problems)",
                value="full",
            ),
        ]

        length = questionary.select(
            "Select problem set length:",
            choices=length_choices,
            default="medium",
        ).ask()

    if length is None:
        raise typer.Exit(1)

    # Generate problems
    console.print()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Generating problems with AI...", total=None)

        try:
            sections = asyncio.run(
                generate_problems(config, selected_topics, length)
            )
        except Exception as e:
            console.print(f"[red]Error generating problems: {e}[/red]")
            raise typer.Exit(1)

        progress.update(task, description="Rendering LaTeX...")

        # Render LaTeX
        topics_header = generate_topics_header(selected_topics)
        topics_subtitle = generate_topics_subtitle(selected_topics)

        latex_content = render_template_manual(
            "",  # Template is built inside the function
            {
                "topics_header": topics_header,
                "topics_subtitle": topics_subtitle,
                "total_problems": sum(len(s.problems) for s in sections),
                "total_points": sum(s.points for s in sections),
                "sections": [
                    {
                        "title": s.title,
                        "subtitle": s.subtitle,
                        "points": s.points,
                        "problems": [
                            {
                                "number": p.number,
                                "title": p.title,
                                "points": p.points,
                                "content": p.content,
                                "parts": p.parts or [],
                                "tikz_graph": p.tikz_graph,
                            }
                            for p in s.problems
                        ],
                    }
                    for s in sections
                ],
            },
        )

        progress.update(task, description="Compiling PDF...")

        # Compile PDF
        try:
            output_dir = output or Path.cwd()
            pdf_path = compile_pdf(latex_content, output_dir)
        except RuntimeError as e:
            console.print(f"[red]{e}[/red]")
            # Save LaTeX file as fallback
            tex_path = output_dir / "BC_Practice.tex"
            tex_path.write_text(latex_content)
            console.print(f"[yellow]LaTeX saved to: {tex_path}[/yellow]")
            raise typer.Exit(1)

    console.print(f"\n[green]PDF generated successfully![/green]")
    console.print(f"[blue]📄 {pdf_path}[/blue]")


@app.command()
def topics():
    """List all available topics."""
    for unit in UNITS:
        bc_tag = " [BC Only]" if unit.bc_only else ""
        console.print(f"\n[bold blue]Unit {unit.number}: {unit.name}{bc_tag}[/bold blue]")
        for topic in unit.topics:
            bc_tag = " [BC]" if topic.bc_only else ""
            console.print(f"  {topic.id} {topic.name}{bc_tag}")


@app.command()
def reset():
    """Reset configuration (remove API keys)."""
    confirm = questionary.confirm(
        "Are you sure you want to reset your configuration?",
        default=False,
    ).ask()

    if confirm:
        clear_config()
        console.print("[green]Configuration reset.[/green]")
    else:
        console.print("[yellow]Cancelled.[/yellow]")


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
