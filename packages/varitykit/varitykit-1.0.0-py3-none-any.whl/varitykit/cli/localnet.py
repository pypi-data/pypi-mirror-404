"""
Local development network commands for VarityKit
"""

import json
import subprocess
import time
from pathlib import Path

import click
from rich import box
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner
from rich.table import Table


@click.group()
@click.pass_context
def localnet(ctx):
    """
    Manage local development environment

    LocalNet is VarityKit's local development environment for testing before
    deploying to production. It includes:

    \b
    • Local Varity server (Chain ID: 421614)
    • Decentralized storage
    • Data availability layer
    • PostgreSQL + Redis
    • Mock services
    • Varity API server
    • Development dashboard

    \b
    Quick Start:
      varitykit localnet start    # Start development environment
      varitykit localnet status   # Check if running
      varitykit localnet stop     # Stop environment
      varitykit localnet reset    # Clear all data and restart

    \b
    Pre-funded Test Accounts:
      10 test accounts with development credits
      See: varitykit localnet accounts
    """
    pass


def get_localdepin_dir() -> Path:
    """Get the LocalDePin directory path"""
    # Try to find localdepin directory relative to this file
    cli_dir = Path(__file__).parent.parent.parent  # Go up to varitykit-cli/
    localdepin_dir = cli_dir / "localdepin"

    if not localdepin_dir.exists():
        # Fallback: look in current directory
        localdepin_dir = Path.cwd() / "localdepin"

    return localdepin_dir


def run_script(script_name: str, console: Console, logger) -> int:
    """Run a LocalDePin management script"""
    localdepin_dir = get_localdepin_dir()
    script_path = localdepin_dir / "scripts" / script_name

    if not script_path.exists():
        console.print(
            Panel.fit(
                f"[bold red]Script not found[/bold red]\n"
                f"Expected: {script_path}\n\n"
                f"LocalDePin directory: {localdepin_dir}\n"
                f"Make sure you're in a VarityKit project or the CLI directory.",
                border_style="red",
            )
        )
        return 1

    try:
        # Run the bash script
        result = subprocess.run(
            ["bash", str(script_path)],
            cwd=localdepin_dir,
            capture_output=False,  # Let output stream to console
            text=True,
        )

        return result.returncode

    except Exception as e:
        console.print(
            Panel.fit(f"[bold red]Failed to run script[/bold red]\n{str(e)}", border_style="red")
        )
        logger.error(f"Script execution failed: {e}")
        return 1


@localnet.command()
@click.pass_context
def start(ctx):
    """
    Start local DePin network

    Starts all 9 services:
    - Arbitrum L3 blockchain node
    - IPFS/Filecoin storage
    - Celestia DA layer
    - PostgreSQL database
    - Redis cache
    - Pinata mock service
    - Akash compute simulator
    - Varity API server
    - Block explorer

    \b
    First-time startup may take 2-3 minutes while Docker pulls images.
    Subsequent starts are faster (~30-60 seconds).

    \b
    After starting, services will be available at:
      • Arbitrum L3:  http://localhost:8547
      • IPFS API:     http://localhost:5001
      • Explorer:     http://localhost:8080
      • Varity API:   http://localhost:3001
    """
    console = Console()
    logger = ctx.obj["logger"]

    console.print(
        Panel.fit(
            "[bold cyan]Starting LocalDePin Network[/bold cyan]\n"
            "This may take 2-3 minutes on first run...",
            border_style="cyan",
        )
    )

    logger.info("Starting LocalDePin network...")

    result_code = run_script("start.sh", console, logger)

    if result_code == 0:
        logger.info("LocalDePin network started successfully")
    else:
        logger.error("LocalDePin network failed to start")
        ctx.exit(result_code)


