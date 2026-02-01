"""
Data migration commands for VarityKit

Migrate data from AWS S3 or Google Cloud Storage to Varity infrastructure
with blockchain verification and integrity checks.
"""

import shutil
import subprocess
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

console = Console()


def check_varity_migrate_installed():
    """Check if varity-migrate CLI is installed"""
    if shutil.which("varity-migrate") is None:
        console.print(
            Panel(
                "[red]Error: varity-migrate is not installed[/red]\n\n"
                "The migration commands require the @varity/migrate package.\n\n"
                "Install it globally:\n"
                "  [cyan]npm install -g @varity/migrate[/cyan]\n\n"
                "Or install locally in your project:\n"
                "  [cyan]npm install @varity/migrate[/cyan]\n"
                "  [cyan]npx varity-migrate --help[/cyan]",
                title="Missing Dependency",
                border_style="red",
            )
        )
        return False
    return True


def run_varity_migrate(args):
    """Execute varity-migrate CLI command"""
    try:
        result = subprocess.run(
            ["varity-migrate"] + args,
            check=False,  # Don't raise exception on non-zero exit
            text=True,
        )
        sys.exit(result.returncode)
    except FileNotFoundError:
        console.print("[red]Error: varity-migrate command not found[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error executing varity-migrate: {e}[/red]")
        sys.exit(1)


@click.group()
@click.pass_context
def migrate(ctx):
    """
    Migrate data from cloud storage to Varity

    Seamlessly migrate data from AWS S3 or Google Cloud Storage to Varity's
    decentralized infrastructure with comprehensive blockchain verification.

    \b
    Features:
    • Multi-cloud support (AWS S3, Google Cloud Storage)
    • Real-time progress tracking with speed indicators
    • Automatic resume from checkpoints
    • SHA-256 hash verification for data integrity
    • Blockchain chain verification (7 supported chains)
    • Contract compatibility checks
    • Gas cost estimation and savings calculator
    • Concurrent transfers for optimal performance
    • Dry run mode for testing

    \b
    Quick Start:
      varitykit migrate s3 --bucket my-bucket
      varitykit migrate gcs --bucket my-bucket
      varitykit migrate status --job-id abc123
      varitykit migrate verify-chain --source-chain 1

    \b
    Supported Chains:
      • Ethereum (1)
      • Arbitrum One (42161)
      • Arbitrum Sepolia (421614)
      • Polygon (137)
      • Base (8453)
      • Optimism (10)
      • Varity L3 (33529) - Default destination

    Note: This command wraps the @varity/migrate package.
          Make sure it's installed: npm install -g @varity/migrate
    """
    # Check if varity-migrate is installed
    if not check_varity_migrate_installed():
        sys.exit(1)


@migrate.command("s3")
@click.option("--bucket", required=True, help="Source S3 bucket name")
@click.option("--prefix", help='Object prefix filter (e.g., "folder/")')
@click.option("--region", default="us-east-1", help="AWS region (default: us-east-1)")
@click.option(
    "--target-layer", default="customer-data", help="Varity storage layer (default: customer-data)"
)
@click.option("--concurrency", default="10", help="Concurrent transfers (default: 10)")
@click.option("--dry-run", is_flag=True, help="Simulate migration without transferring data")
@click.option("--verify", is_flag=True, help="Verify all transfers with SHA-256 hash")
@click.pass_context
def s3_migrate(ctx, bucket, prefix, region, target_layer, concurrency, dry_run, verify):
    """
    Migrate from AWS S3 to Varity

    Migrate data from an AWS S3 bucket to Varity's decentralized infrastructure.
    Supports filtering by prefix, automatic resume, and integrity verification.

    \b
    Examples:
      # Migrate entire bucket
      varitykit migrate s3 --bucket my-s3-bucket

      # Migrate specific folder with verification
      varitykit migrate s3 --bucket my-bucket --prefix "data/" --verify

      # Dry run to estimate migration
      varitykit migrate s3 --bucket my-bucket --dry-run

      # High-speed migration with 20 concurrent transfers
      varitykit migrate s3 --bucket my-bucket --concurrency 20

    \b
    Prerequisites:
      • AWS credentials configured (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
      • Varity API credentials (VARITY_API_KEY)
      • Sufficient storage quota on Varity
    """
    args = ["s3", "--bucket", bucket]

    if prefix:
        args.extend(["--prefix", prefix])
    if region:
        args.extend(["--region", region])
    if target_layer:
        args.extend(["--target-layer", target_layer])
    if concurrency:
        args.extend(["--concurrency", concurrency])
    if dry_run:
        args.append("--dry-run")
    if verify:
        args.append("--verify")

    run_varity_migrate(args)


