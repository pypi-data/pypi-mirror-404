"""RL course-specific CLI commands."""

from pathlib import Path
import click
import sys
import logging
import importlib.metadata
from packaging.version import parse as parse_version

from ..utils import check_last_mastermind


@click.group(name="rl")
def rl_group():
    """Commandes spécifiques au module RL"""
    pass


@click.option("--hide", is_flag=True)
@click.option("--debug", is_flag=True)
@click.option("--error-handling", is_flag=True, help="Catch exceptions within agents")
@click.option(
    "--output",
    default=None,
    type=Path,
    help="Path for output JSON file (none = standard output)",
)
@click.option(
    "--no-check", is_flag=True, help="Do not check if master-mind is up to date"
)
@click.option(
    "--interaction",
    type=click.Choice(["none", "interactive", "map"]),
    help="Race interaction type (when debugging)",
)
@click.option(
    "--num-karts",
    type=int,
    help="Number of karts (must be greater than number of zip files)",
)
@click.option(
    "--max-paths",
    type=int,
    help="Limit on the number of paths for the environment",
)
@click.option(
    "--action-timeout",
    type=float,
    default=None,
    help="Maximum time in seconds allowed for each agent action (default: no timeout)",
)
@click.argument("file_or_modules", type=str, nargs=-1)
@rl_group.command("stk-race")
def rld_stk_race(
    no_check,
    hide,
    max_paths: int | None,
    debug,
    num_karts,
    file_or_modules,
    interaction,
    output,
    error_handling,
    action_timeout,
):
    """Race"""
    # Get original args for self-update
    original_args = [arg for arg in sys.argv]

    if not no_check:
        check_last_mastermind(original_args)

        version = parse_version(importlib.metadata.version("pystk2_gymnasium"))
        assert version >= parse_version("0.7.2") and version < parse_version("0.8.0"), (
            f"Expected pytstk2-gymnasium version 0.7.*, got {version}. Please update."
        )

    if debug:
        logging.getLogger().setLevel(logging.DEBUG)

    from master_mind.rld.stk import race, InteractionMode

    if num_karts < 1 or len(file_or_modules) == 0:
        logging.error("At least one kart")
        sys.exit(1)

    race(
        hide,
        num_karts,
        file_or_modules,
        interaction=InteractionMode[(interaction or "NONE").upper()],
        output=output,
        max_paths=max_paths,
        error_handling=error_handling,
        action_timeout=action_timeout,
    )
