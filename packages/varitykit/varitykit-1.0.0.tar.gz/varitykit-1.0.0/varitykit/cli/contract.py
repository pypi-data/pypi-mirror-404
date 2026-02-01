"""
Contract interaction commands for VarityKit
"""

import json
from datetime import datetime
from pathlib import Path

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


@click.group()
@click.pass_context
def contract(ctx):
    """
    Interact with deployed smart contracts

    Commands for calling contract methods, sending transactions,
    and monitoring contract events.

    \b
    Quick Start:
      varitykit contract call <address> <method> [args]
      varitykit contract send <address> <method> [args]
      varitykit contract events <address> [--watch]

    \b
    Examples:
      # Read-only call
      varitykit contract call 0x123... balanceOf 0xabc...

      # Send transaction
      varitykit contract send 0x123... transfer 0xabc... 100

      # Watch events
      varitykit contract events 0x123... --watch

      # Query past events
      varitykit contract events 0x123... --from-block 1000
    """
    pass


def get_deployed_contracts(network: str = None) -> list:
    """Get list of deployed contracts from deployment history"""
    deployments_dir = Path.cwd() / ".varitykit" / "deployments"

    if not deployments_dir.exists():
        return []

    contracts = []

    # Determine which network files to check
    if network:
        network_files = [deployments_dir / f"{network}.json"]
    else:
        network_files = list(deployments_dir.glob("*.json"))

    for network_file in network_files:
        if not network_file.exists():
            continue

        try:
            with open(network_file, "r") as f:
                data = json.load(f)

            # Get latest deployment
            if data.get("deployments"):
                latest = data["deployments"][-1]
                for contract in latest.get("contracts", []):
                    contracts.append(
                        {
                            "name": contract["name"],
                            "address": contract["address"],
                            "network": data["network"],
                        }
                    )
        except Exception:
            continue

    return contracts


