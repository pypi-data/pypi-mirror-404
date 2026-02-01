"""
Shell completions command for VarityKit
"""

import os
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel


@click.command()
@click.option(
    "--shell",
    type=click.Choice(["bash", "zsh", "fish"], case_sensitive=False),
    help="Shell type (auto-detected if not specified)",
)
@click.option("--install", is_flag=True, help="Install completions to shell config file")
@click.pass_context
def completions(ctx, shell, install):
    """
    Setup shell completions for VarityKit CLI

    Enables tab completion for all commands, options, and arguments.
    Supports bash, zsh, and fish shells.

    \b
    Usage:
      # Auto-detect shell and show instructions
      varitykit completions

      # Generate for specific shell
      varitykit completions --shell bash

      # Auto-install to shell config
      varitykit completions --install
    """
    console = Console()
    logger = ctx.obj["logger"]

    # Auto-detect shell if not specified
    if not shell:
        shell = detect_shell()
        if not shell:
            console.print(
                Panel.fit(
                    "[bold red]Could not detect shell[/bold red]\n"
                    "Please specify shell type with --shell option",
                    border_style="red",
                )
            )
            ctx.exit(1)

    logger.info(f"Generating {shell} completions...")

    if install:
        # Install completions to shell config
        install_completions(shell, console, logger)
    else:
        # Show installation instructions
        show_instructions(shell, console)


def detect_shell() -> str:
    """Detect current shell from environment"""
    shell_env = os.environ.get("SHELL", "")

    if "bash" in shell_env:
        return "bash"
    elif "zsh" in shell_env:
        return "zsh"
    elif "fish" in shell_env:
        return "fish"

    return "bash"  # Default to bash if shell cannot be detected


def get_completion_script(shell: str) -> str:
    """Get completion script for shell type"""

    if shell == "bash":
        return """
# VarityKit shell completions for bash
eval "$(_VARIETYKIT_COMPLETE=bash_source varitykit)"
"""

    elif shell == "zsh":
        return """
# VarityKit shell completions for zsh
eval "$(_VARIETYKIT_COMPLETE=zsh_source varitykit)"
"""

    elif shell == "fish":
        return """
# VarityKit shell completions for fish
eval (env _VARIETYKIT_COMPLETE=fish_source varitykit)
"""

    return ""


def get_config_file(shell: str) -> Path:
    """Get shell configuration file path"""
    home = Path.home()

    if shell == "bash":
        # Try .bashrc first, then .bash_profile
        bashrc = home / ".bashrc"
        bash_profile = home / ".bash_profile"
        return bashrc if bashrc.exists() else bash_profile

    elif shell == "zsh":
        return home / ".zshrc"

    elif shell == "fish":
        fish_config = home / ".config" / "fish" / "config.fish"
        fish_config.parent.mkdir(parents=True, exist_ok=True)
        return fish_config

    # Fallback to .bashrc
    return Path.home() / ".bashrc"


def install_completions(shell: str, console: Console, logger):
    """Install completions to shell config file"""
    config_file = get_config_file(shell)

    if not config_file:
        console.print(
            Panel.fit(
                f"[bold red]Could not find config file for {shell}[/bold red]", border_style="red"
            )
        )
        return

    script = get_completion_script(shell)

    try:
        # Check if already installed
        if config_file.exists():
            content = config_file.read_text()
            if "VARIETYKIT_COMPLETE" in content:
                console.print(
                    Panel.fit(
                        "[bold yellow]Completions already installed[/bold yellow]\n"
                        f"Found in {config_file}",
                        border_style="yellow",
                    )
                )
                return

        # Append completion script
        with open(config_file, "a") as f:
            f.write("\n" + script)

        console.print(
            Panel.fit(
                "[bold green]✓ Completions installed successfully![/bold green]\n"
                f"Added to {config_file}\n\n"
                f"[dim]Restart your shell or run:[/dim]\n"
                f"  source {config_file}",
                border_style="green",
            )
        )

        logger.info(f"Installed {shell} completions to {config_file}")

    except Exception as e:
        console.print(
            Panel.fit(
                f"[bold red]Failed to install completions[/bold red]\n" f"{str(e)}",
                border_style="red",
            )
        )
        logger.error(f"Failed to install completions: {e}")


def show_instructions(shell: str, console: Console):
    """Show manual installation instructions"""
    config_file = get_config_file(shell)
    script = get_completion_script(shell).strip()

    console.print(
        Panel.fit(
            f"[bold cyan]Shell Completions for {shell.upper()}[/bold cyan]", border_style="cyan"
        )
    )

    console.print("\n[bold]Option 1: Auto-install[/bold]")
    console.print("  [cyan]varitykit completions --install[/cyan]\n")

    console.print("[bold]Option 2: Manual installation[/bold]")
    console.print(f"  Add this line to [cyan]{config_file}[/cyan]:\n")
    console.print(f"  [dim]{script}[/dim]\n")

    console.print("[bold]Option 3: Temporary (current session only)[/bold]")

    if shell == "bash":
        console.print('  [cyan]eval "$(_VARIETYKIT_COMPLETE=bash_source varitykit)"[/cyan]\n')
    elif shell == "zsh":
        console.print('  [cyan]eval "$(_VARIETYKIT_COMPLETE=zsh_source varitykit)"[/cyan]\n')
    elif shell == "fish":
        console.print("  [cyan]eval (env _VARIETYKIT_COMPLETE=fish_source varitykit)[/cyan]\n")

    console.print("[dim]After installation, restart your shell or source the config file.[/dim]\n")
