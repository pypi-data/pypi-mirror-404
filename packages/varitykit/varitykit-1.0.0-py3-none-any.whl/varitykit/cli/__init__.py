"""
CLI module for VarityKit
"""


# Lazy import to avoid circular import warnings when running with -m
def __getattr__(name):
    if name == "cli":
        from varitykit.cli.main import cli

        return cli
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["cli"]