@contract.command()
@click.argument("address")
@click.argument("method")
@click.argument("args", nargs=-1)
@click.option(
    "--network",
    "-n",
    default="local",
    type=click.Choice(["local", "sepolia", "mainnet"]),
    help="Network to call on",
)
@click.option("--abi", help="Path to contract ABI JSON file")
@click.option("--value", type=str, help="ETH value to send (in wei)")
@click.option("--gas-limit", type=int, help="Gas limit override")
@click.pass_context
def call(ctx, address, method, args, network, abi, value, gas_limit):
    """
    Call a read-only contract method

    Executes a view/pure function on a smart contract without sending
    a transaction. No gas cost, instant results.

    \b
    Arguments:
      ADDRESS  Contract address (0x...)
      METHOD   Method name to call
      ARGS     Method arguments (space-separated)

    \b
    Examples:
      # Get balance
      varitykit contract call 0x123... balanceOf 0xabc...

      # Get token name
      varitykit contract call 0x123... name

      # Multi-argument call
      varitykit contract call 0x123... allowance 0xowner... 0xspender...

      # Use specific network
      varitykit contract call 0x123... totalSupply --network sepolia

      # Provide custom ABI
      varitykit contract call 0x123... customMethod arg1 --abi ./MyContract.json
    """
    console = Console()
    logger = ctx.obj["logger"]

    try:
        from web3 import Web3

        # Network configuration
        network_config = {
            "local": "http://localhost:8547",
            "sepolia": "https://sepolia-rollup.arbitrum.io/rpc",
            "mainnet": "https://arb1.arbitrum.io/rpc",
        }

        rpc_url = network_config[network]
        w3 = Web3(Web3.HTTPProvider(rpc_url))

        if not w3.is_connected():
            console.print(
                Panel.fit(
                    f"[bold red]Cannot connect to {network} network[/bold red]\n"
                    f"RPC: {rpc_url}\n\n"
                    "Make sure the network is accessible.",
                    border_style="red",
                )
            )
            ctx.exit(1)

        console.print(
            Panel.fit(
                f"[bold cyan]Calling Contract Method[/bold cyan]\n"
                f"Network: {network}\n"
                f"Contract: {address}\n"
                f"Method: {method}\n"
                f"Arguments: {', '.join(args) if args else 'none'}",
                border_style="cyan",
            )
        )

        # Load ABI
        if abi:
            abi_path = Path(abi)
            if not abi_path.exists():
                console.print(f"[red]ABI file not found: {abi}[/red]")
                ctx.exit(1)

            with open(abi_path, "r") as f:
                contract_abi = json.load(f)
        else:
            # Try to find ABI from deployments or artifacts
            deployed_contracts = get_deployed_contracts(network)
            contract_info = next(
                (c for c in deployed_contracts if c["address"].lower() == address.lower()), None
            )

            if contract_info:
                # Try to load from artifacts
                artifacts_dir = Path.cwd() / "artifacts" / "contracts"
                abi_file = (
                    artifacts_dir / f"{contract_info['name']}.sol" / f"{contract_info['name']}.json"
                )

                if abi_file.exists():
                    with open(abi_file, "r") as f:
                        artifact = json.load(f)
                        contract_abi = artifact.get("abi", [])
                else:
                    console.print(
                        Panel.fit(
                            "[bold yellow]No ABI found[/bold yellow]\n\n"
                            "Provide ABI with --abi flag or ensure contract is compiled:\n"
                            "  npx hardhat compile",
                            border_style="yellow",
                        )
                    )
                    ctx.exit(1)
            else:
                console.print(
                    Panel.fit(
                        "[bold yellow]Contract not found in deployments[/bold yellow]\n\n"
                        "Provide ABI with --abi flag:\n"
                        "  varitykit contract call <address> <method> --abi ./Contract.json",
                        border_style="yellow",
                    )
                )
                ctx.exit(1)

        # Create contract instance
        contract_instance = w3.eth.contract(
            address=Web3.to_checksum_address(address), abi=contract_abi
        )

        # Get function
        try:
            func = getattr(contract_instance.functions, method)
        except AttributeError:
            console.print(
                Panel.fit(
                    f"[bold red]Method '{method}' not found in contract[/bold red]\n\n"
                    "Available methods:\n"
                    + "\n".join(
                        f"  • {fn['name']}" for fn in contract_abi if fn.get("type") == "function"
                    )[:500],
                    border_style="red",
                )
            )
            ctx.exit(1)

        # Parse arguments (basic parsing, improve as needed)
        parsed_args = []
        for arg in args:
            # Try to parse as integer
            try:
                parsed_args.append(int(arg))
                continue
            except ValueError:
                pass

            # Try to parse as address
            if arg.startswith("0x") and len(arg) == 42:
                parsed_args.append(Web3.to_checksum_address(arg))
                continue

            # Keep as string
            parsed_args.append(arg)

        # Call function
        console.print("[dim]Calling contract method...[/dim]")

        result = func(*parsed_args).call()

        # Display result
        console.print("\n")
        console.print(
            Panel.fit(
                f"[bold green]✓ Call Successful[/bold green]\n\n"
                f"[bold]Result:[/bold]\n"
                f"{result}",
                border_style="green",
            )
        )

        logger.info(f"Called {method} on {address}: {result}")

    except ImportError:
        console.print(
            Panel.fit(
                "[bold red]web3.py not installed[/bold red]\n\n"
                "Install with:\n"
                "  pip install web3",
                border_style="red",
            )
        )
        ctx.exit(1)

    except Exception as e:
        console.print(
            Panel.fit(f"[bold red]Call failed[/bold red]\n\n" f"{str(e)}", border_style="red")
        )
        logger.error(f"Contract call failed: {e}")
        ctx.exit(1)


