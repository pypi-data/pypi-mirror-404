"""Plugin discovery mechanism for master-mind courses.

This module provides functions to discover and load course plugins
via Python entry points.
"""

import logging
from dataclasses import dataclass
from typing import Dict, Optional
from importlib.metadata import entry_points

from .plugin import CoursePlugin

# Entry point group for course plugins
ENTRY_POINT_GROUP = "master_mind.courses"


@dataclass
class FailedPlugin:
    """Information about a plugin that failed to load."""

    name: str
    package_name: str
    error: str


# Cache for discovered plugins
_discovered_plugins: Optional[Dict[str, CoursePlugin]] = None
_failed_plugins: Optional[Dict[str, FailedPlugin]] = None


def discover_plugins() -> Dict[str, CoursePlugin]:
    """Discover all installed course plugins via entry points.

    Returns a dictionary mapping course names to plugin instances.
    Results are cached after first call.
    """
    global _discovered_plugins, _failed_plugins

    if _discovered_plugins is not None:
        return _discovered_plugins

    _discovered_plugins = {}
    _failed_plugins = {}

    # Python 3.10+ style entry_points API
    eps = entry_points(group=ENTRY_POINT_GROUP)

    for ep in eps:
        try:
            plugin_class = ep.load()
            plugin_instance = plugin_class()

            # Validate that the entry point name matches the plugin name
            if ep.name != plugin_instance.name:
                logging.warning(
                    "Plugin entry point name '%s' does not match plugin name '%s'",
                    ep.name,
                    plugin_instance.name,
                )

            _discovered_plugins[ep.name] = plugin_instance
            logging.debug("Discovered course plugin: %s", ep.name)

        except Exception as e:
            # Track failed plugins so they can still be upgraded
            package_name = ep.dist.name if ep.dist else f"su_master_mind_{ep.name}"
            _failed_plugins[ep.name] = FailedPlugin(
                name=ep.name,
                package_name=package_name,
                error=str(e),
            )
            logging.warning("Failed to load course plugin '%s': %s", ep.name, e)

    return _discovered_plugins


def get_failed_plugins() -> Dict[str, FailedPlugin]:
    """Get plugins that failed to load.

    Returns a dictionary mapping course names to FailedPlugin info.
    Must be called after discover_plugins().
    """
    global _failed_plugins

    if _failed_plugins is None:
        discover_plugins()

    return _failed_plugins or {}


def get_plugin(name: str) -> Optional[CoursePlugin]:
    """Get a specific plugin by name.

    Args:
        name: The course name (e.g., 'llm', 'rl')

    Returns:
        The plugin instance if found, None otherwise.
    """
    plugins = discover_plugins()
    return plugins.get(name)


def get_all_course_names() -> list[str]:
    """Get list of all available course names.

    Returns:
        Sorted list of course names from discovered plugins.
    """
    return sorted(discover_plugins().keys())


def clear_plugin_cache() -> None:
    """Clear the plugin cache.

    Useful for testing or when plugins are installed/uninstalled
    during runtime.
    """
    global _discovered_plugins, _failed_plugins
    _discovered_plugins = None
    _failed_plugins = None
