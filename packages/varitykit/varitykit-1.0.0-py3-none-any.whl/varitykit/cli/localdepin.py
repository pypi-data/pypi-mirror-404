"""
LocalDePin management commands for VarityKit

Manages the local DePin development stack with Docker Compose.
Provides commands to start, stop, reset, and monitor all services.
"""

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, cast

import click
import requests
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()


def get_localdepin_dir() -> Path:
    """Get the localdepin directory path"""
    # From varitykit/cli/localdepin.py -> varitykit-cli/localdepin
    cli_dir = Path(__file__).parent  # varitykit/cli
    varitykit_dir = cli_dir.parent  # varitykit
    cli_root = varitykit_dir.parent  # varitykit-cli
    localdepin_dir = cli_root / "localdepin"

    if not localdepin_dir.exists():
        console.print(f"[red]Error: LocalDePin directory not found at {localdepin_dir}[/red]")
        sys.exit(1)

    return localdepin_dir


def get_docker_compose_path() -> Path:
    """Get path to docker-compose.yml file"""
    return get_localdepin_dir() / "docker-compose.yml"


def check_docker_installed() -> bool:
    """Check if Docker is installed and running"""
    try:
        result = subprocess.run(["docker", "info"], capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def check_docker_compose_installed() -> bool:
    """Check if Docker Compose is installed"""
    try:
        result = subprocess.run(
            ["docker-compose", "--version"], capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def run_docker_compose(
    args: List[str], cwd: Path, capture_output: bool = False
) -> subprocess.CompletedProcess:
    """Run docker-compose command"""
    cmd = ["docker-compose"] + args

    if capture_output:
        result = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)
    else:
        result = subprocess.run(cmd, cwd=str(cwd), check=False)

    return result


def check_service_health(
    service_name: str, port: int, endpoint: str = "/health", timeout: int = 2
) -> Tuple[bool, str]:
    """
    Check if a service is responding to health checks

    Returns:
        Tuple of (is_healthy: bool, message: str)
    """
    try:
        response = requests.get(f"http://localhost:{port}{endpoint}", timeout=timeout)

        if response.status_code == 200:
            return True, "healthy"
        else:
            return False, f"unhealthy (HTTP {response.status_code})"
    except requests.exceptions.ConnectionError:
        return False, "not responding"
    except requests.exceptions.Timeout:
        return False, "timeout"
    except Exception as e:
        return False, f"error: {str(e)[:30]}"


def get_service_status(localdepin_dir: Path) -> Dict[str, Dict]:
    """Get status of all LocalDePin services"""
    result = run_docker_compose(["ps", "--format", "json"], localdepin_dir, capture_output=True)

    services = {}

    if result.returncode == 0 and result.stdout.strip():
        # Parse each line as JSON (docker-compose ps --format json outputs one JSON object per line)
        for line in result.stdout.strip().split("\n"):
            if line.strip():
                try:
                    service_data = json.loads(line)
                    service_name = service_data.get("Service", service_data.get("Name", "unknown"))

                    # Clean up service name (remove project prefix)
                    if "-" in service_name:
                        parts = service_name.split("-")
                        if len(parts) > 1:
                            service_name = "-".join(parts[1:])

                    services[service_name] = {
                        "state": service_data.get("State", "unknown"),
                        "status": service_data.get("Status", "unknown"),
                        "ports": service_data.get("Publishers", []),
                    }
                except json.JSONDecodeError:
                    continue

    return services


# Define service health check endpoints
SERVICE_HEALTH_CHECKS = {
    "arbitrum-node": {"port": 8547, "endpoint": "/"},
    "ipfs-node": {"port": 5001, "endpoint": "/api/v0/id"},
    "pinata-mock": {"port": 3002, "endpoint": "/health"},
    "akash-simulator": {"port": 3003, "endpoint": "/health"},
    "celestia-node": {"port": 26659, "endpoint": "/head"},
    "postgres": {"port": 5432, "endpoint": None},  # No HTTP health check
    "redis": {"port": 6379, "endpoint": None},  # No HTTP health check
    "varity-api-local": {"port": 3001, "endpoint": "/health"},
    "varitykit-explorer": {"port": 8080, "endpoint": "/"},
}


def wait_for_services(services_to_check: List[str], timeout: int = 60) -> bool:
    """
    Wait for services to become healthy

    Returns:
        True if all services are healthy, False otherwise
    """
    start_time = time.time()

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
    ) as progress:

        task = progress.add_task("[cyan]Waiting for services to be healthy...", total=None)

        while time.time() - start_time < timeout:
            all_healthy = True

            for service_name in services_to_check:
                if service_name not in SERVICE_HEALTH_CHECKS:
                    continue

                health_config = SERVICE_HEALTH_CHECKS.get(service_name, {})
                endpoint = health_config.get("endpoint")
                if endpoint is None:
                    # Skip services without HTTP health checks
                    continue

                port = int(health_config.get("port", 0))
                is_healthy, _ = check_service_health(
                    service_name, port, str(endpoint)
                )

                if not is_healthy:
                    all_healthy = False
                    break

            if all_healthy:
                progress.update(task, description="[green]All services are healthy!")
                time.sleep(0.5)  # Brief pause to show success message
                return True

            time.sleep(2)

        progress.update(task, description="[yellow]Timeout waiting for services")
        return False