@localnet.command()
@click.pass_context
def stop(ctx):
    """
    Stop local DePin network

    Stops all running services while preserving data volumes.
    Your blockchain state, IPFS data, and database will be retained.

    To completely reset the network, use 'varitykit localnet reset'
    """
    console = Console()
    logger = ctx.obj["logger"]

    console.print("[yellow]Stopping LocalDePin network...[/yellow]")
    logger.info("Stopping LocalDePin network...")

    result_code = run_script("stop.sh", console, logger)

    if result_code == 0:
        console.print("\n[green]✅ LocalDePin network stopped[/green]\n")
        logger.info("LocalDePin network stopped")
    else:
        logger.error("Failed to stop LocalDePin network")
        ctx.exit(result_code)


@localnet.command()
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def reset(ctx, confirm):
    """
    Reset local DePin network to clean state

    ⚠️  WARNING: This will DELETE ALL DATA including:
    - Blockchain state (all transactions, blocks, accounts)
    - IPFS pins and stored files
    - PostgreSQL database
    - Redis cache

    This cannot be undone!

    After reset, the network will restart with fresh state and
    pre-funded test accounts.
    """
    console = Console()
    logger = ctx.obj["logger"]

    if not confirm:
        console.print(
            Panel.fit(
                "[bold yellow]⚠️  Reset LocalDePin Network[/bold yellow]\n\n"
                "This will DELETE ALL DATA:\n"
                "  • Blockchain transactions and state\n"
                "  • IPFS stored files\n"
                "  • Database records\n"
                "  • Cache data\n\n"
                "[bold red]This action cannot be undone![/bold red]",
                border_style="yellow",
            )
        )

        if not click.confirm("\nAre you sure you want to reset?"):
            console.print("[dim]Reset cancelled[/dim]")
            return

    console.print("[yellow]Resetting LocalDePin network...[/yellow]")
    logger.info("Resetting LocalDePin network...")

    result_code = run_script("reset.sh", console, logger)

    if result_code == 0:
        logger.info("LocalDePin network reset successfully")
    else:
        logger.error("LocalDePin network reset failed")
        ctx.exit(result_code)


@localnet.command()
@click.pass_context
def status(ctx):
    """
    Show status of local DePin network

    Displays which services are running, their health status,
    and available endpoints.
    """
    console = Console()
    logger = ctx.obj["logger"]

    logger.info("Checking LocalDePin network status...")

    result_code = run_script("status.sh", console, logger)

    if result_code != 0:
        logger.error("Failed to check LocalDePin network status")
        ctx.exit(result_code)


@localnet.command()
@click.option("--follow", "-f", is_flag=True, help="Follow log output")
@click.option("--service", "-s", help="Show logs for specific service")
@click.option("--tail", "-n", default=100, help="Number of lines to show")
@click.pass_context
def logs(ctx, follow, service, tail):
    """
    View logs from local DePin network services

    \b
    Examples:
      varitykit localnet logs                    # Show all logs
      varitykit localnet logs -f                 # Follow all logs
      varitykit localnet logs -s arbitrum-node   # Specific service
      varitykit localnet logs -f -s ipfs-node    # Follow specific service

    \b
    Available services:
      • arbitrum-node    - Blockchain node
      • ipfs-node        - IPFS storage
      • celestia-node    - Celestia DA
      • postgres         - Database
      • redis            - Cache
      • pinata-mock      - Pinata mock API
      • akash-simulator  - Akash mock compute
      • varity-api-local - Varity API server
      • varitykit-explorer - Block explorer
    """
    console = Console()
    logger = ctx.obj["logger"]

    localdepin_dir = get_localdepin_dir()

    if not localdepin_dir.exists():
        console.print(
            Panel.fit(
                "[bold red]LocalDePin directory not found[/bold red]\n"
                f"Expected: {localdepin_dir}",
                border_style="red",
            )
        )
        ctx.exit(1)

    # Build docker-compose logs command
    cmd = ["docker-compose", "logs", f"--tail={tail}"]

    if follow:
        cmd.append("--follow")

    if service:
        cmd.append(service)

    try:
        subprocess.run(cmd, cwd=localdepin_dir, check=False)
    except KeyboardInterrupt:
        console.print("\n[dim]Stopped following logs[/dim]")
    except Exception as e:
        console.print(
            Panel.fit(f"[bold red]Failed to show logs[/bold red]\n{str(e)}", border_style="red")
        )
        logger.error(f"Failed to show logs: {e}")
        ctx.exit(1)


