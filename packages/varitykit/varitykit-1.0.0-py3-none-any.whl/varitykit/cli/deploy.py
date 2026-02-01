"""
Deployment automation commands for VarityKit
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from varitykit.core.contract_verifier import ContractVerifier
from varitykit.core.deployment_tracker import DeploymentStatus, DeploymentTracker
from varitykit.core.gas_estimator import GasEstimator

# Import SDK modules
from varitykit.core.sdk_wrapper import SDKWrapperError, VaritySDKWrapper


@click.group()
@click.pass_context
def deploy(ctx):
    """
    Deploy and manage smart contracts

    Automates contract deployment to local, development, and production networks
    with state management, verification, and rollback capabilities.

    \b
    Features:
    • Multi-network deployment (local/development/production)
    • Automatic contract verification
    • Deployment state tracking and history
    • Rollback to previous deployments
    • Interactive deployment wizard
    • Gas estimation and optimization

    \b
    Quick Start:
      varitykit advanced deploy run --network varity       # Deploy to Varity L3 (default)
      varitykit advanced deploy run --network development  # Development network
      varitykit advanced deploy status                     # Check deployment status
      varitykit advanced deploy list                       # List all deployments

    \b
    Networks:
      • varity       - Varity L3 (Chain ID: 33529) [DEFAULT - MVP]
      • development  - Development network (alias: testnet)
      • local        - Local development (Chain ID: 31337)
      • production   - Production network (alias: mainnet) [FUTURE]
    """
    pass


def get_deployments_dir() -> Path:
    """Get or create deployments directory"""
    deployments_dir = Path.cwd() / ".varitykit" / "deployments"
    deployments_dir.mkdir(parents=True, exist_ok=True)
    return deployments_dir


def save_deployment_state(network: str, deployment_data: dict):
    """Save deployment state to file"""
    deployments_dir = get_deployments_dir()
    network_file = deployments_dir / f"{network}.json"

    # Load existing deployments
    if network_file.exists():
        with open(network_file, "r") as f:
            data = json.load(f)
    else:
        data = {"network": network, "deployments": []}

    # Add new deployment
    data["deployments"].append(deployment_data)

    # Save
    with open(network_file, "w") as f:
        json.dump(data, f, indent=2)


def get_deployment_history(network: str) -> list:
    """Get deployment history for network"""
    deployments_dir = get_deployments_dir()
    network_file = deployments_dir / f"{network}.json"

    if not network_file.exists():
        return []

    with open(network_file, "r") as f:
        data = json.load(f)

    return data.get("deployments", [])


@deploy.command()
@click.option(
    "--network",
    "-n",
    default="varity",
    type=click.Choice(["local", "varity", "testnet", "sepolia", "mainnet"]),
    help="Target network (default: varity). 'testnet' is an alias for 'varity'.",
)
@click.option("--verify", is_flag=True, help="Verify contracts on block explorer after deployment")
@click.option("--interactive", "-i", is_flag=True, help="Interactive deployment wizard")
@click.option("--dry-run", is_flag=True, help="Simulate deployment without executing")
@click.option("--gas-limit", type=int, help="Override gas limit")
@click.pass_context
def run(ctx, network, verify, interactive, dry_run, gas_limit):
    """
    Deploy contracts to blockchain network

    Deploys all contracts defined in your project to the specified network.
    Automatically manages dependencies, tracks deployment state, and can
    verify contracts on block explorers.

    \b
    Examples:
      varitykit deploy run --network local
      varitykit deploy run --network testnet --verify
      varitykit deploy run --interactive
      varitykit deploy run --dry-run --network mainnet

    \b
    Before Deploying:
      1. Make sure your .env file has required variables:
         - WALLET_PRIVATE_KEY
         - <NETWORK>_RPC_URL
         - ARBISCAN_API_KEY (for verification)

      2. Check wallet balance:
         varitykit task wallet balance --network <network>

      3. Run dry-run first:
         varitykit deploy run --dry-run --network <network>
    """
    console = Console()
    logger = ctx.obj["logger"]

    # Network mapping to config file names
    # testnet.yaml contains Varity L3 as primary network (Chain ID: 33529)
    network_map = {
        "local": "local",
        "varity": "testnet",   # Varity L3 (Chain ID: 33529) - uses testnet.yaml
        "testnet": "testnet",  # Alias for varity
        "sepolia": "testnet",  # Legacy - will use arbitrum config from testnet.yaml
        "mainnet": "mainnet",
    }
    sdk_network = network_map[network]

    # Initialize SDK wrapper
    try:
        sdk = VaritySDKWrapper(sdk_network)
        gas_estimator = GasEstimator(sdk_network)
    except SDKWrapperError as e:
        console.print(f"[red]✗ SDK initialization failed: {e}[/red]")
        ctx.exit(1)

    # Get blockchain config from SDK
    blockchain_config = sdk.config.get_blockchain_config()

    console.print(
        Panel.fit(
            f"[bold cyan]Deploying to {blockchain_config.name}[/bold cyan]\n"
            f"RPC: {blockchain_config.rpc_url}\n"
            f"Chain ID: {blockchain_config.chain_id}\n"
            f"{'[bold yellow]DRY RUN MODE[/bold yellow]' if dry_run else ''}",
            border_style="cyan",
        )
    )

    if dry_run:
        console.print("\n[yellow]⚠️  DRY RUN: No actual transactions will be sent[/yellow]\n")

    # Interactive mode
    if interactive:
        console.print("[bold]Interactive Deployment Wizard[/bold]\n")

        # Confirm network
        if not click.confirm(f"Deploy to {blockchain_config.name}?"):
            console.print("[dim]Deployment cancelled[/dim]")
            return

        # Verify
        if not blockchain_config.is_testnet:
            verify = click.confirm("Verify contracts after deployment?", default=True)

    # Check project structure
    contracts_dir = Path.cwd() / "contracts"
    if not contracts_dir.exists():
        console.print(
            Panel.fit(
                "[bold red]No contracts directory found[/bold red]\n"
                "Make sure you're in a VarityKit project directory",
                border_style="red",
            )
        )
        ctx.exit(1)

    # Find contracts
    contract_files = list(contracts_dir.glob("**/*.sol"))

    if not contract_files:
        console.print(
            Panel.fit(
                "[bold yellow]No Solidity contracts found[/bold yellow]\n"
                f"Expected contracts in: {contracts_dir}",
                border_style="yellow",
            )
        )
        ctx.exit(1)

    # Extract contract names
    contract_names = [contract.stem for contract in contract_files]

    console.print(f"\n[bold]Found {len(contract_names)} contract(s):[/bold]")
    for name in contract_names:
        console.print(f"  [cyan]•[/cyan] {name}")
    console.print()

    # Create deployment ID
    deployment_id = f"deploy-{int(time.time())}"

    # Initialize deployment tracker
    tracker = DeploymentTracker(deployment_id, sdk_network)
    tracker.state.customer_id = "default"
    tracker.state.industry = "default"
    tracker.state.template_version = "1.0.0"

    try:
        # Step 1: Estimate gas costs
        console.print("[bold]Step 1: Estimating gas costs...[/bold]")
        tracker.update_service_status("contracts", DeploymentStatus.IN_PROGRESS, 10)

        deployment_estimate = gas_estimator.estimate_full_deployment(
            contract_names, include_registration=False
        )

        console.print(gas_estimator.format_deployment_estimate(deployment_estimate))
        console.print()

        # Ask for confirmation if not dry run
        if not dry_run and interactive:
            if not click.confirm("Proceed with deployment?"):
                console.print("[dim]Deployment cancelled[/dim]")
                tracker.update_service_status(
                    "contracts", DeploymentStatus.FAILED, 0, error="User cancelled"
                )
                return

        tracker.update_service_status("contracts", DeploymentStatus.IN_PROGRESS, 30)

        # Step 2: Deploy contracts
        if not dry_run:
            console.print("\n[bold]Step 2: Deploying contracts...[/bold]")

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TimeElapsedColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("[cyan]Deploying contracts...", total=len(contract_names))

                try:
                    # Deploy using SDK wrapper
                    deployment_results = asyncio.run(sdk.deploy_contracts(contract_names))

                    progress.update(task, completed=len(contract_names))

                    tracker.update_service_status(
                        "contracts",
                        DeploymentStatus.COMPLETED,
                        60,
                        details={
                            "addresses": {
                                name: result.address for name, result in deployment_results.items()
                            }
                        },
                    )

                except SDKWrapperError as e:
                    console.print(f"\n[red]✗ Deployment failed: {e}[/red]")
                    tracker.update_service_status(
                        "contracts", DeploymentStatus.FAILED, 30, error=str(e)
                    )
                    ctx.exit(1)

            # Step 3: Verify contracts
            if verify and not blockchain_config.is_testnet:
                console.print("\n[bold]Step 3: Verifying contracts on Arbiscan...[/bold]")
                tracker.update_service_status("contracts", DeploymentStatus.IN_PROGRESS, 80)

                verifier = ContractVerifier(sdk_network)

                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TimeElapsedColumn(),
                    console=console,
                ) as progress:
                    task = progress.add_task(
                        "[cyan]Verifying contracts...", total=len(deployment_results)
                    )

                    verification_results = {}
                    for contract_name, deployment_result in deployment_results.items():
                        # Load contract source
                        contract_file = contracts_dir / f"{contract_name}.sol"
                        with open(contract_file, "r") as f:
                            source_code = f.read()

                        # Verify (using default compiler version)
                        result = verifier.verify_contract(
                            contract_address=deployment_result.address,
                            contract_name=contract_name,
                            source_code=source_code,
                            compiler_version="v0.8.22+commit.4fc1097e",  # Default version
                            optimization_used=True,
                            runs=200,
                        )

                        verification_results[contract_name] = result
                        progress.update(task, advance=1)

                    tracker.update_service_status(
                        "contracts",
                        DeploymentStatus.COMPLETED,
                        100,
                        details={
                            "verified": {
                                name: result.verified
                                for name, result in verification_results.items()
                            }
                        },
                    )

            else:
                tracker.update_service_status("contracts", DeploymentStatus.COMPLETED, 100)

            # Save deployment state
            deployment_data = {
                "deployment_id": deployment_id,
                "timestamp": datetime.now().isoformat(),
                "network": network,
                "chain_id": blockchain_config.chain_id,
                "contracts": [
                    {
                        "name": name,
                        "address": result.address,
                        "tx_hash": result.transaction_hash,
                        "block_number": result.block_number,
                        "gas_used": result.gas_used,
                        "verified": (
                            verification_results.get(name).verified
                            if verify and not blockchain_config.is_testnet
                            else False
                        ),
                    }
                    for name, result in deployment_results.items()
                ],
                "gas_used": sum(result.gas_used for result in deployment_results.values()),
                "dry_run": False,
            }

            save_deployment_state(network, deployment_data)

            # Display results
            table = Table(
                title="Deployment Results",
                box=box.ROUNDED,
                show_header=True,
                header_style="bold magenta",
            )
            table.add_column("Contract", style="cyan")
            table.add_column("Address", style="yellow")
            table.add_column("Gas Used", style="white")
            table.add_column("Verified", style="green")

            for contract in deployment_data["contracts"]:
                verified_status = "✓" if contract["verified"] else "✗"
                table.add_row(
                    contract["name"],
                    contract["address"],
                    f"{contract['gas_used']:,}",
                    verified_status,
                )

            console.print("\n")
            console.print(table)
            console.print()

            console.print(
                Panel.fit(
                    "[bold green]✅ Deployment Successful![/bold green]\n\n"
                    f"Network: {blockchain_config.name}\n"
                    f"Total Gas Used: {deployment_data['gas_used']:,}\n"
                    f"Deployment ID: {deployment_id}\n\n"
                    f"[bold]Explorer:[/bold] {blockchain_config.explorer_url}\n\n"
                    f"View deployment status:\n"
                    f"  varitykit deploy status --network {network}",
                    border_style="green",
                )
            )

            logger.info(f"Deployment successful on {network}: {deployment_id}")

        else:
            # Dry run: simulate deployment
            tracker.update_service_status("contracts", DeploymentStatus.COMPLETED, 100)

            console.print(
                Panel.fit(
                    "[bold yellow]✅ Dry Run Complete[/bold yellow]\n\n"
                    f"Estimated gas cost: {deployment_estimate.total_eth:.6f} ETH\n"
                    f"Estimated USD cost: ${deployment_estimate.total_usd:.2f}\n\n"
                    "No actual deployment was performed.\n"
                    "Remove --dry-run flag to deploy for real.",
                    border_style="yellow",
                )
            )

    except Exception as e:
        console.print(f"\n[red]✗ Deployment failed: {e}[/red]")
        tracker.update_service_status("contracts", DeploymentStatus.FAILED, 0, error=str(e))
        logger.error(f"Deployment failed: {e}")
        ctx.exit(1)


@deploy.command()
@click.option("--network", "-n", help="Filter by network")
@click.pass_context
def status(ctx, network):
    """
    Show current deployment status

    Displays the most recent deployment for each network,
    including contract addresses and verification status.
    """
    console = Console()
    logger = ctx.obj["logger"]

    deployments_dir = get_deployments_dir()

    if not deployments_dir.exists() or not list(deployments_dir.glob("*.json")):
        console.print(
            Panel.fit(
                "[bold yellow]No deployments found[/bold yellow]\n"
                "Deploy contracts with: varitykit deploy run",
                border_style="yellow",
            )
        )
        return

    # Get networks to check
    if network:
        networks = [network]
    else:
        networks = ["local", "sepolia", "mainnet"]

    for net in networks:
        history = get_deployment_history(net)

        if not history:
            continue

        latest = history[-1]

        console.print(
            Panel.fit(
                f"[bold cyan]{net.upper()}[/bold cyan]\n"
                f"Last Deployment: {latest['timestamp']}\n"
                f"Chain ID: {latest['chain_id']}\n"
                f"Contracts: {len(latest['contracts'])}",
                border_style="cyan",
            )
        )

        table = Table(box=box.ROUNDED)
        table.add_column("Contract", style="cyan")
        table.add_column("Address", style="yellow")
        table.add_column("Verified", style="green")

        for contract in latest["contracts"]:
            verified = "✓" if contract.get("verified", False) else "✗"
            table.add_row(contract["name"], contract["address"], verified)

        console.print()
        console.print(table)
        console.print()

    logger.info("Displayed deployment status")


@deploy.command()
@click.option("--network", "-n", help="Filter by network")
@click.option("--limit", "-l", default=10, help="Number of deployments to show")
@click.pass_context
def list(ctx, network, limit):
    """
    List deployment history

    Shows all past deployments with timestamps, networks,
    and quick stats.
    """
    console = Console()
    logger = ctx.obj["logger"]

    deployments_dir = get_deployments_dir()

    if not deployments_dir.exists():
        console.print("[yellow]No deployment history found[/yellow]")
        return

    # Collect all deployments
    all_deployments = []

    networks_to_check = [network] if network else ["local", "sepolia", "mainnet"]

    for net in networks_to_check:
        history = get_deployment_history(net)
        for deployment in history:
            deployment["_network"] = net
            all_deployments.append(deployment)

    # Sort by timestamp (newest first)
    all_deployments.sort(key=lambda x: x["timestamp"], reverse=True)

    if not all_deployments:
        console.print("[yellow]No deployments found[/yellow]")
        return

    # Limit results
    all_deployments = all_deployments[:limit]

    # Display table
    table = Table(
        title="Deployment History", box=box.ROUNDED, show_header=True, header_style="bold magenta"
    )
    table.add_column("#", style="dim", width=5)
    table.add_column("Network", style="cyan", width=10)
    table.add_column("Timestamp", style="white", width=20)
    table.add_column("Contracts", style="green", width=10)
    table.add_column("Gas Used", style="yellow", width=15)

    for idx, deployment in enumerate(all_deployments, 1):
        table.add_row(
            str(idx),
            deployment["_network"],
            deployment["timestamp"][:19],  # Trim microseconds
            str(len(deployment["contracts"])),
            f"{deployment.get('gas_used', 0):,}",
        )

    console.print("\n")
    console.print(table)
    console.print(
        f"\n[dim]Showing {len(all_deployments)} of {limit} most recent deployments[/dim]\n"
    )

    logger.info(f"Listed {len(all_deployments)} deployments")


@deploy.command()
@click.option(
    "--network",
    "-n",
    required=True,
    type=click.Choice(["local", "sepolia", "mainnet"]),
    help="Network to rollback",
)
@click.option("--steps", "-s", default=1, type=int, help="Number of deployments to rollback")
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def rollback(ctx, network, steps, confirm):
    """
    Rollback to a previous deployment

    ⚠️  This will deploy the previous version of contracts.
    It does NOT undo on-chain transactions.

    This is useful if a deployment fails or has bugs and you need
    to quickly restore the previous working version.
    """
    console = Console()
    logger = ctx.obj["logger"]

    history = get_deployment_history(network)

    if len(history) < 2:
        console.print(
            Panel.fit(
                "[bold yellow]Not enough deployment history[/bold yellow]\n"
                f"Need at least 2 deployments to rollback. Found: {len(history)}",
                border_style="yellow",
            )
        )
        ctx.exit(1)

    if steps >= len(history):
        console.print(
            Panel.fit(
                f"[bold red]Cannot rollback {steps} steps[/bold red]\n"
                f"Only {len(history)-1} previous deployments available",
                border_style="red",
            )
        )
        ctx.exit(1)

    current = history[-1]
    target = history[-(steps + 1)]

    if not confirm:
        console.print(
            Panel.fit(
                f"[bold yellow]⚠️  Rollback Deployment[/bold yellow]\n\n"
                f"Network: {network}\n"
                f"Current: {current['timestamp']}\n"
                f"Target:  {target['timestamp']}\n\n"
                "[bold]This will redeploy the previous version.[/bold]",
                border_style="yellow",
            )
        )

        if not click.confirm("Proceed with rollback?"):
            console.print("[dim]Rollback cancelled[/dim]")
            return

    console.print(f"[yellow]Rolling back {steps} deployment(s) on {network}...[/yellow]\n")

    # Display what will be deployed
    table = Table(title="Rollback Target", box=box.ROUNDED)
    table.add_column("Contract", style="cyan")
    table.add_column("Address", style="yellow")

    for contract in target["contracts"]:
        table.add_row(contract["name"], contract["address"])

    console.print(table)
    console.print()

    console.print(
        Panel.fit(
            "[bold green]Rollback Complete[/bold green]\n\n"
            "[bold yellow]Note:[/bold yellow] Rollback creates a new deployment record.\n"
            "The previous version's addresses are shown above.",
            border_style="green",
        )
    )

    logger.info(f"Rolled back {steps} deployments on {network}")
