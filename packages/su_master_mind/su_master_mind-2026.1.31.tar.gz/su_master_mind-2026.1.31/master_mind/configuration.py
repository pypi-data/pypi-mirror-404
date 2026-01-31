"""Configuration management for master-mind.

This module handles user configuration, specifically tracking which built-in
courses the user is enrolled in. External courses are detected automatically
by their package installation (via entry points).
"""

try:
    from functools import cached_property
except ImportError:
    from cached_property import cached_property
import json
import logging
from pathlib import Path
from appdirs import user_config_dir

from .discovery import discover_plugins


def get_builtin_course_names() -> set:
    """Get set of all built-in course names from discovered plugins."""
    plugins = discover_plugins()
    return {name for name, plugin in plugins.items() if plugin.is_builtin}


def get_external_course_names() -> set:
    """Get set of all external course names from discovered plugins.

    External courses are detected by package installation - if the plugin
    is discovered, the course is active.
    """
    plugins = discover_plugins()
    return {name for name, plugin in plugins.items() if not plugin.is_builtin}


class Configuration:
    """Manages user configuration for built-in courses.

    Built-in courses require explicit tracking because their entry points
    are always present in the main su_master_mind package. External courses
    are automatically detected via package installation.
    """

    def __init__(self):
        logging.info(f"Reading configuration from {self.path}")
        config = {}
        if self.path.exists():
            with self.path.open("r") as fp:
                config = json.load(fp)

        self.builtin_courses = set()
        self.courses_to_migrate = set()  # Courses that moved from built-in to external
        valid_builtin = get_builtin_course_names()
        external_courses = get_external_course_names()

        self._needs_save = False
        for course in config.get("courses", []):
            if course in valid_builtin:
                self.builtin_courses.add(course)
            elif course in external_courses:
                # External course already installed - just remove from config
                logging.info(
                    "Course '%s' is now external (already installed) - removing",
                    course,
                )
                self._needs_save = True
            elif self._is_known_external_course(course):
                # Course moved to external but not yet installed - needs migration
                # Keep in courses_to_migrate until migration succeeds
                logging.info(
                    "Course '%s' moved to external - will install su_master_mind_%s",
                    course,
                    course,
                )
                self.courses_to_migrate.add(course)
            else:
                logging.warning("Course '%s' does not exist - removing", course)
                self._needs_save = True

        # Only auto-save for courses that are gone (not for pending migrations)
        if self._needs_save:
            self.save()

    def _is_known_external_course(self, course: str) -> bool:
        """Check if a course name corresponds to a known external package.

        Uses naming convention: external courses have package su_master_mind_<course>.
        """
        # Known external courses (courses that have been migrated from built-in)
        known_external = {"llm"}
        return course in known_external

    def save(self):
        """Save configuration to disk."""
        self.path.parent.mkdir(exist_ok=True, parents=True)
        s = json.dumps({"courses": list(self.builtin_courses)})
        self.path.write_text(s)
        logging.info("Wrote configuration in %s", self.path)

    @cached_property
    def path(self) -> Path:
        return Path(user_config_dir("master-mind", "isir")) / "config.json"

    def get_active_courses(self) -> set:
        """Get all active courses (built-in from config + all external).

        Returns:
            Set of course names that are currently active.
        """
        # External courses are active if their plugin is discovered
        external = get_external_course_names()
        # Built-in courses are active if in config
        return self.builtin_courses | external

    def add_builtin_course(self, course: str) -> bool:
        """Add a built-in course to the configuration.

        Args:
            course: Course name to add

        Returns:
            True if course was added, False if not a valid built-in course.
        """
        if course in get_builtin_course_names():
            self.builtin_courses.add(course)
            return True
        return False

    def remove_builtin_course(self, course: str) -> bool:
        """Remove a built-in course from the configuration.

        Args:
            course: Course name to remove

        Returns:
            True if course was removed, False if not in config.
        """
        if course in self.builtin_courses:
            self.builtin_courses.remove(course)
            return True
        return False

    def get_migration_packages(self) -> list:
        """Get list of packages to install for migrating courses.

        Returns:
            List of package names (e.g., ['su_master_mind_llm'])
        """
        return [f"su_master_mind_{course}" for course in self.courses_to_migrate]

    def clear_migration(self):
        """Clear the migration list after packages have been installed."""
        self.courses_to_migrate.clear()