@click.group()
@click.pass_context
def localdepin(ctx):
    """
    Manage local DePin development stack

    LocalDePin provides a complete local blockchain and storage infrastructure
    for Varity dashboard development. It includes:

    \b
    " Arbitrum L3 blockchain (Nitro dev node)
    " IPFS/Filecoin storage layer
    " Celestia data availability
    " Akash compute simulator (LLM mock)
    " Pinata API mock server
    " PostgreSQL database
    " Redis cache
    " Varity API server
    " VarityKit explorer

    \b
    Quick Start:
      varitykit localdepin start       # Start all services
      varitykit localdepin status      # Check service status
      varitykit localdepin logs        # View logs
      varitykit localdepin stop        # Stop all services

    \b
    Service URLs:
      " Arbitrum RPC:  http://localhost:8547
      " IPFS API:      http://localhost:5001
      " Varity API:    http://localhost:3001
      " Explorer:      http://localhost:8080
    """
    pass


@localdepin.command()
@click.option("--detach", "-d", is_flag=True, help="Run in detached mode (background)")
@click.option("--build", is_flag=True, help="Build images before starting")
@click.option("--wait", is_flag=True, default=True, help="Wait for services to be healthy")
@click.option("--timeout", type=int, default=60, help="Health check timeout in seconds")
@click.pass_context
def start(ctx, detach: bool, build: bool, wait: bool, timeout: int):
    """
    Start local DePin stack

    Starts all LocalDePin services using Docker Compose. This includes
    blockchain, storage, compute, and database services.

    \b
    Examples:
      varitykit localdepin start              # Start and wait for health
      varitykit localdepin start -d           # Start in background
      varitykit localdepin start --build      # Rebuild images first
      varitykit localdepin start --no-wait    # Don't wait for health checks
    """
    logger = (ctx.obj or {}).get("logger") if ctx.obj else None

    # Check prerequisites
    if not check_docker_installed():
        console.print(
            Panel.fit(
                "[bold red]Docker is not installed or not running[/bold red]\n\n"
                "Please install Docker and ensure it's running:\n"
                "• macOS/Windows: Install Docker Desktop\n"
                "• Linux: Install docker and docker-compose packages",
                border_style="red",
            )
        )
        sys.exit(1)

    if not check_docker_compose_installed():
        console.print(
            Panel.fit(
                "[bold red]Docker Compose is not installed[/bold red]\n\n"
                "Please install Docker Compose:\n"
                "• Included with Docker Desktop\n"
                "• Linux: apt-get install docker-compose",
                border_style="red",
            )
        )
        sys.exit(1)

    localdepin_dir = get_localdepin_dir()

    console.print(
        Panel.fit(
            "[bold cyan]Starting LocalDePin Network[/bold cyan]\n\n"
            f"Directory: {localdepin_dir}\n"
            f"Mode: {'Background' if detach else 'Foreground'}\n"
            f"Build: {'Yes' if build else 'No'}",
            border_style="cyan",
        )
    )

    if logger:
        logger.info("Starting LocalDePin network")

    # Build command
    cmd_args = []

    if build:
        console.print("\n[cyan]Building Docker images...[/cyan]")
        build_result = run_docker_compose(["build"], localdepin_dir)
        if build_result.returncode != 0:
            console.print("[red]Failed to build images[/red]")
            sys.exit(1)
        console.print("[green] Images built successfully[/green]\n")

    # Start services
    cmd_args = ["up"]
    if detach:
        cmd_args.append("-d")

    console.print("[cyan]Starting services...[/cyan]")

    result = run_docker_compose(cmd_args, localdepin_dir)

    if result.returncode != 0:
        console.print("[red]Failed to start services[/red]")
        sys.exit(1)

    if detach:
        console.print("[green] Services started in background[/green]\n")

        if wait:
            # Wait for services to be healthy
            core_services = [
                "arbitrum-node",
                "ipfs-node",
                "pinata-mock",
                "akash-simulator",
                "postgres",
                "redis",
            ]

            console.print(
                f"[cyan]Waiting for services to be healthy (timeout: {timeout}s)...[/cyan]\n"
            )

            if wait_for_services(core_services, timeout):
                console.print(
                    Panel.fit(
                        "[bold green] LocalDePin is ready![/bold green]\n\n"
                        "[bold]Service URLs:[/bold]\n"
                        "• Arbitrum RPC:  http://localhost:8547\n"
                        "• IPFS API:      http://localhost:5001\n"
                        "• IPFS Gateway:  http://localhost:8081\n"
                        "• Pinata Mock:   http://localhost:3002\n"
                        "• Akash Sim:     http://localhost:3003\n"
                        "• Celestia RPC:  http://localhost:26658\n"
                        "• Varity API:    http://localhost:3001\n"
                        "• Explorer:      http://localhost:8080\n\n"
                        "[dim]Run 'varitykit localdepin status' to check service health[/dim]",
                        border_style="green",
                    )
                )

                if logger:
                    logger.info("LocalDePin network started successfully")
            else:
                console.print(
                    Panel.fit(
                        "[bold yellow]� Services started but some may not be healthy yet[/bold yellow]\n\n"
                        "Run 'varitykit localdepin status' to check service status\n"
                        "Run 'varitykit localdepin logs <service>' to view logs",
                        border_style="yellow",
                    )
                )
        else:
            console.print("[dim]Skipping health checks (--no-wait)[/dim]")