@migrate.command("gcs")
@click.option("--bucket", required=True, help="Source GCS bucket name")
@click.option("--prefix", help='Object prefix filter (e.g., "folder/")')
@click.option("--project", help="GCP project ID")
@click.option(
    "--target-layer", default="customer-data", help="Varity storage layer (default: customer-data)"
)
@click.option("--concurrency", default="10", help="Concurrent transfers (default: 10)")
@click.option("--dry-run", is_flag=True, help="Simulate migration without transferring data")
@click.option("--verify", is_flag=True, help="Verify all transfers with SHA-256 hash")
@click.pass_context
def gcs_migrate(ctx, bucket, prefix, project, target_layer, concurrency, dry_run, verify):
    """
    Migrate from Google Cloud Storage to Varity

    Migrate data from a Google Cloud Storage bucket to Varity's decentralized
    infrastructure with automatic resume and integrity verification.

    \b
    Examples:
      # Migrate entire bucket
      varitykit migrate gcs --bucket my-gcs-bucket --project my-project

      # Migrate specific folder with verification
      varitykit migrate gcs --bucket my-bucket --prefix "data/" --verify

      # Dry run to estimate migration
      varitykit migrate gcs --bucket my-bucket --dry-run

      # High-speed migration
      varitykit migrate gcs --bucket my-bucket --concurrency 20

    \b
    Prerequisites:
      • GCP credentials configured (GOOGLE_APPLICATION_CREDENTIALS)
      • Varity API credentials (VARITY_API_KEY)
      • Sufficient storage quota on Varity
    """
    args = ["gcs", "--bucket", bucket]

    if prefix:
        args.extend(["--prefix", prefix])
    if project:
        args.extend(["--project", project])
    if target_layer:
        args.extend(["--target-layer", target_layer])
    if concurrency:
        args.extend(["--concurrency", concurrency])
    if dry_run:
        args.append("--dry-run")
    if verify:
        args.append("--verify")

    run_varity_migrate(args)


@migrate.command("status")
@click.option("--job-id", required=True, help="Migration job ID")
@click.pass_context
def status(ctx, job_id):
    """
    Check migration job status

    Query the status of an ongoing or completed migration job.
    Shows progress, transfer statistics, and any errors encountered.

    \b
    Examples:
      varitykit migrate status --job-id mig_abc123xyz

    \b
    Output includes:
      • Job state (running, completed, failed)
      • Objects transferred / total
      • Bytes transferred / total
      • Transfer speed and ETA
      • Error summary if any
    """
    args = ["status", "--job-id", job_id]
    run_varity_migrate(args)


@migrate.command("verify")
@click.option("--job-id", required=True, help="Migration job ID")
@click.pass_context
def verify(ctx, job_id):
    """
    Verify migration integrity

    Verify the integrity of a completed migration by comparing SHA-256 hashes
    of all transferred objects. Ensures data was migrated without corruption.

    \b
    Examples:
      varitykit migrate verify --job-id mig_abc123xyz

    \b
    Verification checks:
      • SHA-256 hash comparison for each object
      • Object count verification
      • Total size verification
      • Missing object detection
    """
    args = ["verify", "--job-id", job_id]
    run_varity_migrate(args)


@migrate.command("verify-chain")
@click.option(
    "--source-chain", required=True, help="Source blockchain chain ID (e.g., 1 for Ethereum)"
)
@click.option("--dest-chain", help="Destination chain ID (default: 33529 - Varity L3)")
@click.option("--source-rpc", help="Source chain RPC URL override")
@click.option("--dest-rpc", help="Destination chain RPC URL override")
@click.option("--wallet", help="Wallet address to check balance")
@click.pass_context
def verify_chain(ctx, source_chain, dest_chain, source_rpc, dest_rpc, wallet):
    """
    Verify blockchain chain connectivity

    Verify RPC connectivity and chain configuration for both source and
    destination chains. Essential for ensuring successful cross-chain migrations.

    \b
    Examples:
      # Verify Ethereum to Varity L3 migration
      varitykit migrate verify-chain --source-chain 1

      # Verify with wallet balance check
      varitykit migrate verify-chain --source-chain 1 --wallet 0xYourAddress

      # Use custom RPC endpoints
      varitykit migrate verify-chain --source-chain 1 \\
        --source-rpc https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY

    \b
    Verification checks:
      • RPC endpoint connectivity
      • Chain ID confirmation
      • Latest block number
      • Gas price estimation
      • Wallet balance (if provided)

    \b
    Supported Source Chains:
      • Ethereum (1)
      • Arbitrum One (42161)
      • Arbitrum Sepolia (421614)
      • Polygon (137)
      • Base (8453)
      • Optimism (10)
    """
    args = ["verify-chain", "--source-chain", source_chain]

    if dest_chain:
        args.extend(["--dest-chain", dest_chain])
    if source_rpc:
        args.extend(["--source-rpc", source_rpc])
    if dest_rpc:
        args.extend(["--dest-rpc", dest_rpc])
    if wallet:
        args.extend(["--wallet", wallet])

    run_varity_migrate(args)


