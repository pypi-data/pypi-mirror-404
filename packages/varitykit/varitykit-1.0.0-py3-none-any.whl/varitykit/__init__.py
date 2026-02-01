"""
VarityKit - AI-powered CLI for building dashboards on Varity L3
"""

__version__ = "1.0.0"
__author__ = "Varity Team"
__email__ = "hello@varity.com"


# Lazy import to avoid circular import warnings
def __getattr__(name):
    if name == "cli":
        from varitykit.cli.main import cli

        return cli
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["cli", "__version__"]
