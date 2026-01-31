"""Package installation for master-mind courses.

This module handles installing course dependencies, supporting both
built-in courses (extras on su_master_mind) and external course packages.
"""

import logging
import shutil
import subprocess
import sys

from .discovery import discover_plugins


def is_using_uv():
    """Check if uv is available."""
    return shutil.which("uv") is not None


def get_pip_command():
    """Detect and return the appropriate pip command (uv or pip)."""
    if is_using_uv():
        return ["uv", "pip", "install"]
    return [sys.executable, "-m", "pip", "install"]


def install_courses(courses):
    """Install packages for the specified courses.

    Uses the plugin interface for pre-flight checks and to determine
    installation method (extras vs separate packages).

    Args:
        courses: List of course names to install (e.g., ['rl', 'deepl', 'llm'])
    """
    if not courses:
        logging.info("No courses to install")
        return

    plugins = discover_plugins()
    unique_courses = sorted(set(courses))

    # Run pre-flight checks for all courses
    for course in unique_courses:
        plugin = plugins.get(course)
        if plugin and not plugin.pre_install_check():
            sys.exit(1)

    # Group courses by installation type:
    # - Built-in courses: use extras on su_master_mind
    # - External plugins: install as separate packages
    builtin_extras = []
    external_packages = []

    for course in unique_courses:
        plugin = plugins.get(course)
        if plugin is None:
            # Course not installed yet - assume external package naming convention
            external_packages.append(f"su_master_mind_{course}")
            continue

        if plugin.is_builtin:
            # Built-in course using extras
            builtin_extras.append(plugin.package_extra)
        else:
            # External package - upgrade it
            external_packages.append(plugin.package_name)

    pip_cmd = get_pip_command()

    # Install built-in courses with extras (single command for efficiency)
    if builtin_extras:
        extras = ",".join(builtin_extras)
        package_spec = f"su_master_mind[{extras}]"
        cmd = pip_cmd + [package_spec]
        logging.info(f"Installing built-in courses: {' '.join(cmd)}")

        try:
            subprocess.check_call(cmd)
            logging.info(f"Successfully installed {package_spec}")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to install {package_spec}: {e}")
            sys.exit(1)

    # Install/upgrade external packages
    # Use --upgrade-package for uv to only upgrade the specific package
    use_uv = is_using_uv()
    for pkg in external_packages:
        if use_uv:
            cmd = pip_cmd + ["--upgrade-package", pkg, pkg]
        else:
            cmd = pip_cmd + ["--upgrade", pkg]
        logging.info(f"Installing external course: {' '.join(cmd)}")

        try:
            subprocess.check_call(cmd)
            logging.info(f"Successfully installed {pkg}")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to install {pkg}: {e}")
            sys.exit(1)