@contract.command()
@click.argument("address")
@click.argument("method")
@click.argument("args", nargs=-1)
@click.option(
    "--network",
    "-n",
    default="local",
    type=click.Choice(["local", "sepolia", "mainnet"]),
    help="Network to send transaction on",
)
@click.option("--abi", help="Path to contract ABI JSON file")
@click.option(
    "--value", type=str, default="0", help='ETH value to send (in wei or ether with "ether" suffix)'
)
@click.option("--gas-limit", type=int, help="Gas limit override")
@click.option(
    "--from", "from_address", help="Sender address (uses wallet from .env if not specified)"
)
@click.option(
    "--private-key", help="Private key (uses WALLET_PRIVATE_KEY from .env if not specified)"
)
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def send(
    ctx, address, method, args, network, abi, value, gas_limit, from_address, private_key, confirm
):
    """
    Send a transaction to a contract method

    Executes a state-changing function on a smart contract.
    Requires gas and may modify blockchain state.

    \b
    Arguments:
      ADDRESS  Contract address (0x...)
      METHOD   Method name to call
      ARGS     Method arguments (space-separated)

    \b
    Examples:
      # Transfer tokens
      varitykit contract send 0x123... transfer 0xrecipient... 100

      # Approve spending
      varitykit contract send 0x123... approve 0xspender... 1000

      # Send ETH with transaction
      varitykit contract send 0x123... deposit --value 1ether

      # Custom gas limit
      varitykit contract send 0x123... complexMethod arg1 --gas-limit 500000

      # Use specific wallet
      varitykit contract send 0x123... transfer 0xabc... 50 --from 0xmywallet...
    """
    console = Console()
    logger = ctx.obj["logger"]

    try:
        import os

        from web3 import Web3

        # Network configuration
        network_config = {
            "local": "http://localhost:8547",
            "sepolia": "https://sepolia-rollup.arbitrum.io/rpc",
            "mainnet": "https://arb1.arbitrum.io/rpc",
        }

        rpc_url = network_config[network]
        w3 = Web3(Web3.HTTPProvider(rpc_url))

        if not w3.is_connected():
            console.print(
                Panel.fit(
                    f"[bold red]Cannot connect to {network} network[/bold red]\n" f"RPC: {rpc_url}",
                    border_style="red",
                )
            )
            ctx.exit(1)

        # Get private key from .env if not provided
        if not private_key:
            env_file = Path(".env")
            if env_file.exists():
                for line in env_file.read_text().split("\n"):
                    if line.startswith("WALLET_PRIVATE_KEY="):
                        private_key = line.split("=")[1].strip()
                        break

        if not private_key:
            console.print(
                Panel.fit(
                    "[bold red]No private key provided[/bold red]\n\n"
                    "Either:\n"
                    "  1. Add WALLET_PRIVATE_KEY to .env file, or\n"
                    "  2. Use --private-key flag",
                    border_style="red",
                )
            )
            ctx.exit(1)

        # Get account from private key
        account = w3.eth.account.from_key(private_key)
        sender = from_address or account.address

        # Parse value
        if value.endswith("ether"):
            value_wei = w3.to_wei(float(value[:-5]), "ether")
        else:
            value_wei = int(value)

        console.print(
            Panel.fit(
                f"[bold cyan]Sending Contract Transaction[/bold cyan]\n"
                f"Network: {network}\n"
                f"Contract: {address}\n"
                f"Method: {method}\n"
                f"From: {sender}\n"
                f"Value: {w3.from_wei(value_wei, 'ether')} ETH\n"
                f"Arguments: {', '.join(args) if args else 'none'}",
                border_style="cyan",
            )
        )

        # Load ABI (same logic as call command)
        if abi:
            abi_path = Path(abi)
            if not abi_path.exists():
                console.print(f"[red]ABI file not found: {abi}[/red]")
                ctx.exit(1)

            with open(abi_path, "r") as f:
                contract_abi = json.load(f)
        else:
            deployed_contracts = get_deployed_contracts(network)
            contract_info = next(
                (c for c in deployed_contracts if c["address"].lower() == address.lower()), None
            )

            if contract_info:
                artifacts_dir = Path.cwd() / "artifacts" / "contracts"
                abi_file = (
                    artifacts_dir / f"{contract_info['name']}.sol" / f"{contract_info['name']}.json"
                )

                if abi_file.exists():
                    with open(abi_file, "r") as f:
                        artifact = json.load(f)
                        contract_abi = artifact.get("abi", [])
                else:
                    console.print("[yellow]No ABI found. Provide with --abi flag[/yellow]")
                    ctx.exit(1)
            else:
                console.print("[yellow]Contract not found. Provide ABI with --abi flag[/yellow]")
                ctx.exit(1)

        # Create contract instance
        contract_instance = w3.eth.contract(
            address=Web3.to_checksum_address(address), abi=contract_abi
        )

        # Get function
        try:
            func = getattr(contract_instance.functions, method)
        except AttributeError:
            console.print(f"[red]Method '{method}' not found in contract[/red]")
            ctx.exit(1)

        # Parse arguments
        parsed_args = []
        for arg in args:
            try:
                parsed_args.append(int(arg))
                continue
            except ValueError:
                pass

            if arg.startswith("0x") and len(arg) == 42:
                parsed_args.append(Web3.to_checksum_address(arg))
                continue

            parsed_args.append(arg)

        # Build transaction
        tx_params = {
            "from": Web3.to_checksum_address(sender),
            "value": value_wei,
            "nonce": w3.eth.get_transaction_count(Web3.to_checksum_address(sender)),
        }

        if gas_limit:
            tx_params["gas"] = gas_limit

        # Estimate gas if not provided
        if not gas_limit:
            try:
                estimated_gas = func(*parsed_args).estimate_gas(tx_params)
                tx_params["gas"] = int(estimated_gas * 1.2)  # 20% buffer
            except Exception as e:
                console.print(f"[yellow]Warning: Gas estimation failed: {e}[/yellow]")
                tx_params["gas"] = 300000  # Default gas limit

        # Estimate cost
        gas_price = w3.eth.gas_price
        estimated_cost = w3.from_wei(tx_params["gas"] * gas_price + value_wei, "ether")

        # Confirmation
        if not confirm:
            console.print(f"\n[bold]Transaction Details:[/bold]")
            console.print(f"  Gas Limit: {tx_params['gas']:,}")
            console.print(f"  Gas Price: {w3.from_wei(gas_price, 'gwei'):.2f} gwei")
            console.print(f"  Estimated Cost: ~{estimated_cost:.6f} ETH\n")

            if not click.confirm("Send transaction?"):
                console.print("[dim]Transaction cancelled[/dim]")
                return

        # Build and sign transaction
        console.print("[dim]Building transaction...[/dim]")
        transaction = func(*parsed_args).build_transaction(tx_params)

        console.print("[dim]Signing transaction...[/dim]")
        signed_tx = w3.eth.account.sign_transaction(transaction, private_key)

        console.print("[dim]Sending transaction...[/dim]")
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

        console.print(f"[green]✓ Transaction sent: {tx_hash.hex()}[/green]")
        console.print("[dim]Waiting for confirmation...[/dim]")

        # Wait for receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)

        # Display result
        console.print("\n")

        if receipt["status"] == 1:
            console.print(
                Panel.fit(
                    f"[bold green]✓ Transaction Successful[/bold green]\n\n"
                    f"[bold]Transaction Hash:[/bold]\n{tx_hash.hex()}\n\n"
                    f"[bold]Block Number:[/bold] {receipt['blockNumber']}\n"
                    f"[bold]Gas Used:[/bold] {receipt['gasUsed']:,}\n"
                    f"[bold]Actual Cost:[/bold] {w3.from_wei(receipt['gasUsed'] * gas_price, 'ether'):.6f} ETH",
                    border_style="green",
                )
            )

            logger.info(f"Transaction successful: {tx_hash.hex()}")
        else:
            console.print(
                Panel.fit(
                    f"[bold red]✗ Transaction Failed[/bold red]\n\n"
                    f"Transaction Hash: {tx_hash.hex()}\n"
                    f"Block Number: {receipt['blockNumber']}",
                    border_style="red",
                )
            )

            logger.error(f"Transaction failed: {tx_hash.hex()}")

    except ImportError:
        console.print(
            Panel.fit(
                "[bold red]web3.py not installed[/bold red]\n\n"
                "Install with:\n"
                "  pip install web3",
                border_style="red",
            )
        )
        ctx.exit(1)

    except Exception as e:
        console.print(
            Panel.fit(
                f"[bold red]Transaction failed[/bold red]\n\n" f"{str(e)}", border_style="red"
            )
        )
        logger.error(f"Transaction failed: {e}")
        ctx.exit(1)


