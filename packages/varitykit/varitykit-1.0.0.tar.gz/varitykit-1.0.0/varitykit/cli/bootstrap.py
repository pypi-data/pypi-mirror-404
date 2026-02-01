"""
Bootstrap command - installs project dependencies
"""

import subprocess
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from varitykit.core.config import ConfigManager


@click.command()
@click.option("--skip-npm", is_flag=True, help="Skip npm install")
@click.option("--skip-pip", is_flag=True, help="Skip pip install")
@click.option("--skip-docker", is_flag=True, help="Skip Docker setup")
@click.pass_context
def bootstrap(ctx, skip_npm, skip_pip, skip_docker):
    """
    Install project dependencies and setup environment

    Installs all required dependencies:
    - npm packages for frontend
    - pip packages for backend
    - Docker images

    Run this command after 'varitykit init' or when cloning an existing project.
    """
    console = Console()
    logger = ctx.obj["logger"]

    console.print(
        Panel.fit(
            "[bold cyan]VarityKit Bootstrap[/bold cyan]\n" "Installing project dependencies...",
            border_style="cyan",
        )
    )

    # Find project root (look for .varitykit.toml)
    config_manager = ConfigManager()
    config_file = config_manager.find_config_file()

    if config_file is None:
        console.print(
            "[red]✗ No VarityKit project found[/red]\n"
            "[dim]Run this command from within a VarityKit project directory.[/dim]"
        )
        ctx.exit(1)

    project_root = config_file.parent if config_file is not None else Path(".")
    logger.info(f"Found project at {project_root}")

    console.print(f"\n[cyan]Project:[/cyan] {project_root.name}")
    console.print(f"[cyan]Path:[/cyan] {project_root}\n")

    success = True

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
    ) as progress:

        # Install npm dependencies
        if not skip_npm:
            package_json = project_root / "package.json"
            if package_json.exists():
                task = progress.add_task("Installing npm packages...", total=None)
                try:
                    result = subprocess.run(
                        ["npm", "install"],
                        cwd=project_root,
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    progress.update(task, completed=True)
                    console.print("[green]✓ npm packages installed[/green]")
                    logger.info("npm install completed successfully")
                except subprocess.CalledProcessError as e:
                    progress.update(task, completed=True)
                    console.print(f"[red]✗ npm install failed[/red]")
                    logger.error(f"npm install failed: {e.stderr}")
                    success = False
                except FileNotFoundError:
                    progress.update(task, completed=True)
                    console.print("[yellow]⚠ npm not found, skipping[/yellow]")
                    logger.warning("npm not found")
            else:
                console.print("[dim]No package.json found, skipping npm install[/dim]")

        # Install pip dependencies
        if not skip_pip:
            requirements_txt = project_root / "requirements.txt"
            pyproject_toml = project_root / "pyproject.toml"

            if requirements_txt.exists() or pyproject_toml.exists():
                task = progress.add_task("Installing Python packages...", total=None)
                try:
                    # Try to use pip
                    if requirements_txt.exists():
                        result = subprocess.run(
                            ["pip", "install", "-r", "requirements.txt"],
                            cwd=project_root,
                            capture_output=True,
                            text=True,
                            check=True,
                        )
                    elif pyproject_toml.exists():
                        result = subprocess.run(
                            ["pip", "install", "-e", "."],
                            cwd=project_root,
                            capture_output=True,
                            text=True,
                            check=True,
                        )

                    progress.update(task, completed=True)
                    console.print("[green]✓ Python packages installed[/green]")
                    logger.info("pip install completed successfully")
                except subprocess.CalledProcessError as e:
                    progress.update(task, completed=True)
                    console.print(f"[red]✗ pip install failed[/red]")
                    logger.error(f"pip install failed: {e.stderr}")
                    success = False
                except FileNotFoundError:
                    progress.update(task, completed=True)
                    console.print("[yellow]⚠ pip not found, skipping[/yellow]")
                    logger.warning("pip not found")
            else:
                console.print(
                    "[dim]No requirements.txt or pyproject.toml found, skipping pip install[/dim]"
                )

        # Setup Docker
        if not skip_docker:
            docker_compose = project_root / "docker-compose.yml"
            if docker_compose.exists():
                task = progress.add_task("Pulling Docker images...", total=None)
                try:
                    result = subprocess.run(
                        ["docker-compose", "pull"],
                        cwd=project_root,
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    progress.update(task, completed=True)
                    console.print("[green]✓ Docker images pulled[/green]")
                    logger.info("Docker pull completed successfully")
                except subprocess.CalledProcessError as e:
                    progress.update(task, completed=True)
                    console.print(f"[yellow]⚠ Docker pull failed[/yellow]")
                    logger.warning(f"Docker pull failed: {e.stderr}")
                    # Don't mark as failure - Docker might not be running
                except FileNotFoundError:
                    progress.update(task, completed=True)
                    console.print("[yellow]⚠ Docker not found, skipping[/yellow]")
                    logger.warning("Docker not found")
            else:
                console.print("[dim]No docker-compose.yml found, skipping Docker setup[/dim]")

        # Create .env file if it doesn't exist
        task = progress.add_task("Setting up environment...", total=None)
        env_example = project_root / ".env.example"
        env_file = project_root / ".env"

        if env_example.exists() and not env_file.exists():
            env_file.write_text(env_example.read_text())
            console.print("[green]✓ .env file created from .env.example[/green]")
            logger.info("Created .env file")
        elif not env_file.exists():
            # Create basic .env
            env_file.write_text(
                "# Environment variables\n" "NODE_ENV=development\n" "VARITY_ENV=development\n"
            )
            console.print("[green]✓ .env file created[/green]")
            logger.info("Created basic .env file")

        progress.update(task, completed=True)

    # Summary
    console.print("\n")
    if success:
        console.print(
            Panel.fit(
                "[bold green]✓ Bootstrap completed successfully![/bold green]\n\n"
                "[cyan]Next steps:[/cyan]\n"
                "  1. Update .env file with your configuration\n"
                "  2. varitykit dev (start development server)\n"
                "  3. varitykit localdepin start (start local blockchain)\n\n"
                "[dim]For more information: varitykit --help[/dim]",
                border_style="green",
            )
        )
        logger.info("Bootstrap completed successfully")
    else:
        console.print(
            Panel.fit(
                "[bold yellow]⚠ Bootstrap completed with warnings[/bold yellow]\n\n"
                "Some dependencies failed to install.\n"
                "Check the output above and install manually if needed.\n\n"
                "[dim]Run 'varitykit doctor' to diagnose issues.[/dim]",
                border_style="yellow",
            )
        )
        logger.warning("Bootstrap completed with warnings")
        ctx.exit(1)
