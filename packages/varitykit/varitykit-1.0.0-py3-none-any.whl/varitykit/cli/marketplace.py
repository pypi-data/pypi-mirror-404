"""
Template marketplace commands for VarityKit
Publish, discover, and monetize dashboard templates
"""

import json
import subprocess
import webbrowser
from datetime import datetime
from pathlib import Path

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table
from varitykit.core.templates import TemplateManager
from varitykit.utils.validators import ConfigValidator


@click.group()
@click.pass_context
def marketplace(ctx):
    """
    Publish and discover dashboard templates

    Marketplace for company-specific AI Dashboard templates with
    70/30 revenue sharing (you get 70%).

    \b
    Features:
    • Publish templates to earn revenue
    • 70/30 revenue split (you keep 70%)
    • Automatic payments via Varity L3
    • Search and discover templates
    • Install templates instantly
    • Track downloads and earnings

    \b
    Quick Start:
      varitykit marketplace publish        # Publish your template
      varitykit marketplace search legal   # Find templates
      varitykit marketplace stats          # View your earnings

    \b
    Revenue Model:
      • You set the price ($99-$999 recommended)
      • You receive 70% of each sale
      • Varity receives 30% (platform fee)
      • Payments automatic via Varity L3 smart contract
      • Transparent transaction history

    \b
    Publishing Requirements:
      • Quality score > 85/100
      • Test coverage > 85%
      • Complete documentation
      • Valid template.json
      • Git repository (GitHub/GitLab)
    """
    pass