@contract.command()
@click.argument("address")
@click.option(
    "--network",
    "-n",
    default="local",
    type=click.Choice(["local", "sepolia", "mainnet"]),
    help="Network to query events on",
)
@click.option("--abi", help="Path to contract ABI JSON file")
@click.option("--event", "-e", help="Specific event name to watch")
@click.option("--from-block", type=int, help="Start block number")
@click.option("--to-block", type=int, help="End block number")
@click.option("--watch", "-w", is_flag=True, help="Watch for new events in real-time")
@click.option("--limit", "-l", type=int, default=10, help="Maximum number of events to display")
@click.pass_context
def events(ctx, address, network, abi, event, from_block, to_block, watch, limit):
    """
    Query or watch contract events

    Retrieves past events or watches for new events emitted by a contract.

    \b
    Examples:
      # Get recent events
      varitykit contract events 0x123...

      # Watch for new events in real-time
      varitykit contract events 0x123... --watch

      # Query specific event type
      varitykit contract events 0x123... --event Transfer

      # Query historical events
      varitykit contract events 0x123... --from-block 1000 --to-block 2000

      # Limit number of results
      varitykit contract events 0x123... --limit 50
    """
    console = Console()
    logger = ctx.obj["logger"]

    try:
        import time

        from web3 import Web3

        # Network configuration
        network_config = {
            "local": "http://localhost:8547",
            "sepolia": "https://sepolia-rollup.arbitrum.io/rpc",
            "mainnet": "https://arb1.arbitrum.io/rpc",
        }

        rpc_url = network_config[network]
        w3 = Web3(Web3.HTTPProvider(rpc_url))

        if not w3.is_connected():
            console.print(
                Panel.fit(
                    f"[bold red]Cannot connect to {network} network[/bold red]", border_style="red"
                )
            )
            ctx.exit(1)

        # Load ABI
        if abi:
            abi_path = Path(abi)
            if not abi_path.exists():
                console.print(f"[red]ABI file not found: {abi}[/red]")
                ctx.exit(1)

            with open(abi_path, "r") as f:
                contract_abi = json.load(f)
        else:
            deployed_contracts = get_deployed_contracts(network)
            contract_info = next(
                (c for c in deployed_contracts if c["address"].lower() == address.lower()), None
            )

            if contract_info:
                artifacts_dir = Path.cwd() / "artifacts" / "contracts"
                abi_file = (
                    artifacts_dir / f"{contract_info['name']}.sol" / f"{contract_info['name']}.json"
                )

                if abi_file.exists():
                    with open(abi_file, "r") as f:
                        artifact = json.load(f)
                        contract_abi = artifact.get("abi", [])
                else:
                    console.print("[yellow]No ABI found. Provide with --abi flag[/yellow]")
                    ctx.exit(1)
            else:
                console.print("[yellow]Contract not found. Provide ABI with --abi flag[/yellow]")
                ctx.exit(1)

        # Create contract instance
        contract_instance = w3.eth.contract(
            address=Web3.to_checksum_address(address), abi=contract_abi
        )

        # Get event filter
        if event:
            try:
                event_obj = getattr(contract_instance.events, event)
            except AttributeError:
                console.print(f"[red]Event '{event}' not found in contract[/red]")
                # List available events
                event_names = [e["name"] for e in contract_abi if e.get("type") == "event"]
                if event_names:
                    console.print(f"\nAvailable events: {', '.join(event_names)}")
                ctx.exit(1)
        else:
            event_obj = None

        if watch:
            # Watch mode
            console.print(
                Panel.fit(
                    f"[bold cyan]Watching Contract Events[/bold cyan]\n"
                    f"Network: {network}\n"
                    f"Contract: {address}\n"
                    f"Event: {event or 'all'}",
                    border_style="cyan",
                )
            )

            console.print("\n[dim]Watching for new events... (Press Ctrl+C to stop)[/dim]\n")

            # Get current block
            current_block = w3.eth.block_number

            try:
                while True:
                    # Get new events
                    if event_obj:
                        logs = event_obj.create_filter(fromBlock=current_block).get_all_entries()
                    else:
                        # Get all events
                        logs = []
                        for e in contract_abi:
                            if e.get("type") == "event":
                                try:
                                    event_filter = getattr(contract_instance.events, e["name"])
                                    logs.extend(
                                        event_filter.create_filter(
                                            fromBlock=current_block
                                        ).get_all_entries()
                                    )
                                except Exception:
                                    pass

                    # Display new events
                    for log in logs:
                        console.print(f"[green]●[/green] [bold]{log.event}[/bold]")
                        console.print(f"  Block: {log.blockNumber}")
                        console.print(f"  Transaction: {log.transactionHash.hex()}")
                        console.print(f"  Args: {dict(log.args)}")
                        console.print()

                    if logs:
                        current_block = w3.eth.block_number

                    time.sleep(2)  # Poll every 2 seconds

            except KeyboardInterrupt:
                console.print("\n[dim]Stopped watching events[/dim]")

        else:
            # Query mode
            console.print(
                Panel.fit(
                    f"[bold cyan]Querying Contract Events[/bold cyan]\n"
                    f"Network: {network}\n"
                    f"Contract: {address}\n"
                    f"Event: {event or 'all'}",
                    border_style="cyan",
                )
            )

            # Determine block range
            if not from_block:
                from_block = max(0, w3.eth.block_number - 1000)  # Last 1000 blocks

            if not to_block:
                to_block = "latest"

            console.print(f"[dim]Querying blocks {from_block} to {to_block}...[/dim]\n")

            # Get events
            if event_obj:
                logs = event_obj.create_filter(
                    fromBlock=from_block, toBlock=to_block
                ).get_all_entries()
            else:
                logs = []
                for e in contract_abi:
                    if e.get("type") == "event":
                        try:
                            event_filter = getattr(contract_instance.events, e["name"])
                            logs.extend(
                                event_filter.create_filter(
                                    fromBlock=from_block, toBlock=to_block
                                ).get_all_entries()
                            )
                        except Exception:
                            pass

            if not logs:
                console.print("[yellow]No events found in specified range[/yellow]")
                return

            # Sort by block number (newest first)
            logs.sort(key=lambda x: x.blockNumber, reverse=True)

            # Limit results
            logs = logs[:limit]

            # Display in table
            table = Table(
                title=f"Contract Events ({len(logs)} events)",
                box=box.ROUNDED,
                show_header=True,
                header_style="bold magenta",
            )
            table.add_column("Block", style="cyan", width=10)
            table.add_column("Event", style="yellow", width=20)
            table.add_column("Transaction", style="white", width=20)
            table.add_column("Args", style="dim")

            for log in logs:
                table.add_row(
                    str(log.blockNumber),
                    log.event,
                    log.transactionHash.hex()[:18] + "...",
                    str(dict(log.args))[:50] + ("..." if len(str(dict(log.args))) > 50 else ""),
                )

            console.print(table)
            console.print(f"\n[dim]Showing {len(logs)} of {len(logs)} events[/dim]\n")

        logger.info(f"Queried events for {address}")

    except ImportError:
        console.print(
            Panel.fit(
                "[bold red]web3.py not installed[/bold red]\n\n"
                "Install with:\n"
                "  pip install web3",
                border_style="red",
            )
        )
        ctx.exit(1)

    except Exception as e:
        console.print(
            Panel.fit(
                f"[bold red]Failed to query events[/bold red]\n\n" f"{str(e)}", border_style="red"
            )
        )
        logger.error(f"Event query failed: {e}")
        ctx.exit(1)


@contract.command()
@click.option("--network", "-n", help="Filter by network")
@click.pass_context
def list(ctx, network):
    """
    List deployed contracts

    Shows all contracts from deployment history with addresses and networks.
    """
    console = Console()
    logger = ctx.obj["logger"]

    contracts = get_deployed_contracts(network)

    if not contracts:
        console.print("[yellow]No deployed contracts found[/yellow]")
        console.print("\nDeploy contracts with:")
        console.print("  [cyan]varitykit deploy run[/cyan]\n")
        return

    table = Table(
        title="Deployed Contracts", box=box.ROUNDED, show_header=True, header_style="bold magenta"
    )
    table.add_column("Name", style="cyan", width=25)
    table.add_column("Address", style="yellow", width=45)
    table.add_column("Network", style="green", width=10)

    for contract in contracts:
        table.add_row(contract["name"], contract["address"], contract["network"])

    console.print("\n")
    console.print(table)
    console.print(f"\n[dim]Total: {len(contracts)} contract(s)[/dim]\n")

    logger.info(f"Listed {len(contracts)} deployed contracts")