@localnet.command()
@click.pass_context
def accounts(ctx):
    """
    List pre-funded test accounts

    Shows all 10 pre-funded accounts with their addresses,
    private keys, and balances.

    These accounts are automatically created when LocalNet starts
    and can be used for testing without requesting testnet funds.
    """
    console = Console()
    logger = ctx.obj["logger"]

    localdepin_dir = get_localdepin_dir()
    accounts_file = localdepin_dir / "config" / "test-accounts.json"

    if not accounts_file.exists():
        console.print(
            Panel.fit(
                "[bold red]Test accounts file not found[/bold red]\n" f"Expected: {accounts_file}",
                border_style="red",
            )
        )
        ctx.exit(1)

    try:
        with open(accounts_file, "r") as f:
            accounts_data = json.load(f)

        console.print(
            Panel.fit(
                "[bold cyan]LocalDePin Test Accounts[/bold cyan]\n"
                "Pre-funded accounts available on the local network",
                border_style="cyan",
            )
        )

        # Create table
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
        table.add_column("#", style="cyan", width=5)
        table.add_column("Name", style="white", width=20)
        table.add_column("Address", style="yellow", width=45)
        table.add_column("Balance", style="green", width=15)

        for account in accounts_data.get("accounts", []):
            table.add_row(
                str(account.get("index", "")),
                account.get("name", "Unknown"),
                account.get("address", "N/A"),
                f"{account.get('balance', 0):,} ETH",
            )

        console.print("\n")
        console.print(table)
        console.print()

        console.print("[bold]To view private keys:[/bold]")
        console.print(f"  [cyan]cat {accounts_file}[/cyan]\n")

        console.print("[bold yellow]⚠️  Security Warning:[/bold yellow]")
        console.print("  These keys are for LOCAL TESTING ONLY")
        console.print("  NEVER use these keys on testnet or mainnet")
        console.print("  NEVER send real funds to these addresses\n")

        logger.info("Displayed test accounts")

    except Exception as e:
        console.print(
            Panel.fit(
                f"[bold red]Failed to load test accounts[/bold red]\n{str(e)}", border_style="red"
            )
        )
        logger.error(f"Failed to load test accounts: {e}")
        ctx.exit(1)