@migrate.command("preflight")
@click.option("--source-chain", required=True, help="Source blockchain chain ID")
@click.option("--dest-chain", help="Destination chain ID (default: 33529 - Varity L3)")
@click.option("--wallet", help="Wallet address for balance checks")
@click.option("--contracts", help="Comma-separated contract addresses to verify")
@click.option("--source-rpc", help="Source chain RPC URL override")
@click.option("--dest-rpc", help="Destination chain RPC URL override")
@click.option("--min-gas", help="Minimum gas balance required")
@click.pass_context
def preflight(ctx, source_chain, dest_chain, wallet, contracts, source_rpc, dest_rpc, min_gas):
    """
    Run pre-flight checks before migration

    Comprehensive validation before starting a migration. Checks chain
    connectivity, contract compatibility, wallet balances, and gas requirements.

    \b
    Examples:
      # Basic pre-flight check
      varitykit migrate preflight --source-chain 1 --wallet 0xYourAddress

      # Check specific contracts
      varitykit migrate preflight --source-chain 1 \\
        --contracts 0xContract1,0xContract2

      # Ensure minimum gas balance
      varitykit migrate preflight --source-chain 1 \\
        --wallet 0xYourAddress --min-gas 0.1

    \b
    Pre-flight checks:
      • Chain connectivity (source and destination)
      • Contract deployability on destination chain
      • Wallet balance sufficiency
      • Gas price estimation
      • USDC 6-decimal compatibility (Varity L3)
      • Storage quota availability
    """
    args = ["preflight", "--source-chain", source_chain]

    if dest_chain:
        args.extend(["--dest-chain", dest_chain])
    if wallet:
        args.extend(["--wallet", wallet])
    if contracts:
        args.extend(["--contracts", contracts])
    if source_rpc:
        args.extend(["--source-rpc", source_rpc])
    if dest_rpc:
        args.extend(["--dest-rpc", dest_rpc])
    if min_gas:
        args.extend(["--min-gas", min_gas])

    run_varity_migrate(args)


@migrate.command("chains")
@click.pass_context
def chains(ctx):
    """
    List supported blockchain chains

    Display all blockchain chains supported for migration, including
    chain IDs, names, RPC endpoints, and native tokens.

    \b
    Example:
      varitykit migrate chains

    \b
    Supported Chains:
      • Ethereum Mainnet (1)
      • Arbitrum One (42161)
      • Arbitrum Sepolia (421614)
      • Polygon (137)
      • Base (8453)
      • Optimism (10)
      • Varity L3 Testnet (33529)
    """
    args = ["chains"]
    run_varity_migrate(args)


@migrate.command("report")
@click.option("--source-chain", required=True, help="Source blockchain chain ID")
@click.option("--dest-chain", help="Destination chain ID (default: 33529 - Varity L3)")
@click.option("--contracts", help="Comma-separated contract addresses to analyze")
@click.option("--wallet", help="Wallet address for balance analysis")
@click.option("--source-rpc", help="Source chain RPC URL override")
@click.option("--dest-rpc", help="Destination chain RPC URL override")
@click.option("--output", help="Output file path for report")
@click.option(
    "--format",
    type=click.Choice(["console", "json", "markdown"]),
    default="console",
    help="Report format (default: console)",
)
@click.pass_context
def report(ctx, source_chain, dest_chain, contracts, wallet, source_rpc, dest_rpc, output, format):
    """
    Generate migration compatibility report

    Generate a comprehensive report analyzing migration feasibility,
    contract compatibility, cost estimation, and potential issues.

    \b
    Examples:
      # Console report
      varitykit migrate report --source-chain 1

      # Markdown report with contract analysis
      varitykit migrate report --source-chain 1 \\
        --contracts 0xContract1,0xContract2 \\
        --format markdown --output report.md

      # JSON report for programmatic use
      varitykit migrate report --source-chain 1 \\
        --wallet 0xYourAddress --format json --output report.json

    \b
    Report includes:
      • Chain compatibility analysis
      • Contract deployability assessment
      • Gas cost estimation (source vs. destination)
      • Storage cost comparison
      • Wallet balance analysis
      • Migration risk assessment
      • Cost savings calculation (vs. AWS/GCS)

    \b
    Output formats:
      • console: Formatted terminal output
      • json: Machine-readable JSON
      • markdown: Documentation-ready markdown
    """
    args = ["report", "--source-chain", source_chain]

    if dest_chain:
        args.extend(["--dest-chain", dest_chain])
    if contracts:
        args.extend(["--contracts", contracts])
    if wallet:
        args.extend(["--wallet", wallet])
    if source_rpc:
        args.extend(["--source-rpc", source_rpc])
    if dest_rpc:
        args.extend(["--dest-rpc", dest_rpc])
    if output:
        args.extend(["--output", output])
    if format:
        args.extend(["--format", format])

    run_varity_migrate(args)
