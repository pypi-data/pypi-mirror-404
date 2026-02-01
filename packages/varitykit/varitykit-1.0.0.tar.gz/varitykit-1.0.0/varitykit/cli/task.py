"""
Task commands - utilities for common operations
"""

import json
from pathlib import Path

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


@click.group()
@click.pass_context
def task(ctx):
    """
    Task utilities for account, storage, and dashboard operations

    \b
    Available task groups:
      account   - Create, restore, and manage accounts
      wallet    - (deprecated, use 'account' instead)
      storage   - Upload, download, and manage storage
      dashboard - Deploy, monitor, and manage dashboards

    \b
    Examples:
      varitykit task account create
      varitykit task storage upload ./data
      varitykit task dashboard deploy
    """
    pass


# ============================================================
# ACCOUNT COMMANDS
# ============================================================


@task.group(name="account")
@click.pass_context
def account(ctx):
    """Account management commands"""
    pass


# Keep backward compatibility with deprecated 'wallet' command
@task.group(name="wallet", deprecated=True, hidden=True)
@click.pass_context
def wallet(ctx):
    """[DEPRECATED] Use 'account' instead - Varity account management"""
    from rich.console import Console
    console = Console()
    console.print("[yellow]⚠  Warning: 'varitykit task wallet' is deprecated.[/yellow]")
    console.print("[yellow]   Please use 'varitykit task account' instead.[/yellow]\n")


@account.command()
@click.option("--name", prompt="Account name", help="Name for the account")
@click.option("--save", is_flag=True, help="Save account to .env file")
@click.pass_context
def create(ctx, name, save):
    """
    Create a new Varity account

    Generates a new account with secure backup credentials.
    Optionally saves to .env file for persistent use.
    """
    console = Console()
    logger = ctx.obj["logger"]

    try:
        # Import web3 for account generation
        import secrets

        from eth_account import Account

        console.print(Panel.fit("[bold cyan]Creating New Varity Account[/bold cyan]", border_style="cyan"))

        # Generate backup credentials (private key)
        private_key = "0x" + secrets.token_hex(32)
        account_obj = Account.from_key(private_key)

        # Display account info
        table = Table(box=box.ROUNDED, show_header=False)
        table.add_column("Property", style="cyan", width=18)
        table.add_column("Value", style="white")

        table.add_row("Name", str(name))
        table.add_row("Address", str(account_obj.address))
        table.add_row("Backup Key", str(f"[dim]{private_key[:20]}...[/dim]"))

        console.print("\n")
        console.print(table)

        # Security warning
        console.print("\n")
        console.print(
            Panel.fit(
                "[bold red]⚠ SECURITY WARNING[/bold red]\n"
                "Never share your backup credentials with anyone!\n"
                "Store them securely and keep backups.\n\n"
                "[bold yellow]Backup Credentials:[/bold yellow]\n"
                f"[dim]{private_key}[/dim]",
                border_style="red",
            )
        )

        if save:
            env_file = Path(".env")

            # Read existing .env or create new
            env_content = ""
            if env_file.exists():
                env_content = env_file.read_text()

            # Add account info
            new_content = env_content + f"\n# Varity Account: {name}\n"
            new_content += f"WALLET_ADDRESS={account_obj.address}\n"
            new_content += f"WALLET_PRIVATE_KEY={private_key}\n"

            env_file.write_text(new_content)

            console.print(f"\n[green]✓ Account saved to .env file[/green]")
            logger.info(f"Created and saved account: {name}")

        else:
            console.print("\n[dim]Use --save flag to save account to .env file[/dim]")
            logger.info(f"Created account: {name}")

    except ImportError:
        console.print(
            Panel.fit(
                "[bold red]Error: eth-account not installed[/bold red]\n"
                "Install with: pip install eth-account",
                border_style="red",
            )
        )
        ctx.exit(1)

    except Exception as e:
        console.print(
            Panel.fit(f"[bold red]Error creating account[/bold red]\n{str(e)}", border_style="red")
        )
        logger.error(f"Failed to create account: {e}")
        ctx.exit(1)


