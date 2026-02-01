"""
AI-Powered Init Command - Uses AI Configuration Engine for intelligent project generation
"""

import asyncio
import sys
from pathlib import Path

import click
from varitykit.core.ai_engine import AIConfigurationEngine


@click.command(name="init")
@click.argument("output_dir", required=False, default=".")
@click.option("--ai/--no-ai", default=True, help="Use AI-powered configuration (default: True)")
@click.option(
    "--min-quality", type=float, default=85.0, help="Minimum quality score (0-100, default: 85)"
)
def init_command(output_dir, ai, min_quality):
    """
    Initialize new Varity dashboard project (AI-powered)

    This command uses the AI Configuration Engine to generate a complete,
    customized dashboard through conversational interface.

    Examples:
        varitykit init                  # Create in current directory
        varitykit init ./my-dashboard   # Create in specific directory
        varitykit init --no-ai          # Use template-based generation
    """
    if not ai:
        click.echo("Template-based generation not yet implemented.")
        click.echo("Use --ai flag for AI-powered generation (default).")
        sys.exit(1)

    # Run async AI configuration
    asyncio.run(ai_init_flow(output_dir, min_quality))


async def ai_init_flow(output_dir: str, min_quality: float):
    """Main AI-powered initialization flow"""
    try:
        # Initialize AI engine
        ai_engine = AIConfigurationEngine(min_quality_score=min_quality)

        # Run interactive configuration
        requirements = await ai_engine.interactive_configuration()

        # Generate template
        output_path = Path(output_dir).resolve()
        template = await ai_engine.generate_template(requirements, output_path)

        # Validate template
        quality_score = await ai_engine.score_template_quality(template)

        # Display quality score
        print("\n" + "=" * 60)
        print(f"= Quality Score: {quality_score.overall:.1f}/100")
        print("=" * 60)
        print(f"  Code Quality:    {quality_score.code_quality:.1f}/100")
        print(f"  Type Safety:     {quality_score.type_safety:.1f}/100")
        print(f"  Security:        {quality_score.security:.1f}/100")
        print(f"  Performance:     {quality_score.performance:.1f}/100")
        print(f"  Accessibility:   {quality_score.accessibility:.1f}/100")
        print(f"  Documentation:   {quality_score.documentation:.1f}/100")
        print()

        if quality_score.overall >= min_quality:
            # Write template to disk
            success = await ai_engine.write_template(template, output_path)

            if success:
                # Display metrics
                metrics = await ai_engine.track_generation_metrics()
                print("=� Generation Metrics:")
                print(f"  Success Rate: {metrics['success_rate']}")
                print(f"  Average Quality: {metrics['average_quality_score']}")
                print()

                sys.exit(0)
            else:
                click.echo(" Failed to write template files.", err=True)
                sys.exit(1)
        else:
            click.echo(
                f" Quality score too low: {quality_score.overall:.1f}/100 "
                f"(minimum: {min_quality}/100).",
                err=True,
            )
            click.echo("Please try again or adjust requirements.", err=True)
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n�  Initialization cancelled by user.")
        sys.exit(130)
    except Exception as e:
        click.echo(f"\n Error during initialization: {e}", err=True)
        import traceback

        traceback.print_exc()
        sys.exit(1)
