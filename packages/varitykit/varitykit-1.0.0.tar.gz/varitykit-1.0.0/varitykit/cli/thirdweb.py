"""
Thirdweb SDK integration commands for VarityKit
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Optional

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


@click.group()
@click.pass_context
def thirdweb(ctx):
    """
    Thirdweb SDK integration for contract deployment and interaction

    Provides enhanced blockchain operations using the Thirdweb SDK,
    including contract deployment, interaction, and IPFS storage.

    \b
    Quick Start:
      varitykit thirdweb deploy <contract-path>
      varitykit thirdweb read <address> <method> [args]
      varitykit thirdweb write <address> <method> --params <params>
      varitykit thirdweb storage <file-path>

    \b
    Examples:
      # Deploy contract
      varitykit thirdweb deploy ./out/MyToken.sol/MyToken.json

      # Read from contract
      varitykit thirdweb read 0x123... balanceOf --params '["0xabc..."]'

      # Write to contract
      varitykit thirdweb write 0x123... transfer --params '["0xabc...", 1000000]'

      # Upload to IPFS
      varitykit thirdweb storage ./metadata.json

    \b
    Environment Variables Required:
      THIRDWEB_CLIENT_ID      - Get from https://thirdweb.com/dashboard
      DEPLOYER_PRIVATE_KEY    - Wallet private key for signing transactions

    Optional:
      THIRDWEB_SECRET_KEY     - For backend operations
    """
    pass


def get_env_var(name: str, required: bool = True) -> Optional[str]:
    """Get environment variable from .env.testnet or environment"""
    # Try environment first
    value = os.getenv(name)

    if not value:
        # Try to load from .env.testnet
        env_file = Path.cwd() / ".env.testnet"
        if not env_file.exists():
            # Try deployments/testnet/.env.testnet
            env_file = Path.cwd() / "deployments" / "testnet" / ".env.testnet"

        if env_file.exists():
            for line in env_file.read_text().split("\n"):
                if line.startswith(f"{name}="):
                    value = line.split("=", 1)[1].strip()
                    break

    if required and not value:
        raise ValueError(f"Missing required environment variable: {name}")

    return value


def get_scripts_dir() -> Path:
    """Get the scripts directory for Thirdweb helper scripts"""
    # Start from CLI directory
    cli_dir = Path(__file__).parent.parent.parent
    scripts_dir = cli_dir / "scripts" / "thirdweb"

    # Create if doesn't exist
    scripts_dir.mkdir(parents=True, exist_ok=True)

    return scripts_dir


@thirdweb.command()
@click.argument("contract_path", type=click.Path(exists=True))
@click.option(
    "--constructor-args", help="Constructor arguments as JSON array (e.g., '[\"arg1\", 123]')"
)
@click.option("--network", default="varity-testnet", help="Network to deploy to")
@click.option("--name", help="Contract name (auto-detected if not provided)")
@click.pass_context
def deploy(ctx, contract_path, constructor_args, network, name):
    """
    Deploy a smart contract using Thirdweb SDK

    Deploys a compiled contract JSON file (with ABI and bytecode) to the
    specified network using the Thirdweb deployment infrastructure.

    \b
    Arguments:
      CONTRACT_PATH  Path to compiled contract JSON file

    \b
    Options:
      --constructor-args  Constructor arguments as JSON array
      --network          Network to deploy to (default: varity-testnet)
      --name             Contract name (auto-detected from file if not provided)

    \b
    Examples:
      # Deploy without constructor arguments
      varitykit thirdweb deploy ./out/MyContract.sol/MyContract.json

      # Deploy with constructor arguments
      varitykit thirdweb deploy ./out/MyToken.sol/MyToken.json \\
        --constructor-args '["MyToken", "MTK", 1000000]'

      # Deploy to specific network
      varitykit thirdweb deploy ./out/NFT.sol/NFT.json --network varity-testnet
    """
    console = Console()
    logger = ctx.obj["logger"]

    try:
        # Read contract file
        contract_file = Path(contract_path)
        if not contract_file.exists():
            console.print(
                Panel.fit(
                    f"[bold red]Contract file not found[/bold red]\n\n" f"Path: {contract_path}",
                    border_style="red",
                )
            )
            ctx.exit(1)

        with open(contract_file, "r") as f:
            contract_data = json.load(f)

        # Extract ABI and bytecode
        abi = contract_data.get("abi")
        bytecode = contract_data.get("bytecode", {})

        if isinstance(bytecode, dict):
            bytecode = bytecode.get("object", "")

        if not abi or not bytecode:
            console.print(
                Panel.fit(
                    "[bold red]Invalid contract file[/bold red]\n\n"
                    "File must contain 'abi' and 'bytecode' fields",
                    border_style="red",
                )
            )
            ctx.exit(1)

        # Auto-detect contract name if not provided
        if not name:
            name = contract_file.stem

        # Get environment variables
        try:
            client_id = get_env_var("THIRDWEB_CLIENT_ID")
            private_key = get_env_var("DEPLOYER_PRIVATE_KEY")
            chain_id = get_env_var("CHAIN_ID", required=False) or "33529"
            rpc_url = (
                get_env_var("RPC_HTTP", required=False)
                or "https://rpc-varity-testnet-rroe52pwjp.t.conduit.xyz"
            )
        except ValueError as e:
            console.print(
                Panel.fit(
                    f"[bold red]Environment Configuration Error[/bold red]\n\n"
                    f"{str(e)}\n\n"
                    "Make sure .env.testnet is configured with:\n"
                    "  THIRDWEB_CLIENT_ID=your_client_id\n"
                    "  DEPLOYER_PRIVATE_KEY=0x...",
                    border_style="red",
                )
            )
            ctx.exit(1)

        console.print(
            Panel.fit(
                f"[bold cyan]Deploying Contract via Thirdweb[/bold cyan]\n"
                f"Contract: {name}\n"
                f"Network: {network} (Chain ID: {chain_id})\n"
                f"RPC: {rpc_url}",
                border_style="cyan",
            )
        )

        # Get script path
        scripts_dir = get_scripts_dir()
        deploy_script = scripts_dir / "deploy.js"

        if not deploy_script.exists():
            console.print(
                Panel.fit(
                    "[bold red]Thirdweb helper script not found[/bold red]\n\n"
                    f"Expected: {deploy_script}\n\n"
                    "Run setup to install Thirdweb scripts.",
                    border_style="red",
                )
            )
            ctx.exit(1)

        # Prepare command
        cmd = [
            "node",
            str(deploy_script),
            "--abi",
            json.dumps(abi),
            "--bytecode",
            bytecode,
            "--name",
            name,
            "--chain-id",
            chain_id,
            "--rpc",
            rpc_url,
            "--client-id",
            client_id,
            "--private-key",
            private_key,
        ]

        if constructor_args:
            cmd.extend(["--constructor-args", constructor_args])

        # Execute deployment
        console.print("[dim]Executing deployment...[/dim]\n")

        result = subprocess.run(cmd, capture_output=True, text=True, cwd=scripts_dir)

        if result.returncode == 0:
            # Parse output
            output = result.stdout.strip()

            console.print(
                Panel.fit(
                    f"[bold green]✓ Contract Deployed Successfully[/bold green]\n\n"
                    f"[bold]Address:[/bold]\n{output}\n\n"
                    f"[bold]Network:[/bold] {network}\n"
                    f"[bold]Chain ID:[/bold] {chain_id}",
                    border_style="green",
                )
            )

            logger.info(f"Deployed {name} to {output} on {network}")
        else:
            console.print(
                Panel.fit(
                    f"[bold red]✗ Deployment Failed[/bold red]\n\n" f"{result.stderr}",
                    border_style="red",
                )
            )
            logger.error(f"Deployment failed: {result.stderr}")
            ctx.exit(1)

    except Exception as e:
        console.print(
            Panel.fit(f"[bold red]Deployment Error[/bold red]\n\n" f"{str(e)}", border_style="red")
        )
        logger.error(f"Deployment error: {e}")
        ctx.exit(1)


@thirdweb.command()
@click.argument("contract_address")
@click.argument("method_name")
@click.option("--params", help="Method parameters as JSON array (e.g., '[\"0xabc...\", 1000]')")
@click.option("--network", default="varity-testnet", help="Network to read from")
@click.pass_context
def read(ctx, contract_address, method_name, params, network):
    """
    Read from a deployed contract using Thirdweb SDK

    Calls a view/pure function on a smart contract without sending a transaction.
    No gas cost, instant results.

    \b
    Arguments:
      CONTRACT_ADDRESS  Contract address (0x...)
      METHOD_NAME       Method name to call

    \b
    Options:
      --params   Method parameters as JSON array
      --network  Network to read from (default: varity-testnet)

    \b
    Examples:
      # Read balance
      varitykit thirdweb read 0x123... balanceOf --params '["0xabc..."]'

      # Read token name
      varitykit thirdweb read 0x123... name

      # Multi-parameter read
      varitykit thirdweb read 0x123... allowance \\
        --params '["0xowner...", "0xspender..."]'
    """
    console = Console()
    logger = ctx.obj["logger"]

    try:
        # Get environment variables
        try:
            client_id = get_env_var("THIRDWEB_CLIENT_ID")
            chain_id = get_env_var("CHAIN_ID", required=False) or "33529"
            rpc_url = (
                get_env_var("RPC_HTTP", required=False)
                or "https://rpc-varity-testnet-rroe52pwjp.t.conduit.xyz"
            )
        except ValueError as e:
            console.print(
                Panel.fit(
                    f"[bold red]Environment Configuration Error[/bold red]\n\n" f"{str(e)}",
                    border_style="red",
                )
            )
            ctx.exit(1)

        console.print(
            Panel.fit(
                f"[bold cyan]Reading from Contract[/bold cyan]\n"
                f"Contract: {contract_address}\n"
                f"Method: {method_name}\n"
                f"Network: {network}",
                border_style="cyan",
            )
        )

        # Get script path
        scripts_dir = get_scripts_dir()
        read_script = scripts_dir / "read.js"

        if not read_script.exists():
            console.print(
                Panel.fit(
                    "[bold red]Thirdweb helper script not found[/bold red]\n\n"
                    f"Expected: {read_script}",
                    border_style="red",
                )
            )
            ctx.exit(1)

        # Prepare command
        cmd = [
            "node",
            str(read_script),
            "--address",
            contract_address,
            "--method",
            method_name,
            "--chain-id",
            chain_id,
            "--rpc",
            rpc_url,
            "--client-id",
            client_id,
        ]

        if params:
            cmd.extend(["--params", params])

        # Execute read
        console.print("[dim]Calling contract method...[/dim]\n")

        result = subprocess.run(cmd, capture_output=True, text=True, cwd=scripts_dir)

        if result.returncode == 0:
            output = result.stdout.strip()

            console.print(
                Panel.fit(
                    f"[bold green]✓ Call Successful[/bold green]\n\n"
                    f"[bold]Result:[/bold]\n{output}",
                    border_style="green",
                )
            )

            logger.info(f"Read {method_name} from {contract_address}: {output}")
        else:
            console.print(
                Panel.fit(
                    f"[bold red]✗ Call Failed[/bold red]\n\n" f"{result.stderr}", border_style="red"
                )
            )
            logger.error(f"Read failed: {result.stderr}")
            ctx.exit(1)

    except Exception as e:
        console.print(
            Panel.fit(f"[bold red]Read Error[/bold red]\n\n" f"{str(e)}", border_style="red")
        )
        logger.error(f"Read error: {e}")
        ctx.exit(1)


@thirdweb.command()
@click.argument("contract_address")
@click.argument("method_name")
@click.option("--params", required=True, help="Method parameters as JSON array (required)")
@click.option("--network", default="varity-testnet", help="Network to send transaction to")
@click.option("--value", default="0", help="ETH/native token value to send (in wei)")
@click.pass_context
def write(ctx, contract_address, method_name, params, network, value):
    """
    Write to a deployed contract using Thirdweb SDK

    Sends a transaction to execute a state-changing function on a smart contract.
    Requires gas and may modify blockchain state.

    \b
    Arguments:
      CONTRACT_ADDRESS  Contract address (0x...)
      METHOD_NAME       Method name to call

    \b
    Options:
      --params   Method parameters as JSON array (required)
      --network  Network to send transaction to (default: varity-testnet)
      --value    Native token value to send in wei (default: 0)

    \b
    Examples:
      # Transfer tokens
      varitykit thirdweb write 0x123... transfer \\
        --params '["0xrecipient...", 1000000]'

      # Approve spending
      varitykit thirdweb write 0x123... approve \\
        --params '["0xspender...", 1000000000]'

      # Send with value
      varitykit thirdweb write 0x123... deposit \\
        --params '[]' --value 1000000
    """
    console = Console()
    logger = ctx.obj["logger"]

    try:
        # Get environment variables
        try:
            client_id = get_env_var("THIRDWEB_CLIENT_ID")
            private_key = get_env_var("DEPLOYER_PRIVATE_KEY")
            chain_id = get_env_var("CHAIN_ID", required=False) or "33529"
            rpc_url = (
                get_env_var("RPC_HTTP", required=False)
                or "https://rpc-varity-testnet-rroe52pwjp.t.conduit.xyz"
            )
        except ValueError as e:
            console.print(
                Panel.fit(
                    f"[bold red]Environment Configuration Error[/bold red]\n\n" f"{str(e)}",
                    border_style="red",
                )
            )
            ctx.exit(1)

        console.print(
            Panel.fit(
                f"[bold cyan]Sending Transaction to Contract[/bold cyan]\n"
                f"Contract: {contract_address}\n"
                f"Method: {method_name}\n"
                f"Network: {network}\n"
                f"Value: {value} wei",
                border_style="cyan",
            )
        )

        # Confirmation
        if not click.confirm("Send transaction?"):
            console.print("[dim]Transaction cancelled[/dim]")
            return

        # Get script path
        scripts_dir = get_scripts_dir()
        write_script = scripts_dir / "write.js"

        if not write_script.exists():
            console.print(
                Panel.fit(
                    "[bold red]Thirdweb helper script not found[/bold red]\n\n"
                    f"Expected: {write_script}",
                    border_style="red",
                )
            )
            ctx.exit(1)

        # Prepare command
        cmd = [
            "node",
            str(write_script),
            "--address",
            contract_address,
            "--method",
            method_name,
            "--params",
            params,
            "--chain-id",
            chain_id,
            "--rpc",
            rpc_url,
            "--client-id",
            client_id,
            "--private-key",
            private_key,
            "--value",
            value,
        ]

        # Execute write
        console.print("[dim]Sending transaction...[/dim]\n")

        result = subprocess.run(cmd, capture_output=True, text=True, cwd=scripts_dir)

        if result.returncode == 0:
            output = result.stdout.strip()

            console.print(
                Panel.fit(
                    f"[bold green]✓ Transaction Successful[/bold green]\n\n"
                    f"[bold]Transaction Hash:[/bold]\n{output}",
                    border_style="green",
                )
            )

            logger.info(f"Transaction sent: {output}")
        else:
            console.print(
                Panel.fit(
                    f"[bold red]✗ Transaction Failed[/bold red]\n\n" f"{result.stderr}",
                    border_style="red",
                )
            )
            logger.error(f"Write failed: {result.stderr}")
            ctx.exit(1)

    except Exception as e:
        console.print(
            Panel.fit(f"[bold red]Write Error[/bold red]\n\n" f"{str(e)}", border_style="red")
        )
        logger.error(f"Write error: {e}")
        ctx.exit(1)


@thirdweb.command()
@click.argument("file_path")
@click.option("--download", is_flag=True, help="Download from IPFS instead of upload")
@click.option("--output", "-o", help="Output path for downloaded file")
@click.pass_context
def storage(ctx, file_path, download, output):
    """
    Upload files to or download files from Thirdweb IPFS

    Provides decentralized storage integration using Thirdweb's IPFS gateway.

    \b
    Arguments:
      FILE_PATH  File path (for upload) or IPFS URI (for download)

    \b
    Options:
      --download  Download from IPFS instead of upload
      --output    Output path for downloaded file

    \b
    Examples:
      # Upload file
      varitykit thirdweb storage ./metadata.json

      # Upload directory
      varitykit thirdweb storage ./images/

      # Download from IPFS
      varitykit thirdweb storage ipfs://QmXxx... --download

      # Download to specific path
      varitykit thirdweb storage ipfs://QmXxx... --download --output ./metadata.json
    """
    console = Console()
    logger = ctx.obj["logger"]

    try:
        # Get environment variables
        try:
            client_id = get_env_var("THIRDWEB_CLIENT_ID")
        except ValueError as e:
            console.print(
                Panel.fit(
                    f"[bold red]Environment Configuration Error[/bold red]\n\n" f"{str(e)}",
                    border_style="red",
                )
            )
            ctx.exit(1)

        # Get script path
        scripts_dir = get_scripts_dir()

        if download:
            # Download mode
            console.print(
                Panel.fit(
                    f"[bold cyan]Downloading from IPFS[/bold cyan]\n" f"URI: {file_path}",
                    border_style="cyan",
                )
            )

            download_script = scripts_dir / "download.js"

            if not download_script.exists():
                console.print(
                    Panel.fit(
                        "[bold red]Thirdweb helper script not found[/bold red]\n\n"
                        f"Expected: {download_script}",
                        border_style="red",
                    )
                )
                ctx.exit(1)

            cmd = [
                "node",
                str(download_script),
                "--uri",
                file_path,
                "--client-id",
                client_id,
            ]

            if output:
                cmd.extend(["--output", output])

            console.print("[dim]Downloading from IPFS...[/dim]\n")

        else:
            # Upload mode
            upload_path = Path(file_path)
            if not upload_path.exists():
                console.print(
                    Panel.fit(
                        f"[bold red]File not found[/bold red]\n\n" f"Path: {file_path}",
                        border_style="red",
                    )
                )
                ctx.exit(1)

            console.print(
                Panel.fit(
                    f"[bold cyan]Uploading to IPFS[/bold cyan]\n" f"File: {file_path}",
                    border_style="cyan",
                )
            )

            upload_script = scripts_dir / "upload.js"

            if not upload_script.exists():
                console.print(
                    Panel.fit(
                        "[bold red]Thirdweb helper script not found[/bold red]\n\n"
                        f"Expected: {upload_script}",
                        border_style="red",
                    )
                )
                ctx.exit(1)

            cmd = [
                "node",
                str(upload_script),
                "--file",
                file_path,
                "--client-id",
                client_id,
            ]

            console.print("[dim]Uploading to IPFS...[/dim]\n")

        # Execute operation
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=scripts_dir)

        if result.returncode == 0:
            output_text = result.stdout.strip()

            if download:
                console.print(
                    Panel.fit(
                        f"[bold green]✓ Download Successful[/bold green]\n\n" f"{output_text}",
                        border_style="green",
                    )
                )
            else:
                console.print(
                    Panel.fit(
                        f"[bold green]✓ Upload Successful[/bold green]\n\n"
                        f"[bold]IPFS URI:[/bold]\n{output_text}",
                        border_style="green",
                    )
                )

            logger.info(f"Storage operation successful: {output_text}")
        else:
            console.print(
                Panel.fit(
                    f"[bold red]✗ Storage Operation Failed[/bold red]\n\n" f"{result.stderr}",
                    border_style="red",
                )
            )
            logger.error(f"Storage operation failed: {result.stderr}")
            ctx.exit(1)

    except Exception as e:
        console.print(
            Panel.fit(f"[bold red]Storage Error[/bold red]\n\n" f"{str(e)}", border_style="red")
        )
        logger.error(f"Storage error: {e}")
        ctx.exit(1)


@thirdweb.command()
@click.pass_context
def setup(ctx):
    """
    Setup Thirdweb integration scripts

    Installs required Node.js dependencies and creates helper scripts for
    Thirdweb SDK operations.
    """
    console = Console()
    logger = ctx.obj["logger"]

    try:
        scripts_dir = get_scripts_dir()

        console.print(
            Panel.fit(
                f"[bold cyan]Setting up Thirdweb Integration[/bold cyan]\n"
                f"Scripts directory: {scripts_dir}",
                border_style="cyan",
            )
        )

        # Create package.json
        package_json = {
            "name": "varitykit-thirdweb-scripts",
            "version": "1.0.0",
            "type": "module",
            "dependencies": {
                "@thirdweb-dev/sdk": "^4.0.0",
                "commander": "^11.0.0",
                "dotenv": "^16.0.0",
            },
        }

        package_file = scripts_dir / "package.json"
        with open(package_file, "w") as f:
            json.dump(package_json, f, indent=2)

        console.print("[dim]Installing Node.js dependencies...[/dim]\n")

        # Install dependencies
        result = subprocess.run(["npm", "install"], cwd=scripts_dir, capture_output=True, text=True)

        if result.returncode != 0:
            console.print(
                Panel.fit(
                    f"[bold red]✗ npm install failed[/bold red]\n\n" f"{result.stderr}",
                    border_style="red",
                )
            )
            ctx.exit(1)

        console.print(
            Panel.fit(
                "[bold green]✓ Thirdweb Setup Complete[/bold green]\n\n"
                "Helper scripts installed successfully.\n"
                "You can now use:\n"
                "  varitykit thirdweb deploy\n"
                "  varitykit thirdweb read\n"
                "  varitykit thirdweb write\n"
                "  varitykit thirdweb storage",
                border_style="green",
            )
        )

        logger.info("Thirdweb setup completed successfully")

    except Exception as e:
        console.print(
            Panel.fit(f"[bold red]Setup Error[/bold red]\n\n" f"{str(e)}", border_style="red")
        )
        logger.error(f"Setup error: {e}")
        ctx.exit(1)
