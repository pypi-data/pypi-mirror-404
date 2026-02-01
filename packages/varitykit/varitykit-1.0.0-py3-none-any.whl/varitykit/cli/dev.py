"""
Development server commands for VarityKit
"""

import os
import signal
import subprocess
import sys
from pathlib import Path

import click
from rich import box
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table


@click.command()
@click.option(
    "--project",
    "-p",
    type=click.Choice(["marketing", "iso-dashboard", "docs"], case_sensitive=False),
    default="marketing",
    help="Frontend project to run",
)
@click.option("--api-only", is_flag=True, help="Run only the API server")
@click.option("--frontend-only", is_flag=True, help="Run only the frontend")
@click.option("--port", default=3001, help="API server port (default: 3001)")
@click.pass_context
def dev(ctx, project, api_only, frontend_only, port):
    """
    Start development servers (API + Frontend)

    Runs the Varity API server and frontend concurrently with hot-reload.
    Perfect for rapid development and testing.

    \b
    Examples:
      varitykit dev                      # Start both API + marketing website
      varitykit dev -p iso-dashboard     # Start both API + ISO dashboard
      varitykit dev --api-only           # Start only API server
      varitykit dev --frontend-only      # Start only frontend

    \b
    Default URLs:
      • API Server:        http://localhost:3001
      • Marketing Website: http://localhost:3000
      • ISO Dashboard:     http://localhost:3002
      • Docs Portal:       http://localhost:3003

    \b
    Press Ctrl+C to stop all servers.
    """
    console = Console()
    logger = ctx.obj["logger"]

    # Get project root (3 levels up from cli dir)
    varity_root = Path(__file__).parent.parent.parent.parent

    # Define paths
    api_server_path = varity_root / "packages" / "varity-api-server"
    marketing_path = varity_root / "marketing-website"
    iso_dashboard_path = varity_root / "iso-dashboard-mvp"
    docs_path = varity_root / "varitykit-docs"

    # Validate paths exist
    if not api_only and not api_server_path.exists():
        console.print(f"[red]✗[/red] API server not found at {api_server_path}")
        ctx.exit(1)

    # Select frontend path and port
    frontend_map = {
        "marketing": (marketing_path, 3000, "Marketing Website"),
        "iso-dashboard": (iso_dashboard_path, 3002, "ISO Dashboard"),
        "docs": (docs_path, 3003, "Docs Portal"),
    }

    frontend_path, frontend_port, frontend_name = frontend_map[project]

    if not frontend_only and not frontend_path.exists():
        console.print(f"[red]✗[/red] {frontend_name} not found at {frontend_path}")
        ctx.exit(1)

    # Create info panel
    services = []
    if not frontend_only:
        services.append(f"[cyan]• API Server:[/cyan] http://localhost:{port}")
    if not api_only:
        services.append(f"[green]• {frontend_name}:[/green] http://localhost:{frontend_port}")

    console.print(
        Panel.fit(
            "[bold cyan]Starting Development Servers[/bold cyan]\n\n"
            + "\n".join(services)
            + "\n\n[yellow]Press Ctrl+C to stop all servers[/yellow]",
            border_style="cyan",
        )
    )

    logger.info(
        f"Starting development servers (project={project}, api_port={port}, frontend_port={frontend_port})"
    )

    processes: List[subprocess.Popen] = []

    def cleanup_processes(signum=None, frame=None):
        """Kill all child processes"""
        console.print("\n[yellow]Shutting down servers...[/yellow]")
        for proc in processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        logger.info("All development servers stopped")
        sys.exit(0)

    # Register signal handlers
    signal.signal(signal.SIGINT, cleanup_processes)
    signal.signal(signal.SIGTERM, cleanup_processes)

    try:
        # Start API server
        if not frontend_only:
            console.print("[cyan]Starting API server...[/cyan]")
            logger.info(f"Starting API server at {api_server_path}")

            api_env = os.environ.copy()
            api_env["PORT"] = str(port)

            api_proc = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=str(api_server_path),
                env=api_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            processes.append(api_proc)
            console.print(f"[green]✓[/green] API server starting on port {port}")

        # Start frontend
        if not api_only:
            console.print(f"[green]Starting {frontend_name}...[/green]")
            logger.info(f"Starting {frontend_name} at {frontend_path}")

            frontend_env = os.environ.copy()
            frontend_env["PORT"] = str(frontend_port)

            frontend_proc = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=str(frontend_path),
                env=frontend_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            processes.append(frontend_proc)
            console.print(f"[green]✓[/green] {frontend_name} starting on port {frontend_port}")

        console.print("\n[bold green]All servers started successfully![/bold green]")
        console.print("[yellow]Watching for logs... (Ctrl+C to stop)[/yellow]\n")

        # Stream logs from all processes
        import select

        while True:
            # Check if any process has died
            for proc in processes:
                if proc.poll() is not None:
                    console.print(
                        f"[red]✗[/red] Process died unexpectedly (exit code: {proc.returncode})"
                    )
                    cleanup_processes()

            # Read available output
            for proc in processes:
                if proc.stdout:
                    line = proc.stdout.readline()
                    if line:
                        # Color code by process
                        if proc == processes[0]:  # API
                            console.print(f"[cyan][API][/cyan] {line.strip()}")
                        else:  # Frontend
                            console.print(f"[green][{frontend_name}][/green] {line.strip()}")

    except Exception as e:
        logger.error(f"Development server error: {e}")
        console.print(f"[red]Error:[/red] {e}")
        cleanup_processes()
        ctx.exit(1)
