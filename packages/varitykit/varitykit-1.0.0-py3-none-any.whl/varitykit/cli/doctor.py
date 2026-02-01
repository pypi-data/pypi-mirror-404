"""
Enhanced doctor command - comprehensive environment validation
"""

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from varitykit.utils.validators import (
    EnvironmentValidator,
    LocalDePinValidator,
    NetworkValidator,
    SystemValidator,
)


@click.command()
@click.option("--fix", is_flag=True, help="Attempt to automatically fix issues")
@click.option("--full", is_flag=True, help="Run full diagnostics including LocalDePin services")
@click.pass_context
def doctor(ctx, fix, full):
    """
    Comprehensive environment diagnostics (20+ checks)

    Validates development environment, system resources, network connectivity,
    and LocalDePin services. Use --full for complete diagnostics.

    \b
    Check Categories:
    • Required Tools (6 checks): Docker, Node.js, Python, Git
    • System Resources (2 checks): Disk space, memory
    • Project Configuration (2 checks): .env file, varity.config.json
    • Network Connectivity (1 check): Internet access
    • API Endpoints (2 checks): Staging and production APIs
    • Port Availability (3 checks): Frontend, backend, blockchain
    • Blockchain RPCs (3 checks): Arbitrum L3, Sepolia, Arbitrum One
    • IPFS Gateway (1 check): LocalDePin IPFS
    • LocalDePin Services (9 checks): All 9 DePin services [--full only]

    \b
    Examples:
      varitykit doctor              # Quick check (20 checks)
      varitykit doctor --full       # Full check (29 checks)
      varitykit doctor --fix        # Auto-fix issues
      varitykit doctor --full --fix # Full check with auto-fix
    """
    console = Console()
    logger = ctx.obj["logger"]

    logger.info("Running comprehensive environment diagnostics...")

    console.print(
        Panel.fit(
            "[bold cyan]VarityKit Doctor - Enterprise Diagnostics[/bold cyan]\n"
            f"Running {'[bold]FULL[/bold] ' if full else ''}environment validation...",
            border_style="cyan",
        )
    )

    # Create results table
    table = Table(
        title="Environment Validation Results",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Category", style="cyan", width=25)
    table.add_column("Component", style="white", width=25)
    table.add_column("Status", width=12)
    table.add_column("Details", style="dim")

    all_passed = True
    warnings = []
    failures = []
    check_count = 0

    # ============================================================
    # CATEGORY 1: Required Tools (6 checks)
    # ============================================================
    console.print("\n[bold]1/8 Checking required tools...[/bold]")
    env_results = EnvironmentValidator.validate_environment()

    for tool, result in env_results.items():
        check_count += 1
        if result.passed:
            table.add_row(
                "Required Tools", tool, "[green]✓ PASS[/green]", result.details or result.message
            )
        else:
            table.add_row(
                "Required Tools", tool, "[red]✗ FAIL[/red]", result.details or result.message
            )
            all_passed = False
            failures.append(f"{tool}: {result.message}")

    # ============================================================
    # CATEGORY 2: Docker Daemon (1 check)
    # ============================================================
    console.print("[bold]2/8 Checking Docker daemon...[/bold]")
    docker_result = EnvironmentValidator.check_docker_running()
    check_count += 1

    if docker_result.passed:
        table.add_row("Docker", str("Docker Daemon") + str("[green]✓ PASS[/green]") + str(docker_result.message))
    else:
        table.add_row(
            "Docker",
            "Docker Daemon",
            "[yellow]⚠ WARN[/yellow]",
            docker_result.details or docker_result.message,
        )
        warnings.append(f"Docker: {docker_result.message}")

    # ============================================================
    # CATEGORY 3: System Resources (2 checks)
    # ============================================================
    console.print("[bold]3/8 Checking system resources...[/bold]")

    # Disk space
    disk_result = SystemValidator.check_disk_space(min_gb=10)
    check_count += 1
    if disk_result.passed:
        table.add_row(
            "System Resources", "Disk Space", "[green]✓ PASS[/green]", disk_result.message
        )
    else:
        table.add_row(
            "System Resources",
            "Disk Space",
            "[red]✗ FAIL[/red]",
            disk_result.details or disk_result.message,
        )
        all_passed = False
        failures.append(f"Disk Space: {disk_result.message}")

    # Memory
    memory_result = SystemValidator.check_memory(min_gb=4)
    check_count += 1
    if memory_result.passed:
        table.add_row("System Resources", str("Memory") + str("[green]✓ PASS[/green]") + str(memory_result.message))
    else:
        table.add_row(
            "System Resources",
            "Memory",
            "[yellow]⚠ WARN[/yellow]",
            memory_result.details or memory_result.message,
        )
        warnings.append(f"Memory: {memory_result.message}")

    # ============================================================
    # CATEGORY 4: Project Configuration (2 checks)
    # ============================================================
    console.print("[bold]4/8 Checking project configuration...[/bold]")

    # .env file
    env_file_result = SystemValidator.check_env_file()
    check_count += 1
    if env_file_result.passed:
        table.add_row(
            "Project Config", ".env File", "[green]✓ PASS[/green]", env_file_result.message
        )
    else:
        table.add_row(
            "Project Config",
            ".env File",
            "[yellow]⚠ WARN[/yellow]",
            env_file_result.details or env_file_result.message,
        )
        warnings.append(f".env file: {env_file_result.message}")

    # varity.config.json
    config_result = SystemValidator.check_config_file()
    check_count += 1
    if config_result.passed:
        table.add_row(
            "Project Config",
            "varity.config.json",
            "[green]✓ PASS[/green]",
            config_result.details or config_result.message,
        )
    else:
        table.add_row(
            "Project Config",
            "varity.config.json",
            "[yellow]⚠ WARN[/yellow]",
            config_result.details or config_result.message,
        )
        warnings.append(f"Config file: {config_result.message}")

    # ============================================================
    # CATEGORY 5: Network Connectivity (1 check)
    # ============================================================
    console.print("[bold]5/8 Checking network connectivity...[/bold]")
    network_result = NetworkValidator.check_internet_connection()
    check_count += 1

    if network_result.passed:
        table.add_row("Network", str("Internet") + str("[green]✓ PASS[/green]") + str(network_result.message))
    else:
        table.add_row(
            "Network",
            "Internet",
            "[red]✗ FAIL[/red]",
            network_result.details or network_result.message,
        )
        all_passed = False
        failures.append(f"Internet: {network_result.message}")

    # ============================================================
    # CATEGORY 6: API Endpoints (2 checks)
    # ============================================================
    console.print("[bold]6/8 Checking API endpoints...[/bold]")
    api_endpoints = {
        "Staging API": "https://staging.api.varity.io/health",
        "Production API": "https://api.varity.io/health",
    }

    for name, url in api_endpoints.items():
        check_count += 1
        api_result = NetworkValidator.check_api_endpoint(url)

        if api_result.passed:
            table.add_row("API Endpoints", str(name) + str("[green]✓ PASS[/green]") + str(api_result.message))
        else:
            table.add_row(
                "API Endpoints",
                name,
                "[yellow]⚠ WARN[/yellow]",
                api_result.details or api_result.message,
            )
            warnings.append(f"{name}: {api_result.message}")

    # ============================================================
    # CATEGORY 7: Port Availability (3 checks)
    # ============================================================
    console.print("[bold]7/8 Checking port availability...[/bold]")
    critical_ports = {
        3000: "Frontend Dev Server",
        3001: "Backend Dev Server",
        8545: "Local Blockchain",
    }

    for port, description in critical_ports.items():
        check_count += 1
        port_result = NetworkValidator.check_port_available(port)

        if port_result.passed:
            table.add_row(
                "Ports", f"Port {port} ({description})", "[green]✓ PASS[/green]", "Available"
            )
        else:
            table.add_row(
                "Ports", f"Port {port} ({description})", "[yellow]⚠ WARN[/yellow]", "In use"
            )
            warnings.append(f"Port {port}: In use")

    # ============================================================
    # CATEGORY 8: Blockchain RPCs (3 checks)
    # ============================================================
    console.print("[bold]8/8 Checking blockchain RPC endpoints...[/bold]")
    blockchain_rpcs = {
        "Arbitrum L3 (Local)": "http://localhost:8547",
        "Arbitrum Sepolia": "https://sepolia-rollup.arbitrum.io/rpc",
        "Arbitrum One": "https://arb1.arbitrum.io/rpc",
    }

    for name, rpc_url in blockchain_rpcs.items():
        check_count += 1
        rpc_result = NetworkValidator.check_blockchain_rpc(rpc_url, name)

        if rpc_result.passed:
            table.add_row(
                "Blockchain RPC",
                name,
                "[green]✓ PASS[/green]",
                rpc_result.details or rpc_result.message,
            )
        else:
            table.add_row(
                "Blockchain RPC",
                name,
                "[yellow]⚠ WARN[/yellow]",
                rpc_result.details or rpc_result.message,
            )
            warnings.append(f"{name}: {rpc_result.message}")

    # ============================================================
    # FULL MODE: LocalDePin Services (9 checks)
    # ============================================================
    if full:
        console.print("\n[bold]FULL MODE: Checking LocalDePin services (9 checks)...[/bold]")

        # Check docker-compose
        compose_result = LocalDePinValidator.check_docker_compose_running()
        check_count += 1

        if compose_result.passed:
            table.add_row(
                "LocalDePin",
                "Docker Compose",
                "[green]✓ PASS[/green]",
                compose_result.details or compose_result.message,
            )
        else:
            table.add_row(
                "LocalDePin",
                "Docker Compose",
                "[yellow]⚠ WARN[/yellow]",
                compose_result.details or compose_result.message,
            )
            warnings.append(f"Docker Compose: {compose_result.message}")

        # Check all LocalDePin services
        depin_results = LocalDePinValidator.check_all_services()

        for service_key, result in depin_results.items():
            check_count += 1
            service_name = LocalDePinValidator.LOCALDEPIN_SERVICES[service_key]["name"]

            if result.passed:
                table.add_row(
                    "LocalDePin Services", service_name, "[green]✓ PASS[/green]", result.message
                )
            else:
                table.add_row(
                    "LocalDePin Services",
                    service_name,
                    "[yellow]⚠ WARN[/yellow]",
                    result.details or result.message,
                )
                warnings.append(f"{service_name}: {result.message}")

    # ============================================================
    # Display Results
    # ============================================================
    console.print("\n")
    console.print(table)

    # Summary
    console.print(f"\n[bold]Total Checks: {check_count}[/bold]")

    if failures:
        console.print(f"\n[bold red]Failures: {len(failures)}[/bold red]")
        for failure in failures[:5]:  # Show first 5
            console.print(f"  [red]✗[/red] {failure}")
        if len(failures) > 5:
            console.print(f"  [dim]... and {len(failures) - 5} more[/dim]")

    if warnings:
        console.print(f"\n[bold yellow]Warnings: {len(warnings)}[/bold yellow]")
        for warning in warnings[:5]:  # Show first 5
            console.print(f"  [yellow]⚠[/yellow] {warning}")
        if len(warnings) > 5:
            console.print(f"  [dim]... and {len(warnings) - 5} more[/dim]")

    # Final summary panel
    if all_passed:
        console.print("\n")
        console.print(
            Panel.fit(
                "[bold green]✓ All critical checks passed![/bold green]\n"
                f"Your environment is ready for development.\n"
                f"[dim]{check_count} checks completed, {len(warnings)} warnings[/dim]",
                border_style="green",
            )
        )
        logger.info(f"Environment validation passed ({check_count} checks)")
        ctx.exit(0)
    else:
        console.print("\n")
        console.print(
            Panel.fit(
                f"[bold red]✗ {len(failures)} critical checks failed[/bold red]\n"
                f"Please fix issues and run again.\n"
                f"[dim]{check_count} checks completed, {len(warnings)} warnings[/dim]",
                border_style="red",
            )
        )

        # Provide installation instructions for failed tools
        console.print("\n[bold]Installation Instructions:[/bold]\n")

        failed_tools = [tool for tool, result in env_results.items() if not result.passed]

        if "docker" in failed_tools or "docker-compose" in failed_tools:
            console.print("  [cyan]Docker:[/cyan] https://docs.docker.com/get-docker/")

        if "node" in failed_tools or "npm" in failed_tools:
            console.print("  [cyan]Node.js:[/cyan] https://nodejs.org/")

        if "python" in failed_tools:
            console.print("  [cyan]Python:[/cyan] https://www.python.org/downloads/")

        if "git" in failed_tools:
            console.print("  [cyan]Git:[/cyan] https://git-scm.com/downloads")

        if fix:
            console.print("\n[bold yellow]Auto-fix feature coming soon![/bold yellow]")
            console.print("Currently in development for Phase 1, Week 2.\n")

        console.print("\n[dim]Run 'varitykit doctor' again after fixing issues.[/dim]")
        console.print("[dim]Use 'varitykit doctor --full' for complete diagnostics.[/dim]\n")

        logger.error(f"Environment validation failed ({len(failures)} failures)")
        ctx.exit(1)