# Deprecated wallet create for backward compatibility
@wallet.command()
@click.option("--name", prompt="Account name", help="Name for the account")
@click.option("--save", is_flag=True, help="Save account to .env file")
@click.pass_context
def create(ctx, name, save):
    """[DEPRECATED] Use 'varitykit task account create' instead"""
    # Call the new account create command
    ctx.invoke(account.commands['create'], name=name, save=save)


@account.command()
@click.option("--backup-key", prompt="Backup credentials", hide_input=True, help="Backup credentials to restore")
@click.option("--name", prompt="Account name", help="Name for the account")
@click.option("--save", is_flag=True, help="Save account to .env file")
@click.pass_context
def restore(ctx, backup_key, name, save):
    """
    Restore an existing account from backup

    Restores an account using your backup credentials.
    Optionally saves to .env file.
    """
    console = Console()
    logger = ctx.obj["logger"]

    try:
        from eth_account import Account

        # Ensure backup key has 0x prefix
        if not backup_key.startswith("0x"):
            backup_key = "0x" + backup_key

        # Validate and restore
        account_obj = Account.from_key(backup_key)

        console.print(Panel.fit("[bold cyan]Account Restored[/bold cyan]", border_style="cyan"))

        table = Table(box=box.ROUNDED, show_header=False)
        table.add_column("Property", style="cyan", width=15)
        table.add_column("Value", style="white")

        table.add_row("Name", str(name))
        table.add_row("Address", str(account_obj.address))

        console.print("\n")
        console.print(table)

        if save:
            env_file = Path(".env")
            env_content = ""
            if env_file.exists():
                env_content = env_file.read_text()

            new_content = env_content + f"\n# Varity Account: {name}\n"
            new_content += f"WALLET_ADDRESS={account_obj.address}\n"
            new_content += f"WALLET_PRIVATE_KEY={backup_key}\n"

            env_file.write_text(new_content)

            console.print(f"\n[green]✓ Account saved to .env file[/green]")
            logger.info(f"Restored and saved account: {name}")

        logger.info(f"Restored account: {name} ({account_obj.address})")

    except ImportError:
        console.print(
            Panel.fit(
                "[bold red]Error: eth-account not installed[/bold red]\n"
                "Install with: pip install eth-account",
                border_style="red",
            )
        )
        ctx.exit(1)

    except Exception as e:
        console.print(
            Panel.fit(f"[bold red]Error restoring account[/bold red]\n{str(e)}", border_style="red")
        )
        logger.error(f"Failed to restore account: {e}")
        ctx.exit(1)


# Deprecated import_wallet for backward compatibility
@wallet.command(name="import-wallet")
@click.option("--private-key", prompt="Backup credentials", hide_input=True, help="Backup credentials to restore")
@click.option("--name", prompt="Account name", help="Name for the account")
@click.option("--save", is_flag=True, help="Save account to .env file")
@click.pass_context
def import_wallet(ctx, private_key, name, save):
    """[DEPRECATED] Use 'varitykit task account restore' instead"""
    # Call the new account restore command
    ctx.invoke(account.commands['restore'], backup_key=private_key, name=name, save=save)


