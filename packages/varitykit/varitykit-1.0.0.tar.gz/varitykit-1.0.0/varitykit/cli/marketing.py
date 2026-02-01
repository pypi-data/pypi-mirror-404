"""
Marketing website deployment commands for Akash Network
"""

import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import click
import requests
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()


@click.group()
def marketing():
    """
    Deploy and manage marketing website on Akash Network.

    The Varity marketing website is deployed to Akash Network for
    decentralized hosting with 90%+ cost savings vs traditional cloud.

    \b
    Features:
    • Automated Docker build and push
    • Akash deployment creation and management
    • SSL/TLS with automatic Let's Encrypt
    • Custom domain configuration (varity.ai)
    • Live deployment status monitoring
    • Log streaming from providers

    \b
    Quick Start:
      varitykit marketing deploy --network mainnet
      varitykit marketing status
      varitykit marketing logs

    \b
    Cost Comparison:
      Traditional Cloud: $10-50/month
      Akash Network: <$1/month (90%+ savings)
    """
    pass


def get_deployment_info_file() -> Path:
    """Get path to deployment info file"""
    config_dir = Path.home() / ".varitykit" / "marketing"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "deployment.json"


def save_deployment_info(info: dict):
    """Save deployment information"""
    info_file = get_deployment_info_file()
    with open(info_file, "w") as f:
        json.dump(info, f, indent=2)


def load_deployment_info() -> Dict[Any, Any]:
    """Load deployment information"""
    info_file = get_deployment_info_file()
    if not info_file.exists():
        return {}

    with open(info_file, "r", encoding="utf-8") as f:
        return json.load(f)


def get_akash_config(network: str) -> dict:
    """Get Akash network configuration"""
    return {
        "mainnet": {
            "rpc": "https://rpc.akash.forbole.com:443",
            "chain_id": "akashnet-2",
            "name": "Akash Mainnet",
        },
        "testnet": {
            "rpc": "https://rpc.sandbox-01.aksh.pw:443",
            "chain_id": "sandbox-01",
            "name": "Akash Testnet",
        },
    }[network]