@localnet.command()
@click.pass_context
def info(ctx):
    """
    Show LocalDePin network information

    Displays configuration, endpoints, and system requirements.
    """
    console = Console()
    logger = ctx.obj["logger"]

    localdepin_dir = get_localdepin_dir()

    # Network info
    table = Table(
        title="LocalDePin Network Information",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Service", style="cyan", width=25)
    table.add_column("Endpoint", style="yellow", width=35)
    table.add_column("Port", style="green", width=10)

    services = [
        ("Arbitrum L3 RPC", "http://localhost:8547", "8547"),
        ("Arbitrum L3 WebSocket", "ws://localhost:8548", "8548"),
        ("IPFS API", "http://localhost:5001", "5001"),
        ("IPFS Gateway", "http://localhost:8081", "8081"),
        ("Pinata Mock API", "http://localhost:3002", "3002"),
        ("Akash Simulator", "http://localhost:3003", "3003"),
        ("Celestia RPC", "http://localhost:26658", "26658"),
        ("Celestia Gateway", "http://localhost:26659", "26659"),
        ("Varity API Server", "http://localhost:3001", "3001"),
        ("VarityKit Explorer", "http://localhost:8080", "8080"),
        ("PostgreSQL", "localhost:5432", "5432"),
        ("Redis", "localhost:6379", "6379"),
    ]

    for service, endpoint, port in services:
        table.add_row(service, endpoint, port)

    console.print("\n")
    console.print(table)
    console.print()

    # Configuration
    console.print(
        Panel.fit(
            "[bold cyan]Configuration[/bold cyan]\n\n"
            f"[bold]LocalDePin Directory:[/bold]\n  {localdepin_dir}\n\n"
            f"[bold]Docker Compose File:[/bold]\n  {localdepin_dir / 'docker-compose.yml'}\n\n"
            f"[bold]Test Accounts:[/bold]\n  {localdepin_dir / 'config' / 'test-accounts.json'}\n\n"
            "[bold]Chain ID:[/bold] 421614 (Arbitrum Sepolia)",
            border_style="cyan",
        )
    )

    # Requirements
    console.print(
        Panel.fit(
            "[bold cyan]System Requirements[/bold cyan]\n\n"
            "[bold]Required:[/bold]\n"
            "  • Docker 20.10+\n"
            "  • Docker Compose 1.29+\n"
            "  • 8GB RAM minimum\n"
            "  • 20GB disk space\n\n"
            "[bold]Recommended:[/bold]\n"
            "  • 16GB RAM\n"
            "  • 50GB disk space\n"
            "  • SSD storage",
            border_style="cyan",
        )
    )

    console.print()
    logger.info("Displayed network information")


@localnet.command()
@click.option("--name", default="localnet-snapshot", help="Snapshot name")
@click.pass_context
def snapshot(ctx, name):
    """
    Create a snapshot of current network state

    Saves the current blockchain state, database, and IPFS data
    so you can restore it later with 'varitykit localnet restore'

    \b
    Example:
      varitykit localnet snapshot --name my-test-state
      # Make changes, test things
      varitykit localnet restore --name my-test-state
    """
    console = Console()
    logger = ctx.obj["logger"]

    localdepin_dir = get_localdepin_dir()

    console.print(
        Panel.fit(
            "[bold cyan]Creating Network Snapshot[/bold cyan]\n" f"Name: {name}",
            border_style="cyan",
        )
    )

    try:
        # Create snapshots directory
        snapshots_dir = localdepin_dir / "snapshots"
        snapshots_dir.mkdir(exist_ok=True)

        snapshot_dir = snapshots_dir / name
        if snapshot_dir.exists():
            console.print(
                Panel.fit(
                    f"[bold yellow]Snapshot '{name}' already exists[/bold yellow]\n"
                    "Use a different name or delete the existing snapshot",
                    border_style="yellow",
                )
            )
            ctx.exit(1)

        snapshot_dir.mkdir()

        # Export docker volumes
        console.print("[yellow]Exporting blockchain state...[/yellow]")
        subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "-v",
                "localdepin_arbitrum-data:/data",
                "-v",
                f"{snapshot_dir}:/backup",
                "alpine",
                "tar",
                "czf",
                "/backup/arbitrum-data.tar.gz",
                "-C",
                "/data",
                ".",
            ],
            check=True,
            capture_output=True,
        )

        console.print("[yellow]Exporting IPFS data...[/yellow]")
        subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "-v",
                "localdepin_ipfs-data:/data",
                "-v",
                f"{snapshot_dir}:/backup",
                "alpine",
                "tar",
                "czf",
                "/backup/ipfs-data.tar.gz",
                "-C",
                "/data",
                ".",
            ],
            check=True,
            capture_output=True,
        )

        console.print("[yellow]Exporting PostgreSQL data...[/yellow]")
        subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "-v",
                "localdepin_postgres-data:/data",
                "-v",
                f"{snapshot_dir}:/backup",
                "alpine",
                "tar",
                "czf",
                "/backup/postgres-data.tar.gz",
                "-C",
                "/data",
                ".",
            ],
            check=True,
            capture_output=True,
        )

        # Save metadata
        metadata = {
            "name": name,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "chain_id": 421614,
        }

        with open(snapshot_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

        console.print("\n")
        console.print(
            Panel.fit(
                f"[bold green]✅ Snapshot '{name}' created successfully[/bold green]\n\n"
                f"Location: {snapshot_dir}\n"
                f"Size: {sum(f.stat().st_size for f in snapshot_dir.glob('*')) // 1024 // 1024}MB",
                border_style="green",
            )
        )

        logger.info(f"Created snapshot: {name}")

    except subprocess.CalledProcessError as e:
        console.print(
            Panel.fit(
                f"[bold red]Failed to create snapshot[/bold red]\n{e.stderr.decode() if e.stderr else str(e)}",
                border_style="red",
            )
        )
        logger.error(f"Snapshot creation failed: {e}")
        ctx.exit(1)

    except Exception as e:
        console.print(
            Panel.fit(
                f"[bold red]Failed to create snapshot[/bold red]\n{str(e)}", border_style="red"
            )
        )
        logger.error(f"Snapshot creation failed: {e}")
        ctx.exit(1)


@localnet.command()
@click.option("--name", default="localnet-snapshot", help="Snapshot name")
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def restore(ctx, name, confirm):
    """
    Restore network state from a snapshot

    ⚠️  This will replace current state with the snapshot.
    Make sure to create a snapshot of current state if you want to keep it.
    """
    console = Console()
    logger = ctx.obj["logger"]

    localdepin_dir = get_localdepin_dir()
    snapshot_dir = localdepin_dir / "snapshots" / name

    if not snapshot_dir.exists():
        console.print(
            Panel.fit(
                f"[bold red]Snapshot '{name}' not found[/bold red]\n"
                "Use 'varitykit localnet snapshot --name <name>' to create one",
                border_style="red",
            )
        )
        ctx.exit(1)

    if not confirm:
        console.print(
            Panel.fit(
                f"[bold yellow]⚠️  Restore Snapshot '{name}'[/bold yellow]\n\n"
                "This will REPLACE current network state with the snapshot.\n\n"
                "[bold red]Current data will be lost![/bold red]",
                border_style="yellow",
            )
        )

        if not click.confirm("\nAre you sure you want to restore?"):
            console.print("[dim]Restore cancelled[/dim]")
            return

    console.print(f"[yellow]Restoring snapshot '{name}'...[/yellow]")

    try:
        # Stop network first
        console.print("[yellow]Stopping network...[/yellow]")
        run_script("stop.sh", console, logger)

        # Restore volumes
        console.print("[yellow]Restoring blockchain state...[/yellow]")
        subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "-v",
                "localdepin_arbitrum-data:/data",
                "-v",
                f"{snapshot_dir}:/backup",
                "alpine",
                "sh",
                "-c",
                "rm -rf /data/* && tar xzf /backup/arbitrum-data.tar.gz -C /data",
            ],
            check=True,
            capture_output=True,
        )

        console.print("[yellow]Restoring IPFS data...[/yellow]")
        subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "-v",
                "localdepin_ipfs-data:/data",
                "-v",
                f"{snapshot_dir}:/backup",
                "alpine",
                "sh",
                "-c",
                "rm -rf /data/* && tar xzf /backup/ipfs-data.tar.gz -C /data",
            ],
            check=True,
            capture_output=True,
        )

        console.print("[yellow]Restoring PostgreSQL data...[/yellow]")
        subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "-v",
                "localdepin_postgres-data:/data",
                "-v",
                f"{snapshot_dir}:/backup",
                "alpine",
                "sh",
                "-c",
                "rm -rf /data/* && tar xzf /backup/postgres-data.tar.gz -C /data",
            ],
            check=True,
            capture_output=True,
        )

        # Restart network
        console.print("[yellow]Restarting network...[/yellow]")
        run_script("start.sh", console, logger)

        console.print("\n")
        console.print(
            Panel.fit(
                f"[bold green]✅ Snapshot '{name}' restored successfully[/bold green]",
                border_style="green",
            )
        )

        logger.info(f"Restored snapshot: {name}")

    except subprocess.CalledProcessError as e:
        console.print(
            Panel.fit(
                f"[bold red]Failed to restore snapshot[/bold red]\n{e.stderr.decode() if e.stderr else str(e)}",
                border_style="red",
            )
        )
        logger.error(f"Snapshot restore failed: {e}")
        ctx.exit(1)

    except Exception as e:
        console.print(
            Panel.fit(
                f"[bold red]Failed to restore snapshot[/bold red]\n{str(e)}", border_style="red"
            )
        )
        logger.error(f"Snapshot restore failed: {e}")
        ctx.exit(1)