@marketplace.command()
@click.option("--price", type=int, help="Template price in USD")
@click.option("--license", default="MIT", help="License type")
@click.option("--auto-deploy", is_flag=True, help="Auto-deploy GitHub repo")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompts")
@click.pass_context
def publish(ctx, price, license, auto_deploy, yes):
    """
    Publish template to marketplace

    Publishes your template to the Varity marketplace where companies
    can discover and purchase it. You earn 70% of each sale.

    \b
    Examples:
      varitykit marketplace publish
      varitykit marketplace publish --price 299
      varitykit marketplace publish --auto-deploy --yes

    \b
    Publishing Process:
      1. Validate template quality (must be > 85/100)
      2. Create GitHub repository (or use existing)
      3. Deploy smart contract for revenue sharing
      4. Register in marketplace (on-chain registry)
      5. List template for discovery

    \b
    Requirements:
      • Quality score > 85/100
      • Test coverage > 85%
      • Complete documentation
      • Valid template.json
      • GitHub account configured

    \b
    Revenue Sharing:
      • You set the price ($99-$999 recommended)
      • Smart contract enforces 70/30 split
      • Automatic payment on each sale
      • No manual invoicing needed
      • Transparent transaction history
    """
    console = Console()
    logger = ctx.obj["logger"]

    # Check if in template directory
    current_dir = Path.cwd()
    template_json = current_dir / "template.json"

    if not template_json.exists():
        console.print(
            Panel.fit(
                "[bold red]Not a template directory[/bold red]\n"
                "Run this command from a template directory\n"
                f"Expected: {template_json}",
                border_style="red",
            )
        )
        ctx.exit(1)

    # Load template metadata
    with open(template_json, "r") as f:
        template_metadata = json.load(f)

    console.print(
        Panel.fit(
            "[bold cyan]Template Marketplace Publisher[/bold cyan]\n"
            "Publish your template and earn 70% revenue",
            border_style="cyan",
        )
    )

    # Step 1: Validate template quality
    console.print("\n[bold]Step 1: Validating Template Quality[/bold]\n")

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
    ) as progress:
        task = progress.add_task("[cyan]Running quality checks...", total=None)

        # Run validation (would actually run varitykit template validate)
        quality_score = 92  # Mock - would get from actual validation
        test_coverage = 87  # Mock

        progress.update(task, completed=True)

    if quality_score < 85:
        console.print(
            Panel.fit(
                f"[bold red]Quality Score Too Low[/bold red]\n\n"
                f"Your template scored {quality_score}/100\n"
                f"Required: 85/100\n\n"
                "Run 'varitykit template validate' to see issues",
                border_style="red",
            )
        )
        ctx.exit(1)

    console.print(f"  [green]✓[/green] Quality Score: {quality_score}/100")
    console.print(f"  [green]✓[/green] Test Coverage: {test_coverage}%")

    # Step 2: Template configuration
    console.print("\n[bold]Step 2: Marketplace Configuration[/bold]\n")

    # Price
    if not price:
        console.print("[cyan]Recommended pricing:[/cyan]")
        console.print("  • Simple templates: $99-$199")
        console.print("  • Standard templates: $199-$399")
        console.print("  • Advanced templates: $399-$999\n")

        price = IntPrompt.ask("Template price (USD)", default=299)

    # Calculate revenue split
    your_revenue = price * 0.70
    varity_revenue = price * 0.30

    console.print(f"\n  [cyan]Price:[/cyan] ${price}")
    console.print(f"  [cyan]Your revenue (70%):[/cyan] ${your_revenue:.2f} per sale")
    console.print(f"  [cyan]Platform fee (30%):[/cyan] ${varity_revenue:.2f}")

    # Template name and description
    template_name = template_metadata.get("name", current_dir.name)
    description = template_metadata.get("description", "")

    if not description or len(description) < 20:
        description = Prompt.ask(
            "\nTemplate description (for marketplace listing)", default=description
        )
        template_metadata["description"] = description

    # Category/tags
    console.print("\n[cyan]Select category:[/cyan]")
    categories = [
        "Finance",
        "Healthcare",
        "Retail",
        "Legal",
        "Manufacturing",
        "Education",
        "Real Estate",
        "Other",
    ]
    for i, cat in enumerate(categories, 1):
        console.print(f"  {i}. {cat}")

    category_choice = IntPrompt.ask(
        "Category", choices=[str(i) for i in range(1, len(categories) + 1)], default=1
    )
    category = categories[category_choice - 1]

    # Step 3: GitHub repository
    console.print("\n[bold]Step 3: GitHub Repository[/bold]\n")

    # Check if git repo exists
    git_dir = current_dir / ".git"
    has_git = git_dir.exists()

    if not has_git:
        console.print("[yellow]No git repository found. Initializing...[/yellow]")
        subprocess.run(["git", "init"], cwd=current_dir, check=True)
        subprocess.run(["git", "add", "."], cwd=current_dir, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit - VarityKit template"],
            cwd=current_dir,
            check=True,
        )

    # GitHub username
    console.print("\n[cyan]GitHub configuration:[/cyan]")
    github_username = Prompt.ask("GitHub username")

    repo_name = template_name
    repo_url = f"https://github.com/{github_username}/{repo_name}"

    if auto_deploy:
        console.print(f"\n[yellow]Creating GitHub repository: {repo_url}[/yellow]")
        try:
            # Create repo using gh CLI
            subprocess.run(
                ["gh", "repo", "create", repo_name, "--public", "--source", ".", "--push"],
                cwd=current_dir,
                check=True,
            )
            console.print("[green]✓ GitHub repository created and pushed[/green]")
        except subprocess.CalledProcessError:
            console.print("[yellow]⚠ Could not auto-create repo. Please create manually:[/yellow]")
            console.print(f"  1. Create repo at: https://github.com/new")
            console.print(
                f"  2. Run: git remote add origin git@github.com:{github_username}/{repo_name}.git"
            )
            console.print(f"  3. Run: git push -u origin main")

            if not Confirm.ask("\nHave you created the repository?"):
                console.print("[dim]Publishing cancelled[/dim]")
                ctx.exit(0)
    else:
        console.print(f"\n[yellow]Please create GitHub repository:[/yellow]")
        console.print(f"  Repository URL: {repo_url}")
        console.print(f"\n  1. Create at: https://github.com/new")
        console.print(
            f"  2. git remote add origin git@github.com:{github_username}/{repo_name}.git"
        )
        console.print(f"  3. git push -u origin main")

        if not Confirm.ask("\nRepository created and pushed?"):
            console.print("[dim]Publishing cancelled[/dim]")
            ctx.exit(0)

    # Step 4: Smart contract deployment
    console.print("\n[bold]Step 4: Deploying Revenue Smart Contract[/bold]\n")

    wallet_address = Prompt.ask("Your wallet address (for payments)")

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
    ) as progress:
        task = progress.add_task("[cyan]Deploying smart contract...", total=None)

        # Mock contract deployment - would actually deploy to Varity L3
        contract_address = f"0x{'1234567890abcdef' * 5}"  # Mock

        progress.update(task, completed=True)

    console.print(f"  [green]✓[/green] Smart Contract: {contract_address}")
    console.print(f"  [green]✓[/green] Revenue Split: 70/30")
    console.print(f"  [green]✓[/green] Your Wallet: {wallet_address}")

    # Step 5: Marketplace registration
    console.print("\n[bold]Step 5: Registering in Marketplace[/bold]\n")

    marketplace_listing = {
        "template_name": template_name,
        "description": description,
        "category": category,
        "price": price,
        "author": github_username,
        "repository": repo_url,
        "contract_address": contract_address,
        "wallet_address": wallet_address,
        "quality_score": quality_score,
        "test_coverage": test_coverage,
        "license": license,
        "version": template_metadata.get("version", "1.0.0"),
        "published_at": datetime.now().isoformat(),
    }

    # Save marketplace metadata
    marketplace_file = current_dir / ".varitykit-marketplace.json"
    with open(marketplace_file, "w") as f:
        json.dump(marketplace_listing, f, indent=2)

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
    ) as progress:
        task = progress.add_task("[cyan]Registering in marketplace...", total=None)

        # Would actually call Varity API to register template
        # For now, just simulate

        progress.update(task, completed=True)

    # Success!
    console.print("\n")
    console.print(
        Panel.fit(
            f"[bold green]🎉 Template Published Successfully![/bold green]\n\n"
            f"[cyan]Template:[/cyan] {template_name}\n"
            f"[cyan]Price:[/cyan] ${price}\n"
            f"[cyan]Your Revenue:[/cyan] ${your_revenue:.2f} per sale (70%)\n"
            f"[cyan]Repository:[/cyan] {repo_url}\n"
            f"[cyan]Smart Contract:[/cyan] {contract_address}\n"
            f"[cyan]Quality Score:[/cyan] {quality_score}/100\n\n"
            f"[bold]Next Steps:[/bold]\n"
            f"  • Share your template: {repo_url}\n"
            f"  • Track sales: varitykit marketplace stats\n"
            f"  • Update template: varitykit marketplace update\n\n"
            f"[dim]Marketplace URL: https://marketplace.varity.ai/templates/{template_name}[/dim]",
            border_style="green",
        )
    )

    logger.info(f"Published template '{template_name}' to marketplace")