@marketing.command()
@click.option(
    "--network", default="mainnet", type=click.Choice(["mainnet", "testnet"]), help="Akash network"
)
@click.option("--build", is_flag=True, help="Build Docker image first")
@click.option("--registry", default="ghcr.io/varity/marketing-website", help="Docker registry")
@click.option("--skip-push", is_flag=True, help="Skip Docker push (testing only)")
def deploy(network, build, registry, skip_push):
    """
    Deploy marketing website to Akash Network.

    This command will:
    1. Build the Next.js static website (if --build)
    2. Create Docker image
    3. Push to container registry
    4. Deploy to Akash Network
    5. Wait for lease from provider
    6. Send manifest to provider
    7. Get service URL

    \b
    Prerequisites:
      • Docker installed and running
      • Akash CLI installed (akash)
      • Akash wallet with AKT tokens
      • Docker registry credentials (for push)

    \b
    Examples:
      # Deploy to mainnet (production)
      varitykit marketing deploy --network mainnet --build

      # Deploy to testnet (testing)
      varitykit marketing deploy --network testnet --build

      # Deploy without building (use existing image)
      varitykit marketing deploy --network mainnet
    """
    console.print(
        Panel.fit(
            "[bold cyan]Varity Marketing Website Deployment[/bold cyan]\n"
            f"Network: {network}\n"
            f"Registry: {registry}",
            border_style="cyan",
        )
    )

    akash_config = get_akash_config(network)
    marketing_dir = Path(__file__).parent.parent.parent.parent / "marketing-website"

    # Verify marketing website directory exists
    if not marketing_dir.exists():
        console.print(f"[red]✗ Marketing website directory not found: {marketing_dir}[/red]")
        return

    # Step 1: Build website (if requested)
    if build:
        console.print("\n[bold]Step 1: Building website...[/bold]")

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:
            task = progress.add_task("[cyan]Running npm build...", total=None)

            result = subprocess.run(
                ["npm", "run", "build"], cwd=str(marketing_dir), capture_output=True, text=True
            )

            if result.returncode != 0:
                console.print(f"[red]✗ Build failed: {result.stderr}[/red]")
                return

            progress.update(task, completed=True)

        console.print("[green]✓[/green] Website built successfully")

    # Step 2: Build Docker image
    console.print("\n[bold]Step 2: Building Docker image...[/bold]")

    tag = f"{registry}:latest"
    build_tag = f"{registry}:{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
    ) as progress:
        task = progress.add_task(f"[cyan]Building {tag}...", total=None)

        result = subprocess.run(
            [
                "docker",
                "build",
                "-f",
                "deploy/Dockerfile",
                "-t",
                tag,
                "-t",
                build_tag,
                "--build-arg",
                f"BUILD_DATE={datetime.now().isoformat()}",
                "--build-arg",
                "VCS_REF=main",
                "--build-arg",
                "VERSION=1.0.0",
                ".",
            ],
            cwd=str(marketing_dir),
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            console.print(f"[red]✗ Docker build failed: {result.stderr}[/red]")
            return

        progress.update(task, completed=True)

    console.print(f"[green]✓[/green] Docker image built: {tag}")
    console.print(f"[green]✓[/green] Version tag: {build_tag}")

    # Step 3: Push to registry
    if not skip_push:
        console.print("\n[bold]Step 3: Pushing to registry...[/bold]")

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:
            task = progress.add_task(f"[cyan]Pushing {tag}...", total=None)

            result = subprocess.run(["docker", "push", tag], capture_output=True, text=True)

            if result.returncode != 0:
                console.print(f"[red]✗ Docker push failed: {result.stderr}[/red]")
                return

            progress.update(task, completed=True)

        console.print(f"[green]✓[/green] Image pushed to {registry}")
    else:
        console.print("\n[yellow]⚠️  Skipping Docker push (--skip-push)[/yellow]")

    # Step 4: Deploy to Akash
    console.print("\n[bold]Step 4: Deploying to Akash Network...[/bold]")

    sdl_path = marketing_dir / "deploy" / "akash.sdl"

    # Check if akash CLI is available
    result = subprocess.run(["which", "akash"], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        console.print("[red]✗ Akash CLI not found. Install from: https://docs.akash.network/[/red]")
        return

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
    ) as progress:
        task = progress.add_task("[cyan]Creating deployment...", total=None)

        result = subprocess.run(
            [
                "akash",
                "tx",
                "deployment",
                "create",
                str(sdl_path),
                "--from",
                "varity-deployer",
                "--node",
                akash_config["rpc"],
                "--chain-id",
                akash_config["chain_id"],
                "--fees",
                "5000uakt",
                "--gas",
                "auto",
                "--gas-adjustment",
                "1.5",
                "-y",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            console.print(f"[red]✗ Akash deployment failed: {result.stderr}[/red]")
            return

        progress.update(task, completed=True)

    # Parse deployment ID from output
    deployment_id = None
    for line in result.stdout.split("\n"):
        if "dseq" in line.lower() or "deployment" in line.lower():
            # Extract deployment sequence number
            parts = line.split(":")
            if len(parts) > 1:
                deployment_id = parts[1].strip().strip('"')
                break

    if not deployment_id:
        # Fallback: try to parse JSON output
        try:
            output_json = json.loads(result.stdout)
            deployment_id = output_json.get("dseq") or output_json.get("deployment_id")
        except Exception:
            pass

    if not deployment_id:
        console.print("[yellow]⚠️  Could not parse deployment ID from output[/yellow]")
        console.print(result.stdout)
        deployment_id = "unknown"

    console.print(f"[green]✓[/green] Deployment created: {deployment_id}")

    # Step 5: Wait for lease
    console.print("\n[bold]Step 5: Waiting for provider lease...[/bold]")
    console.print(
        "[dim]Providers will bid on your deployment. This may take 30-60 seconds...[/dim]\n"
    )

    lease_info = None
    max_wait = 120  # 2 minutes
    start_time = time.time()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Waiting for lease...", total=max_wait)

        while time.time() - start_time < max_wait:
            # Query for active leases
            result = subprocess.run(
                [
                    "akash",
                    "query",
                    "market",
                    "lease",
                    "list",
                    "--owner",
                    "varity-deployer",  # This should be the actual address
                    "--node",
                    akash_config["rpc"],
                    "--output",
                    "json",
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                try:
                    leases = json.loads(result.stdout)
                    # Find lease for this deployment
                    for lease in leases.get("leases", []):
                        if lease.get("deployment_id") == deployment_id:
                            lease_info = lease
                            break

                    if lease_info:
                        break
                except Exception:
                    pass

            elapsed = time.time() - start_time
            progress.update(task, completed=min(elapsed, max_wait))
            time.sleep(5)

    if not lease_info:
        console.print("[red]✗ No lease received after 2 minutes[/red]")
        console.print(
            "[yellow]Check deployment status with: akash query market lease list[/yellow]"
        )
        return

    provider = lease_info.get("provider", "unknown")
    console.print(f"[green]✓[/green] Lease created with provider: {provider}")

    # Step 6: Send manifest
    console.print("\n[bold]Step 6: Sending manifest to provider...[/bold]")

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
    ) as progress:
        task = progress.add_task("[cyan]Uploading manifest...", total=None)

        result = subprocess.run(
            [
                "akash",
                "provider",
                "send-manifest",
                str(sdl_path),
                "--dseq",
                deployment_id,
                "--provider",
                provider,
                "--from",
                "varity-deployer",
                "--node",
                akash_config["rpc"],
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            console.print(f"[yellow]⚠️  Manifest send warning: {result.stderr}[/yellow]")
        else:
            progress.update(task, completed=True)
            console.print("[green]✓[/green] Manifest sent")

    # Step 7: Get service URL
    console.print("\n[bold]Step 7: Getting service URL...[/bold]")

    time.sleep(10)  # Wait for service to start

    result = subprocess.run(
        [
            "akash",
            "provider",
            "lease-status",
            "--dseq",
            deployment_id,
            "--provider",
            provider,
            "--from",
            "varity-deployer",
            "--node",
            akash_config["rpc"],
            "--output",
            "json",
        ],
        capture_output=True,
        text=True,
    )

    service_url = None
    if result.returncode == 0:
        try:
            status = json.loads(result.stdout)
            services = status.get("services", {})
            web_service = services.get("web", {})
            uris = web_service.get("uris", [])
            if uris:
                service_url = uris[0]
        except Exception:
            pass

    if not service_url:
        service_url = f"http://{provider}:8080"  # Fallback

    # Save deployment info
    deployment_info = {
        "deployment_id": deployment_id,
        "provider": provider,
        "service_url": service_url,
        "network": network,
        "registry": registry,
        "deployed_at": datetime.now().isoformat(),
        "akash_config": akash_config,
    }
    save_deployment_info(deployment_info)

    # Display summary
    console.print("\n")
    console.print(
        Panel.fit(
            "[bold green]✅ Deployment Complete![/bold green]\n\n"
            f"[bold]Service URL:[/bold] {service_url}\n"
            f"[bold]Deployment ID:[/bold] {deployment_id}\n"
            f"[bold]Provider:[/bold] {provider}\n"
            f"[bold]Network:[/bold] {akash_config['name']}\n\n"
            f"[dim]View status:[/dim] varitykit marketing status\n"
            f"[dim]View logs:[/dim] varitykit marketing logs",
            border_style="green",
        )
    )


@marketing.command()
def status():
    """
    Check marketing website deployment status.

    Displays information about the current deployment including
    service URL, provider, and accessibility check.

    \b
    Example:
      varitykit marketing status
    """
    info = load_deployment_info()

    if not info:
        console.print(
            Panel.fit(
                "[bold yellow]No deployment found[/bold yellow]\n\n"
                "Deploy the marketing website with:\n"
                "  varitykit marketing deploy --network mainnet --build",
                border_style="yellow",
            )
        )
        return

    console.print(
        Panel.fit(
            "[bold]Varity Marketing Website[/bold]\n\n"
            f"[cyan]Service URL:[/cyan] {info['service_url']}\n"
            f"[cyan]Deployment ID:[/cyan] {info['deployment_id']}\n"
            f"[cyan]Provider:[/cyan] {info['provider']}\n"
            f"[cyan]Network:[/cyan] {info['network']}\n"
            f"[cyan]Deployed:[/cyan] {info['deployed_at']}\n"
            f"[cyan]Registry:[/cyan] {info['registry']}",
            border_style="cyan",
        )
    )

    # Check if site is accessible
    console.print("\n[bold]Checking accessibility...[/bold]")

    try:
        response = requests.get(info["service_url"], timeout=10)
        if response.status_code == 200:
            console.print(f"[green]✓[/green] Website is accessible (HTTP {response.status_code})")

            # Check response time
            response_time = response.elapsed.total_seconds()
            console.print(f"[green]✓[/green] Response time: {response_time:.2f}s")

        else:
            console.print(f"[yellow]⚠[/yellow] Website returned HTTP {response.status_code}")

    except requests.Timeout:
        console.print(f"[red]✗[/red] Request timeout after 10s")

    except requests.RequestException as e:
        console.print(f"[red]✗[/red] Website not accessible: {e}")


@marketing.command()
@click.option("--follow", "-f", is_flag=True, help="Follow log output (like tail -f)")
@click.option("--lines", "-n", default=100, help="Number of lines to show")
def logs(follow, lines):
    """
    View marketing website logs from Akash provider.

    Fetches and displays logs from the deployed service on Akash Network.

    \b
    Examples:
      # View last 100 lines
      varitykit marketing logs

      # View last 500 lines
      varitykit marketing logs --lines 500

      # Follow logs in real-time
      varitykit marketing logs --follow
    """
    info = load_deployment_info()

    if not info:
        console.print("[yellow]No deployment found[/yellow]")
        return

    console.print(f"[cyan]Fetching logs from {info['provider']}...[/cyan]\n")

    cmd = [
        "akash",
        "provider",
        "service-logs",
        "--dseq",
        info["deployment_id"],
        "--provider",
        info["provider"],
        "--from",
        "varity-deployer",
        "--service",
        "web",
    ]

    if follow:
        cmd.append("--follow")

    if lines:
        cmd.extend(["--tail", str(lines)])

    # Stream logs
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    try:
        if process.stdout:
            for line in process.stdout:
                print(line, end="")
    except KeyboardInterrupt:
        process.terminate()
        console.print("\n[dim]Log streaming stopped[/dim]")


@marketing.command()
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
def close(confirm):
    """
    Close marketing website deployment.

    ⚠️  This will terminate the Akash deployment and stop serving
    the marketing website.

    \b
    Example:
      varitykit marketing close --confirm
    """
    info = load_deployment_info()

    if not info:
        console.print("[yellow]No deployment found[/yellow]")
        return

    if not confirm:
        console.print(
            Panel.fit(
                f"[bold yellow]⚠️  Close Deployment[/bold yellow]\n\n"
                f"Deployment ID: {info['deployment_id']}\n"
                f"Provider: {info['provider']}\n"
                f"Service URL: {info['service_url']}\n\n"
                "[bold]This will stop serving the website.[/bold]",
                border_style="yellow",
            )
        )

        if not click.confirm("Proceed with closing deployment?"):
            console.print("[dim]Cancelled[/dim]")
            return

    console.print("[cyan]Closing deployment...[/cyan]")

    result = subprocess.run(
        [
            "akash",
            "tx",
            "deployment",
            "close",
            "--dseq",
            info["deployment_id"],
            "--from",
            "varity-deployer",
            "--node",
            info["akash_config"]["rpc"],
            "--chain-id",
            info["akash_config"]["chain_id"],
            "--fees",
            "5000uakt",
            "-y",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        console.print(f"[red]✗ Failed to close deployment: {result.stderr}[/red]")
        return

    console.print("[green]✓[/green] Deployment closed")

    # Remove deployment info
    info_file = get_deployment_info_file()
    if info_file.exists():
        info_file.unlink()