@account.command(name="list")
@click.pass_context
def list_accounts(ctx):
    """List all Varity accounts in .env file"""
    console = Console()
    logger = ctx.obj["logger"]

    env_file = Path(".env")

    if not env_file.exists():
        console.print(
            Panel.fit(
                "[bold yellow]No .env file found[/bold yellow]\n"
                "Create an account with: varitykit task account create",
                border_style="yellow",
            )
        )
        ctx.exit(0)

    # Parse .env file for account addresses
    accounts = []
    current_account: dict = {}

    for line in env_file.read_text().split("\n"):
        if line.startswith("# Varity Account:") or line.startswith("# Wallet:"):
            if current_account:
                accounts.append(current_account)
            name = line.replace("# Varity Account:", "").replace("# Wallet:", "").strip()
            current_account: dict = {"name": name}

        elif line.startswith("WALLET_ADDRESS="):
            current_account["address"] = line.split("=")[1].strip()

    if current_account:
        accounts.append(current_account)

    if not accounts:
        console.print(
            Panel.fit(
                "[bold yellow]No accounts found in .env file[/bold yellow]", border_style="yellow"
            )
        )
        ctx.exit(0)

    # Display accounts
    table = Table(title="Varity Accounts", box=box.ROUNDED, show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan", width=20)
    table.add_column("Address", style="white")

    for account_info in accounts:
        table.add_row(account_info.get("name", str("Unknown")), account_info.get("address", "N/A"))

    console.print("\n")
    console.print(table)
    console.print(f"\n[dim]Total: {len(accounts)} account(s)[/dim]\n")

    logger.info(f"Listed {len(accounts)} accounts")


# Deprecated list_wallets for backward compatibility
@wallet.command(name="list-wallets")
@click.pass_context
def list_wallets(ctx):
    """[DEPRECATED] Use 'varitykit task account list' instead"""
    ctx.invoke(account.commands['list'])


@account.command()
@click.option("--address", help="Account address to check")
@click.option(
    "--network",
    default="local",
    type=click.Choice(["local", "development", "production", "sepolia", "arbitrum"]),
    help="Network to check balance on",
)
@click.pass_context
def balance(ctx, address, network):
    """Check account balance on network"""
    console = Console()
    logger = ctx.obj["logger"]

    try:
        from web3 import Web3

        # Map network names (with backward compatibility)
        network_mapping = {
            "local": "local",
            "development": "sepolia",  # development = testnet
            "production": "arbitrum",  # production = mainnet
            "sepolia": "sepolia",      # legacy support
            "arbitrum": "arbitrum",    # legacy support
        }

        actual_network = network_mapping.get(network, network)

        # Get RPC URL based on network
        rpc_urls = {
            "local": "http://localhost:8547",
            "sepolia": "https://sepolia-rollup.arbitrum.io/rpc",
            "arbitrum": "https://arb1.arbitrum.io/rpc",
        }

        rpc_url = rpc_urls[actual_network]
        w3 = Web3(Web3.HTTPProvider(rpc_url))

        if not address:
            # Try to get from .env
            env_file = Path(".env")
            if env_file.exists():
                for line in env_file.read_text().split("\n"):
                    if line.startswith("WALLET_ADDRESS="):
                        address = line.split("=")[1].strip()
                        break

        if not address:
            console.print(
                Panel.fit(
                    "[bold red]No account address specified[/bold red]\n"
                    "Use --address flag or create an account first",
                    border_style="red",
                )
            )
            ctx.exit(1)

        # Convert to checksum address for type safety
        address = Web3.to_checksum_address(address)

        # Get balance
        balance_wei = w3.eth.get_balance(address)
        balance_eth = w3.from_wei(balance_wei, "ether")

        # Display balance
        table = Table(box=box.ROUNDED, show_header=False)
        table.add_column("Property", style="cyan", width=15)
        table.add_column("Value", style="white")

        display_network = network.upper() if network in ["local", "development", "production"] else actual_network.upper()
        table.add_row("Network", str(display_network))
        table.add_row("Address", str(address))
        table.add_row("Balance", str(f"{balance_eth:.6f} credits"))
        table.add_row("Wei", str(str(balance_wei)))

        console.print("\n")
        console.print(table)
        console.print()

        logger.info(f"Checked balance for {address} on {network}")

    except ImportError:
        console.print(
            Panel.fit(
                "[bold red]Error: web3 not installed[/bold red]\n" "Install with: pip install web3",
                border_style="red",
            )
        )
        ctx.exit(1)

    except Exception as e:
        console.print(
            Panel.fit(f"[bold red]Error checking balance[/bold red]\n{str(e)}", border_style="red")
        )
        logger.error(f"Failed to check balance: {e}")
        ctx.exit(1)


# Deprecated balance for backward compatibility
@wallet.command(name="balance")
@click.option("--address", help="Account address to check")
@click.option(
    "--network",
    default="local",
    type=click.Choice(["local", "development", "production", "sepolia", "arbitrum"]),
    help="Network to check balance on",
)
@click.pass_context
def balance_deprecated(ctx, address, network):
    """[DEPRECATED] Use 'varitykit task account balance' instead"""
    ctx.invoke(account.commands['balance'], address=address, network=network)


# ============================================================
# STORAGE COMMANDS
# ============================================================


@task.group()
@click.pass_context
def storage(ctx):
    """Storage management commands (IPFS/Filecoin)"""
    pass


@storage.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--pin", is_flag=True, help="Pin file to IPFS")
@click.pass_context
def upload(ctx, file_path, pin):
    """
    Upload file to IPFS/Filecoin

    Uploads a file to the local IPFS node or Pinata gateway.
    """
    console = Console()
    logger = ctx.obj["logger"]

    try:
        import requests

        file_path = Path(file_path)

        console.print(
            Panel.fit(
                f"[bold cyan]Uploading to IPFS[/bold cyan]\n" f"File: {file_path.name}",
                border_style="cyan",
            )
        )

        # Upload to local IPFS
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = requests.post("http://localhost:5001/api/v0/add", files=files, timeout=30)

        if response.status_code == 200:
            data = response.json()
            ipfs_hash = data["Hash"]

            table = Table(box=box.ROUNDED, show_header=False)
            table.add_column("Property", style="cyan", width=15)
            table.add_column("Value", style="white")

            table.add_row("File", str(file_path.name))
            table.add_row("Size", str(f"{file_path.stat().st_size:,} bytes"))
            table.add_row("IPFS Hash", str(ipfs_hash))
            table.add_row("Gateway URL", str(f"http://localhost:8080/ipfs/{ipfs_hash}"))

            console.print("\n")
            console.print(table)
            console.print()

            console.print(f"[green]✓ File uploaded successfully![/green]")

            if pin:
                console.print(f"[dim]Pinning file...[/dim]")
                # Pin the file
                pin_response = requests.post(
                    f"http://localhost:5001/api/v0/pin/add?arg={ipfs_hash}", timeout=10
                )
                if pin_response.status_code == 200:
                    console.print(f"[green]✓ File pinned[/green]\n")

            logger.info(f"Uploaded file: {file_path.name} -> {ipfs_hash}")

        else:
            console.print(
                Panel.fit(
                    f"[bold red]Upload failed[/bold red]\n" f"Status: {response.status_code}",
                    border_style="red",
                )
            )
            ctx.exit(1)

    except requests.exceptions.ConnectionError:
        console.print(
            Panel.fit(
                "[bold red]Cannot connect to IPFS node[/bold red]\n"
                "Start LocalDePin with: varitykit localdepin start",
                border_style="red",
            )
        )
        ctx.exit(1)

    except Exception as e:
        console.print(
            Panel.fit(f"[bold red]Error uploading file[/bold red]\n{str(e)}", border_style="red")
        )
        logger.error(f"Failed to upload file: {e}")
        ctx.exit(1)


@storage.command()
@click.argument("ipfs_hash")
@click.option("--output", "-o", help="Output file path")
@click.pass_context
def download(ctx, ipfs_hash, output):
    """Download file from IPFS by hash"""
    console = Console()
    logger = ctx.obj["logger"]

    try:
        import requests

        console.print(f"[dim]Downloading {ipfs_hash}...[/dim]")

        response = requests.get(f"http://localhost:8080/ipfs/{ipfs_hash}", timeout=30)

        if response.status_code == 200:
            # Determine output path
            if not output:
                output = f"{ipfs_hash[:8]}.dat"

            output_path = Path(output)
            output_path.write_bytes(response.content)

            console.print(f"[green]✓ Downloaded to {output_path}[/green]")
            console.print(f"[dim]Size: {len(response.content):,} bytes[/dim]\n")

            logger.info(f"Downloaded {ipfs_hash} to {output_path}")

        else:
            console.print(
                Panel.fit(
                    f"[bold red]Download failed[/bold red]\n" f"Status: {response.status_code}",
                    border_style="red",
                )
            )
            ctx.exit(1)

    except Exception as e:
        console.print(
            Panel.fit(f"[bold red]Error downloading file[/bold red]\n{str(e)}", border_style="red")
        )
        logger.error(f"Failed to download: {e}")
        ctx.exit(1)


@storage.command()
@click.pass_context
def list_files(ctx):
    """List pinned files on IPFS"""
    console = Console()
    logger = ctx.obj["logger"]

    try:
        import requests

        response = requests.post("http://localhost:5001/api/v0/pin/ls", timeout=10)

        if response.status_code == 200:
            data = response.json()
            pins = data.get("Keys", {})

            if not pins:
                console.print("[dim]No pinned files found[/dim]\n")
                ctx.exit(0)

            table = Table(
                title="Pinned Files", box=box.ROUNDED, show_header=True, header_style="bold magenta"
            )
            table.add_column("IPFS Hash", style="cyan", width=50)
            table.add_column("Type", style="white", width=15)

            for ipfs_hash, info in pins.items():
                table.add_row(ipfs_hash, str(info.get("Type", "unknown")))

            console.print("\n")
            console.print(table)
            console.print(f"\n[dim]Total: {len(pins)} file(s)[/dim]\n")

            logger.info(f"Listed {len(pins)} pinned files")

        else:
            console.print(
                Panel.fit("[bold red]Failed to list files[/bold red]", border_style="red")
            )
            ctx.exit(1)

    except requests.exceptions.ConnectionError:
        console.print(
            Panel.fit(
                "[bold red]Cannot connect to IPFS node[/bold red]\n"
                "Start LocalDePin with: varitykit localdepin start",
                border_style="red",
            )
        )
        ctx.exit(1)

    except Exception as e:
        console.print(
            Panel.fit(f"[bold red]Error listing files[/bold red]\n{str(e)}", border_style="red")
        )
        logger.error(f"Failed to list files: {e}")
        ctx.exit(1)


# ============================================================
# DASHBOARD COMMANDS
# ============================================================


@task.group()
@click.pass_context
def dashboard(ctx):
    """Dashboard deployment and management commands"""
    pass


@dashboard.command()
@click.option("--name", prompt="Dashboard name", help="Name for the dashboard")
@click.option(
    "--network",
    default="local",
    type=click.Choice(["local", "development", "production", "testnet", "mainnet"]),
    help="Deployment network",
)
@click.pass_context
def deploy(ctx, name, network):
    """
    Deploy dashboard to Varity

    Builds and deploys the dashboard to the specified network.
    """
    console = Console()
    logger = ctx.obj["logger"]

    # Map network names (with backward compatibility)
    network_mapping = {
        "local": "local",
        "development": "testnet",
        "production": "mainnet",
        "testnet": "testnet",  # legacy support
        "mainnet": "mainnet",  # legacy support
    }
    actual_network = network_mapping.get(network, network)
    display_network = network.upper() if network in ["local", "development", "production"] else actual_network.upper()

    console.print(
        Panel.fit(
            f"[bold cyan]Deploying Dashboard[/bold cyan]\n" f"Name: {name}\n" f"Network: {display_network}",
            border_style="cyan",
        )
    )

    # This would integrate with the actual deployment pipeline
    console.print("\n[bold]Deployment Steps:[/bold]")
    console.print("  [dim]1. Building frontend...[/dim]")
    console.print("  [dim]2. Uploading to decentralized storage...[/dim]")
    console.print("  [dim]3. Deploying application...[/dim]")
    console.print("  [dim]4. Registering on Varity...[/dim]\n")

    console.print(
        Panel.fit(
            "[bold yellow]Deployment feature coming soon![/bold yellow]\n"
            "This will integrate with the full deployment pipeline.",
            border_style="yellow",
        )
    )

    logger.info(f"Deploy requested: {name} to {network}")


@dashboard.command()
@click.pass_context
def list_dashboards(ctx):
    """List deployed dashboards"""
    console = Console()

    console.print(
        Panel.fit(
            "[bold yellow]Dashboard listing coming soon![/bold yellow]\n"
            "This will show all your deployed dashboards.",
            border_style="yellow",
        )
    )


@dashboard.command()
@click.argument("dashboard_id")
@click.pass_context
def logs(ctx, dashboard_id):
    """View dashboard logs"""
    console = Console()

    console.print(
        Panel.fit(
            "[bold yellow]Log viewing coming soon![/bold yellow]\n" f"Dashboard ID: {dashboard_id}",
            border_style="yellow",
        )
    )