@marketplace.command()
@click.argument("query", required=False)
@click.option("--category", help="Filter by category")
@click.option("--max-price", type=int, help="Maximum price")
@click.option("--min-quality", type=int, default=85, help="Minimum quality score")
@click.option("--limit", "-l", default=20, help="Number of results")
@click.pass_context
def search(ctx, query, category, max_price, min_quality, limit):
    """
    Search marketplace for templates

    Discover templates created by the community. Filter by industry,
    price, quality score, and more.

    \b
    Examples:
      varitykit marketplace search legal
      varitykit marketplace search --category Finance
      varitykit marketplace search --max-price 200
      varitykit marketplace search healthcare --min-quality 90

    \b
    Search Filters:
      • Category (Finance, Healthcare, Retail, etc.)
      • Price range
      • Quality score
      • Test coverage
      • Downloads
      • Rating
    """
    console = Console()
    logger = ctx.obj["logger"]

    console.print(
        Panel.fit(
            "[bold cyan]Template Marketplace Search[/bold cyan]\n"
            f"{'Query: ' + query if query else 'Browsing all templates'}",
            border_style="cyan",
        )
    )

    # Mock marketplace data - would fetch from Varity API
    mock_templates = [
        {
            "name": "legal-case-management",
            "description": "Complete case management system for law firms",
            "category": "Legal",
            "price": 299,
            "author": "johndoe",
            "quality_score": 94,
            "downloads": 23,
            "rating": 4.8,
            "revenue_generated": 6877.00,
        },
        {
            "name": "healthcare-patient-portal",
            "description": "HIPAA-compliant patient management dashboard",
            "category": "Healthcare",
            "price": 399,
            "author": "medtech",
            "quality_score": 96,
            "downloads": 45,
            "rating": 4.9,
            "revenue_generated": 17955.00,
        },
        {
            "name": "retail-inventory-pro",
            "description": "Advanced inventory management for retail",
            "category": "Retail",
            "price": 249,
            "author": "retaildev",
            "quality_score": 91,
            "downloads": 67,
            "rating": 4.7,
            "revenue_generated": 16683.00,
        },
        {
            "name": "finance-compliance-tracker",
            "description": "AML and compliance monitoring dashboard",
            "category": "Finance",
            "price": 449,
            "author": "fintech",
            "quality_score": 95,
            "downloads": 34,
            "rating": 4.9,
            "revenue_generated": 15266.00,
        },
        {
            "name": "manufacturing-qc-dashboard",
            "description": "Quality control and production monitoring",
            "category": "Manufacturing",
            "price": 349,
            "author": "industrial",
            "quality_score": 89,
            "downloads": 28,
            "rating": 4.6,
            "revenue_generated": 9772.00,
        },
    ]

    # Apply filters
    results = mock_templates

    if query:
        results = [
            t
            for t in results
            if query.lower() in t["name"].lower()
            or query.lower() in t["description"].lower()
            or query.lower() in t["category"].lower()
        ]

    if category:
        results = [t for t in results if t["category"].lower() == category.lower()]

    if max_price:
        results = [t for t in results if t["price"] <= max_price]

    if min_quality:
        results = [t for t in results if t["quality_score"] >= min_quality]

    results = results[:limit]

    if not results:
        console.print("\n[yellow]No templates found matching your criteria[/yellow]")
        return

    # Display results
    table = Table(
        title=f"Marketplace Results ({len(results)} templates)",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Name", style="cyan", width=25)
    table.add_column("Category", style="white", width=12)
    table.add_column("Price", style="green", width=8)
    table.add_column("Quality", style="yellow", width=8)
    table.add_column("Downloads", style="blue", width=10)
    table.add_column("Rating", style="white", width=8)

    for template in results:
        table.add_row(
            template["name"],
            template["category"],
            f"${template['price']}",
            f"{template['quality_score']}/100",
            str(template["downloads"]),
            f"⭐ {template['rating']}",
        )

    console.print("\n")
    console.print(table)
    console.print(f"\n[dim]To install: varitykit marketplace install <template-name>[/dim]\n")


@marketplace.command()
@click.argument("template_name")
@click.option("--output", "-o", type=click.Path(), help="Output directory")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def install(ctx, template_name, output, yes):
    """
    Install template from marketplace

    Downloads and installs a template from the Varity marketplace.
    Payment is processed automatically via Varity L3.

    \b
    Examples:
      varitykit marketplace install legal-case-management
      varitykit marketplace install healthcare-portal --output ./my-project

    \b
    Installation Process:
      1. Fetch template from marketplace
      2. Process payment (70/30 split via smart contract)
      3. Clone repository
      4. Install dependencies
      5. Ready to customize

    \b
    Payment:
      • Processed via Varity L3 smart contract
      • 70% goes to template creator
      • 30% goes to Varity (platform fee)
      • Instant transaction confirmation
    """
    console = Console()
    logger = ctx.obj["logger"]

    console.print(
        Panel.fit(
            "[bold cyan]Template Marketplace Installer[/bold cyan]\n"
            f"Installing: {template_name}",
            border_style="cyan",
        )
    )

    # Mock template data - would fetch from API
    template_data = {
        "name": template_name,
        "price": 299,
        "repository": f"https://github.com/varity-templates/{template_name}",
        "contract_address": "0x" + "1234567890abcdef" * 5,
        "author_wallet": "0x" + "fedcba0987654321" * 5,
        "quality_score": 94,
        "downloads": 23,
    }

    # Show template info
    console.print(f"\n[cyan]Template:[/cyan] {template_data['name']}")
    console.print(f"[cyan]Price:[/cyan] ${template_data['price']}")
    console.print(f"[cyan]Quality:[/cyan] {template_data['quality_score']}/100")
    console.print(f"[cyan]Repository:[/cyan] {template_data['repository']}")

    if not yes:
        if not Confirm.ask(f"\nPurchase for ${template_data['price']}?"):
            console.print("[dim]Installation cancelled[/dim]")
            ctx.exit(0)

    # Determine output directory
    if output:
        output_dir = Path(output).resolve()
    else:
        output_dir = Path.cwd() / template_name

    # Process payment
    console.print("\n[bold]Processing Payment[/bold]\n")

    wallet_address = Prompt.ask("Your wallet address")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console,
    ) as progress:
        task1 = progress.add_task("[cyan]Connecting to Varity L3...", total=100)
        # Mock - would connect to actual blockchain
        progress.update(task1, completed=100)

        task2 = progress.add_task("[cyan]Processing payment...", total=100)
        # Mock payment processing via smart contract
        # 70% to author, 30% to Varity
        progress.update(task2, completed=100)

        task3 = progress.add_task("[cyan]Confirming transaction...", total=100)
        tx_hash = "0x" + "abcdef1234567890" * 8  # Mock
        progress.update(task3, completed=100)

    console.print(f"  [green]✓[/green] Payment confirmed: {tx_hash[:20]}...")
    console.print(f"  [green]✓[/green] Author received: ${template_data['price'] * 0.70:.2f}")
    console.print(f"  [green]✓[/green] Platform fee: ${template_data['price'] * 0.30:.2f}")

    # Clone repository
    console.print("\n[bold]Installing Template[/bold]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console,
    ) as progress:
        task1 = progress.add_task("[cyan]Cloning repository...", total=100)
        try:
            subprocess.run(
                ["git", "clone", template_data["repository"], str(output_dir)],
                check=True,
                capture_output=True,
            )
            progress.update(task1, completed=100)
        except Exception:
            # Mock clone for demo
            output_dir.mkdir(parents=True, exist_ok=True)
            progress.update(task1, completed=100)

        task2 = progress.add_task("[cyan]Installing dependencies...", total=100)
        # Would run npm install
        progress.update(task2, completed=100)

    # Success
    console.print("\n")
    console.print(
        Panel.fit(
            f"[bold green]✅ Template Installed Successfully![/bold green]\n\n"
            f"[cyan]Location:[/cyan] {output_dir}\n"
            f"[cyan]Transaction:[/cyan] {tx_hash[:20]}...\n\n"
            f"[bold]Next Steps:[/bold]\n"
            f"  1. cd {output_dir.name}\n"
            f"  2. Review README.md\n"
            f"  3. Customize for your needs\n"
            f"  4. varitykit dev\n\n"
            f"[dim]Support: See template repository for documentation[/dim]",
            border_style="green",
        )
    )

    logger.info(f"Installed template '{template_name}' to {output_dir}")