@localdepin.command()
@click.option("--volumes", "-v", is_flag=True, help="Remove volumes (deletes all data)")
@click.pass_context
def stop(ctx, volumes: bool):
    """
    Stop local DePin stack

    Stops all LocalDePin services. Data is preserved unless --volumes flag is used.

    \b
    Examples:
      varitykit localdepin stop        # Stop services, keep data
      varitykit localdepin stop -v     # Stop services and delete data
    """
    logger = (ctx.obj or {}).get("logger") if ctx.obj else None

    localdepin_dir = get_localdepin_dir()

    if volumes:
        console.print(
            Panel.fit(
                "[bold yellow]� Stopping services and removing volumes[/bold yellow]\n\n"
                "This will delete ALL data including:\n"
                "• Blockchain state\n"
                "• IPFS data\n"
                "• Database\n"
                "• Cache",
                border_style="yellow",
            )
        )

        if not click.confirm("Are you sure?"):
            console.print("[dim]Cancelled[/dim]")
            return

    console.print("[cyan]Stopping LocalDePin services...[/cyan]\n")

    cmd_args = ["down"]
    if volumes:
        cmd_args.append("--volumes")

    result = run_docker_compose(cmd_args, localdepin_dir)

    if result.returncode == 0:
        msg = "Services stopped" + (" and volumes removed" if volumes else "")
        console.print(f"[green] {msg}[/green]")

        if logger:
            logger.info(f"LocalDePin network stopped (volumes_removed={volumes})")
    else:
        console.print("[red]Failed to stop services[/red]")
        sys.exit(1)


