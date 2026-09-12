"""Load prompt templates from agents/prompts/.

Uses importlib.resources rather than __file__-relative paths, so it resolves
identically whether the package is run from the repo, installed, or copied into
a container image.

Slots use string.Template ($name), not str.format. Prompts routinely contain
literal braces — a JSON example, a dict — and .format() would raise on them.

Status: implemented.
"""

from __future__ import annotations

from importlib.resources import files
from string import Template

PACKAGE = "agents.prompts"


def load(name: str) -> str:
    """Return the raw template text. `name` is the filename without .md."""
    return files(PACKAGE).joinpath(f"{name}.md").read_text(encoding="utf-8")


def render(name: str, **slots: object) -> str:
    """Load a template and substitute $slots.

    Raises KeyError naming the missing slot rather than silently leaving a
    literal `$objective` in a prompt the model then has to interpret.
    """
    return Template(load(name)).substitute(**slots)


def available() -> list[str]:
    """Template names present in the package, for sanity checks and logging."""
    return sorted(
        p.name.removesuffix(".md")
        for p in files(PACKAGE).iterdir()
        if p.name.endswith(".md")
    )