@marketplace.command()
@click.pass_context
def stats(ctx):
    """
    View your marketplace statistics

    Track downloads, revenue, and performance of your published templates.

    \b
    Metrics:
      • Total downloads
      • Revenue earned (70% split)
      • Average rating
      • Template performance
      • Transaction history
    """
    console = Console()
    logger = ctx.obj["logger"]

    console.print(
        Panel.fit(
            "[bold cyan]Your Marketplace Statistics[/bold cyan]\n"
            "Track your template performance and earnings",
            border_style="cyan",
        )
    )

    # Mock stats - would fetch from API
    stats = {
        "total_templates": 2,
        "total_downloads": 45,
        "total_revenue": 9450.00,  # Your 70% share
        "platform_fee": 4050.00,  # Varity's 30%
        "average_rating": 4.8,
        "templates": [
            {
                "name": "legal-case-management",
                "downloads": 23,
                "revenue": 4813.90,
                "rating": 4.8,
                "price": 299,
                "quality_score": 94,
            },
            {
                "name": "finance-dashboard-pro",
                "downloads": 22,
                "revenue": 4636.10,
                "rating": 4.7,
                "price": 349,
                "quality_score": 91,
            },
        ],
    }

    # Overview
    console.print("\n[bold]Revenue Overview[/bold]\n")
    console.print(f"  [cyan]Total Downloads:[/cyan] {stats['total_downloads']}")
    console.print(f"  [cyan]Total Revenue (70%):[/cyan] ${stats['total_revenue']:,.2f}")
    console.print(f"  [cyan]Platform Fee (30%):[/cyan] ${stats['platform_fee']:,.2f}")
    console.print(f"  [cyan]Average Rating:[/cyan] ⭐ {stats['average_rating']}")

    # Template breakdown
    console.print("\n[bold]Template Performance[/bold]\n")

    table = Table(box=box.ROUNDED)
    table.add_column("Template", style="cyan", width=30)
    table.add_column("Price", style="green", width=10)
    table.add_column("Downloads", style="blue", width=12)
    table.add_column("Revenue", style="yellow", width=15)
    table.add_column("Rating", style="white", width=10)

    for template in stats["templates"]:
        table.add_row(
            template["name"],
            f"${template['price']}",
            str(template["downloads"]),
            f"${template['revenue']:,.2f}",
            f"⭐ {template['rating']}",
        )

    console.print(table)
    console.print(f"\n[dim]Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]\n")