@localdepin.command()
@click.option(
    "--format", type=click.Choice(["table", "json"]), default="table", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed status including health checks")
@click.pass_context
def status(ctx, format: str, verbose: bool):
    """
    Show status of local DePin services

    Displays running status, health, and port mappings for all services.

    \b
    Examples:
      varitykit localdepin status           # Table view
      varitykit localdepin status -v        # Include health checks
      varitykit localdepin status --json    # JSON output
    """
    logger = (ctx.obj or {}).get("logger") if ctx.obj else None

    localdepin_dir = get_localdepin_dir()

    # Get service status from docker-compose
    services = get_service_status(localdepin_dir)

    if not services:
        console.print(
            Panel.fit(
                "[bold yellow]No services running[/bold yellow]\n\n"
                "Start LocalDePin with: varitykit localdepin start",
                border_style="yellow",
            )
        )
        return

    if format == "json":
        # JSON output
        output = {"timestamp": datetime.now().isoformat(), "services": services}

        if verbose:
            # Add health check data
            for service_name in services:
                if service_name in SERVICE_HEALTH_CHECKS:
                    health_config = SERVICE_HEALTH_CHECKS.get(service_name, {})
                    if health_config["endpoint"]:
                        is_healthy, msg = check_service_health(
                            service_name, health_config["port"], health_config["endpoint"]
                        )
                        services[service_name]["health"] = {
                            "status": "healthy" if is_healthy else "unhealthy",
                            "message": msg,
                        }

        console.print(json.dumps(output, indent=2))
    else:
        # Table output
        table = Table(
            title="LocalDePin Service Status",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta",
        )

        table.add_column("Service", style="cyan", width=20)
        table.add_column("State", style="white", width=12)
        table.add_column("Status", style="white", width=20)

        if verbose:
            table.add_column("Health", style="white", width=15)
            table.add_column("Port", style="yellow", width=10)

        for service_name, service_data in sorted(services.items()):
            state = service_data["state"]
            status = service_data["status"]

            # Color code state
            if state.lower() == "running":
                state_formatted = f"[green]{state}[/green]"
            else:
                state_formatted = f"[yellow]{state}[/yellow]"

            row = [service_name, state_formatted, status]

            if verbose:
                # Add health check
                if service_name in SERVICE_HEALTH_CHECKS:
                    health_config = SERVICE_HEALTH_CHECKS.get(service_name, {})
                    if health_config["endpoint"]:
                        is_healthy, msg = check_service_health(
                            service_name, health_config["port"], health_config["endpoint"]
                        )

                        if is_healthy:
                            health_str = f"[green] {msg}[/green]"
                        else:
                            health_str = f"[red] {msg}[/red]"

                        row.append(health_str)
                        row.append(str(health_config["port"]))
                    else:
                        row.append("[dim]N/A[/dim]")
                        row.append(str(health_config["port"]))
                else:
                    row.append("[dim]unknown[/dim]")
                    row.append("[dim]N/A[/dim]")

            table.add_row(*row)

        console.print("\n")
        console.print(table)
        console.print("\n")

        if verbose:
            console.print(
                Panel.fit(
                    "[bold]Service URLs:[/bold]\n"
                    "• Arbitrum RPC:  http://localhost:8547\n"
                    "• IPFS API:      http://localhost:5001\n"
                    "• IPFS Gateway:  http://localhost:8081\n"
                    "• Pinata Mock:   http://localhost:3002\n"
                    "• Akash Sim:     http://localhost:3003\n"
                    "• Celestia RPC:  http://localhost:26658\n"
                    "• Varity API:    http://localhost:3001\n"
                    "• Explorer:      http://localhost:8080",
                    border_style="cyan",
                    title="Quick Reference",
                )
            )
            console.print()

    if logger:
        logger.info(f"LocalDePin status checked ({len(services)} services)")


@localdepin.command()
@click.option("--service", "-s", help="Service name (or all services if omitted)")
@click.option("--follow", "-f", is_flag=True, help="Follow log output")
@click.option("--tail", "-n", type=int, default=100, help="Number of lines to show")
@click.pass_context
def logs(ctx, service: Optional[str], follow: bool, tail: int):
    """
    View logs from DePin services

    \b
    Examples:
      varitykit localdepin logs                    # All services
      varitykit localdepin logs -s arbitrum-node   # Specific service
      varitykit localdepin logs -f                 # Follow all logs
      varitykit localdepin logs -s ipfs-node -f    # Follow IPFS logs
    """
    logger = (ctx.obj or {}).get("logger") if ctx.obj else None

    localdepin_dir = get_localdepin_dir()

    cmd_args = ["logs", f"--tail={tail}"]

    if follow:
        cmd_args.append("--follow")

    if service:
        cmd_args.append(service)

    if logger:
        logger.info(f"Viewing logs for {service or 'all services'}")

    # Run logs command (this will stream output)
    run_docker_compose(cmd_args, localdepin_dir)


@localdepin.command()
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def reset(ctx, confirm: bool):
    """
    Reset local DePin stack (delete all data)

    �  WARNING: This will:
    " Stop all services
    " Delete all blockchain data
    " Delete all IPFS data
    " Delete database
    " Delete cache
    " Remove all volumes

    Use this for a completely fresh start.
    """
    logger = (ctx.obj or {}).get("logger") if ctx.obj else None

    if not confirm:
        console.print(
            Panel.fit(
                "[bold red]�  WARNING: Reset LocalDePin[/bold red]\n\n"
                "This will permanently delete:\n"
                "• All blockchain state (transactions, blocks)\n"
                "• All IPFS pins and data\n"
                "• PostgreSQL database\n"
                "• Redis cache\n"
                "• All Docker volumes\n\n"
                "[bold]This action cannot be undone![/bold]",
                border_style="red",
            )
        )

        if not click.confirm("\nAre you absolutely sure you want to reset?"):
            console.print("[dim]Reset cancelled[/dim]")
            return

    localdepin_dir = get_localdepin_dir()

    console.print("\n[yellow]Resetting LocalDePin...[/yellow]\n")

    # Stop and remove everything
    result = run_docker_compose(["down", "--volumes", "--remove-orphans"], localdepin_dir)

    if result.returncode == 0:
        console.print(
            Panel.fit(
                "[bold green] LocalDePin reset complete[/bold green]\n\n"
                "All data has been deleted.\n"
                "Start fresh with: varitykit localdepin start",
                border_style="green",
            )
        )

        if logger:
            logger.info("LocalDePin network reset (all data deleted)")
    else:
        console.print("[red]Failed to reset LocalDePin[/red]")
        sys.exit(1)


if __name__ == "__main__":
    localdepin()