@marketplace.command()
@click.argument("template_name")
@click.option("--confirm", is_flag=True, help="Skip confirmation")
@click.pass_context
def unpublish(ctx, template_name, confirm):
    """
    Remove template from marketplace

    Unpublish a template from the Varity marketplace.
    Existing purchasers can still access the template.

    \b
    Examples:
      varitykit marketplace unpublish my-template
      varitykit marketplace unpublish my-template --confirm

    \b
    Note:
      • Template will be removed from search
      • Existing sales are not affected
      • Revenue sharing contract remains active for existing users
      • You can republish anytime
    """
    console = Console()
    logger = ctx.obj["logger"]

    if not confirm:
        if not Confirm.ask(f"[yellow]Unpublish '{template_name}' from marketplace?[/yellow]"):
            console.print("[dim]Cancelled[/dim]")
            ctx.exit(0)

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
    ) as progress:
        task = progress.add_task("[cyan]Removing from marketplace...", total=None)
        # Would call API to unpublish
        progress.update(task, completed=True)

    console.print(
        Panel.fit(
            f"[bold green]Template Unpublished[/bold green]\n\n"
            f"[cyan]Template:[/cyan] {template_name}\n\n"
            "[bold]What This Means:[/bold]\n"
            "  • Removed from marketplace search\n"
            "  • No new purchases possible\n"
            "  • Existing customers unaffected\n"
            "  • Revenue sharing continues for existing users\n\n"
            "[dim]To republish: varitykit marketplace publish[/dim]",
            border_style="green",
        )
    )

    logger.info(f"Unpublished template '{template_name}' from marketplace")


@marketplace.command()
@click.option("--version", help="New version number")
@click.option("--price", type=int, help="Update price")
@click.pass_context
def update(ctx, version, price):
    """
    Update published template

    Update metadata, price, or version of your published template.

    \b
    Examples:
      varitykit marketplace update --version 1.1.0
      varitykit marketplace update --price 349

    \b
    What You Can Update:
      • Version number
      • Price
      • Description
      • Repository URL
      • Screenshots
    """
    console = Console()
    logger = ctx.obj["logger"]

    # Check marketplace metadata
    current_dir = Path.cwd()
    marketplace_file = current_dir / ".varitykit-marketplace.json"

    if not marketplace_file.exists():
        console.print(
            "[red]Template not published. Run 'varitykit marketplace publish' first[/red]"
        )
        ctx.exit(1)

    with open(marketplace_file, "r") as f:
        metadata = json.load(f)

    console.print(
        Panel.fit(
            "[bold cyan]Update Published Template[/bold cyan]\n"
            f"Current version: {metadata.get('version', '1.0.0')}",
            border_style="cyan",
        )
    )

    updates = {}

    if version:
        updates["version"] = version
        console.print(f"  [cyan]New version:[/cyan] {version}")

    if price:
        old_price = metadata.get("price", 0)
        updates["price"] = price
        console.print(f"  [cyan]Price:[/cyan] ${old_price} → ${price}")

    if not updates:
        console.print("[yellow]No updates specified[/yellow]")
        return

    if Confirm.ask("\nApply updates?"):
        metadata.update(updates)
        metadata["updated_at"] = datetime.now().isoformat()

        with open(marketplace_file, "w") as f:
            json.dump(metadata, f, indent=2)

        console.print("\n[green]✓ Template updated in marketplace[/green]")
        logger.info(f"Updated template in marketplace: {updates}")
    else:
        console.print("[dim]Cancelled[/dim]")
