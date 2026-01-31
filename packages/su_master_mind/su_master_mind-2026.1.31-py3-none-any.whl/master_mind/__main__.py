from typing import List
import click
import sys
import logging
import shutil
import subprocess

from .configuration import Configuration, get_builtin_course_names
from .utils import check_last_mastermind, check_last
from .discovery import (
    clear_plugin_cache,
    discover_plugins,
    get_all_course_names,
    get_failed_plugins,
)
from .plugin import CoursePlugin, DownloadableResource

logging.basicConfig(level=logging.INFO)

original_args = [arg for arg in sys.argv]


def is_using_uv():
    """Check if uv is available."""
    return shutil.which("uv") is not None


def get_pip_command():
    """Detect and return the appropriate pip command."""
    if is_using_uv():
        return ["uv", "pip"]
    return [sys.executable, "-m", "pip"]


def is_editable_install(package: str = "su_master_mind") -> bool:
    """Check if a package is installed in editable/development mode."""
    try:
        from importlib.metadata import distribution

        dist = distribution(package)
        # Check for editable install indicators
        # Method 1: Check if direct_url.json indicates editable
        if dist.read_text("direct_url.json"):
            import json

            direct_url = json.loads(dist.read_text("direct_url.json"))
            if direct_url.get("dir_info", {}).get("editable", False):
                return True
        return False
    except Exception:
        return False


def get_course_names() -> List[str]:
    """Get list of valid course names for CLI choices."""
    return get_all_course_names()


class CourseChoice(click.Choice):
    """Custom Choice that loads courses dynamically."""

    def __init__(self):
        # Initialize with empty list, will be populated on first use
        super().__init__([])

    @property
    def choices(self):
        return get_course_names()

    @choices.setter
    def choices(self, value):
        pass  # Ignore setting, we always use dynamic values


def migrate_courses_if_needed(configuration: Configuration):
    """Check for and handle migration of courses from built-in to external.

    This handles the case where a user had a course (e.g., 'llm') configured
    when it was built-in, but the course has since moved to an external package.

    The course remains in config until migration succeeds, ensuring no data loss
    if installation fails.
    """
    packages = configuration.get_migration_packages()

    if not packages:
        return

    logging.info("Migrating courses to external packages: %s", ", ".join(packages))

    pip_cmd = get_pip_command() + ["install"]
    cmd = pip_cmd + packages
    logging.info(f"Running: {' '.join(cmd)}")

    try:
        subprocess.check_call(cmd)
        # Migration succeeded - now remove from config and save
        configuration.clear_migration()
        configuration.save()
        clear_plugin_cache()
        print("Migration completed successfully")  # noqa: T201
    except subprocess.CalledProcessError as e:
        logging.error(f"Migration failed: {e}")
        logging.error("Course remains in config - will retry on next run")
        logging.error(
            "You can manually install with: pip install %s", " ".join(packages)
        )


@click.group()
@click.pass_context
def main(ctx):
    """Master-mind CLI for managing course dependencies and datasets."""
    ctx.ensure_object(dict)
    # Load configuration once and store in context
    ctx.obj["config"] = Configuration()
    # Handle migration of courses from built-in to external packages
    migrate_courses_if_needed(ctx.obj["config"])


@main.group()
def courses():
    """Permet de gerer la liste des cours suivis"""
    pass


@click.argument("courses", nargs=-1)
@courses.command("add")
@click.pass_context
def courses_add(ctx, courses: List[str]):
    """Ajout de cours

    For built-in courses: adds to config and installs dependencies.
    For external courses: installs the course package.
    """
    if not courses:
        print("No courses specified")  # noqa: T201
        return

    configuration = ctx.obj["config"]
    builtin_names = get_builtin_course_names()
    packages_to_install = []

    for course in courses:
        if course in builtin_names:
            # Built-in course: add to config
            configuration.add_builtin_course(course)
            packages_to_install.append(f"su_master_mind[{course}]")
            print(f"Added built-in course: {course}")  # noqa: T201
        else:
            # External course: install the package
            package_name = f"su_master_mind_{course}"
            packages_to_install.append(package_name)
            print(f"Installing external course package: {package_name}")  # noqa: T201

    configuration.save()

    # Install packages
    if packages_to_install:
        pip_cmd = get_pip_command() + ["install"]
        cmd = pip_cmd + packages_to_install
        logging.info(f"Running: {' '.join(cmd)}")
        try:
            subprocess.check_call(cmd)
            # Clear plugin cache so new plugins are discovered
            clear_plugin_cache()
        except subprocess.CalledProcessError as e:
            logging.error(f"Installation failed: {e}")
            sys.exit(1)

    print(  # noqa: T201
        "Don't forget to download the datasets with `master-mind download-datasets`"
    )


@click.argument("courses", type=CourseChoice(), nargs=-1)
@courses.command("rm")
@click.pass_context
def courses_rm(ctx, courses: List[str]):
    """Enlever un cours

    For built-in courses: removes from config (dependencies remain installed).
    For external courses: uninstalls the course package.
    """
    if not courses:
        print("No courses specified")  # noqa: T201
        return

    configuration = ctx.obj["config"]
    plugins = discover_plugins()
    packages_to_uninstall = []

    for course in courses:
        plugin = plugins.get(course)
        if plugin is None:
            logging.warning(f"Course '{course}' not found")
            continue

        if plugin.is_builtin:
            # Built-in course: remove from config
            if configuration.remove_builtin_course(course):
                print(f"Removed built-in course: {course}")  # noqa: T201
            else:
                print(f"Course '{course}' was not configured")  # noqa: T201
        else:
            # External course: uninstall the package
            packages_to_uninstall.append(plugin.package_name)
            print(f"Uninstalling external course: {plugin.package_name}")  # noqa: T201

    configuration.save()

    # Uninstall external packages
    if packages_to_uninstall:
        pip_cmd = get_pip_command() + ["uninstall", "-y"]
        cmd = pip_cmd + packages_to_uninstall
        logging.info(f"Running: {' '.join(cmd)}")
        try:
            subprocess.check_call(cmd)
            # Clear plugin cache so removed plugins are no longer discovered
            clear_plugin_cache()
        except subprocess.CalledProcessError as e:
            logging.error(f"Uninstallation failed: {e}")
            sys.exit(1)


@courses.command("list")
@click.pass_context
def courses_list(ctx):
    """Liste des cours actifs

    Shows built-in courses from config and all installed external courses.
    """
    configuration = ctx.obj["config"]
    active_courses = configuration.get_active_courses()
    plugins = discover_plugins()

    if not active_courses:
        print("No active courses")  # noqa: T201
        return

    for course in sorted(active_courses):
        plugin = plugins.get(course)
        if plugin:
            marker = "(built-in)" if plugin.is_builtin else "(external)"
            print(f"{course} {marker}: {plugin.description}")  # noqa: T201
        else:
            print(f"{course} (unknown)")  # noqa: T201


@courses.command("available")
def courses_available():
    """Liste des cours disponibles (installes)

    Shows all discovered course plugins.
    """
    plugins = discover_plugins()

    if not plugins:
        print("No course plugins discovered")  # noqa: T201
        return

    print("Built-in courses:")  # noqa: T201
    for name, plugin in sorted(plugins.items()):
        if plugin.is_builtin:
            print(f"  {name}: {plugin.description}")  # noqa: T201

    print("\nExternal courses (installed):")  # noqa: T201
    for name, plugin in sorted(plugins.items()):
        if not plugin.is_builtin:
            print(f"  {name}: {plugin.description}")  # noqa: T201


@click.option(
    "--no-self-update",
    is_flag=True,
    default=None,
    help="Skip self-update check (default if editable install)",
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Update all packages without confirmation",
)
@main.command()
@click.pass_context
def update(ctx, no_self_update: bool, yes: bool):
    """Mettre a jour l'ensemble des modules pour les cours suivis"""
    # Default --no-self-update to True if editable install
    if no_self_update is None:
        no_self_update = is_editable_install()
        if no_self_update:
            logging.info("Editable install detected, skipping self-update")

    if not no_self_update:
        check_last_mastermind(original_args)

    configuration = ctx.obj["config"]
    plugins = discover_plugins()

    # Collect packages to update
    packages_to_update = []

    # Built-in courses (extras on su_master_mind)
    builtin_extras = []
    for course in configuration.builtin_courses:
        plugin = plugins.get(course)
        if plugin and plugin.is_builtin:
            builtin_extras.append(plugin.package_extra)

    if builtin_extras:
        extras = ",".join(sorted(builtin_extras))
        packages_to_update.append(("su_master_mind", f"su_master_mind[{extras}]"))

    # External courses (separate packages)
    for name, plugin in plugins.items():
        if not plugin.is_builtin:
            packages_to_update.append((plugin.package_name, plugin.package_name))

    # Failed plugins (may be fixed by upgrading)
    failed_plugins = get_failed_plugins()
    for name, failed in failed_plugins.items():
        # Skip if already covered by builtin extras
        if name in [p.package_extra for p in plugins.values() if p.is_builtin]:
            continue
        # Skip if already in the list
        if any(pkg == failed.package_name for pkg, _ in packages_to_update):
            continue
        logging.info(
            "Plugin '%s' failed to load (%s) - will try to upgrade %s",
            name,
            failed.error,
            failed.package_name,
        )
        packages_to_update.append((failed.package_name, failed.package_name))

    if not packages_to_update:
        print("No packages to update")  # noqa: T201
        return

    pip_cmd = get_pip_command() + ["install"]
    use_uv = is_using_uv()
    updated_any = False

    for package_name, package_spec in packages_to_update:
        # Check if there's an update available
        new_version = check_last(package_name)
        if new_version is None:
            logging.info("%s is up to date", package_name)
            continue

        if not yes:
            prompt = f"Update {package_name} to {new_version}?"
            if not click.confirm(prompt, default=True):
                logging.info("Skipping %s", package_name)
                continue

        # Use --upgrade-package for uv to only upgrade the specific package
        # Use --upgrade for pip (standard behavior)
        if use_uv:
            cmd = pip_cmd + ["--upgrade-package", package_name, package_spec]
        else:
            cmd = pip_cmd + ["--upgrade", package_spec]
        logging.info("Running: %s", " ".join(cmd))

        try:
            subprocess.check_call(cmd)
            logging.info("Successfully updated %s", package_name)
            updated_any = True
        except subprocess.CalledProcessError as e:
            logging.error("Failed to update %s: %s", package_name, e)

    if not updated_any:
        print("All packages are up to date")  # noqa: T201
        return

    # Clear plugin cache to pick up any changes
    clear_plugin_cache()

    print(  # noqa: T201
        "Don't forget to download the datasets with `master-mind download-datasets`"
    )


@click.option(
    "--download",
    is_flag=True,
    help="Download all resources (default is to list)",
)
@click.option(
    "--lecture",
    help="Only process resources for a specific lecture",
)
@click.option(
    "--key",
    help="Download a specific resource by its key (implies --download)",
)
@click.option(
    "--course",
    "course_filter",
    help="Only process resources for a specific course",
)
@click.option(
    "--optional",
    "include_optional",
    is_flag=True,
    help="Include optional resources when downloading",
)
@main.command()
@click.pass_context
def download_datasets(
    ctx,
    download: bool,
    lecture: str,
    key: str,
    course_filter: str,
    include_optional: bool,
):
    """List or download datasets for enrolled courses.

    By default, lists available resources. Use --download to download all,
    or --key to download a specific resource.
    """
    import os

    from master_mind.plugin import _CACHE_ENV_VAR

    # Ensure HuggingFace Hub is online for dataset downloads
    hf_hub_offline = os.environ.pop("HF_HUB_OFFLINE", None)

    # --key implies --download
    should_download = download or key

    # Show cache location when downloading
    if should_download:
        cache_path = os.environ.get(_CACHE_ENV_VAR)
        if cache_path:
            print(f"Cache location: {cache_path}")  # noqa: T201
        else:
            logging.warning(
                "%s is not set - resources will use HuggingFace's default cache "
                "(~/.cache/huggingface). Set this variable to use a shared cache.",
                _CACHE_ENV_VAR,
            )

    try:
        configuration = ctx.obj["config"]
        active_courses = configuration.get_active_courses()
        plugins = discover_plugins()

        # Filter by course if specified
        if course_filter:
            if course_filter not in active_courses:
                logging.error("Course '%s' is not active", course_filter)
                sys.exit(1)
            active_courses = [course_filter]

        for course in active_courses:
            plugin = plugins.get(course)
            if not plugin:
                logging.warning("No plugin found for course %s", course)
                continue

            resources = plugin.get_downloadable_resources()

            # If plugin doesn't override get_downloadable_resources, fall back to legacy
            has_custom_resources = (
                type(plugin).get_downloadable_resources
                is not CoursePlugin.get_downloadable_resources
            )

            if not has_custom_resources:
                if should_download and not lecture and not key:
                    logging.info("Installing resources for %s (legacy)", course)
                    plugin.download_datasets()
                else:
                    print(  # noqa: T201
                        f"{course}: no structured resources (legacy plugin)"
                    )
                continue

            # Empty structured resources (new-style plugin with nothing to download)
            if not resources:
                print(f"{course}: no resources")  # noqa: T201
                continue

            # Filter by lecture if specified
            if lecture:
                if lecture not in resources:
                    continue
                resources = {lecture: resources[lecture]}

            # Download mode
            if should_download:
                logging.info("Installing resources for %s", course)
                downloaded: set[DownloadableResource] = set()
                for lec_name, res_list in resources.items():
                    for res in res_list:
                        if key and res.key != key:
                            continue
                        # Skip optional unless --optional or --key targets it
                        if res.optional and not include_optional and not key:
                            logging.info("Skipping %s/%s (optional)", lec_name, res.key)
                            continue
                        if res in downloaded:
                            logging.info(
                                "Skipping %s/%s (already downloaded)", lec_name, res.key
                            )
                            continue
                        downloaded.add(res)
                        logging.info(
                            "Downloading %s/%s: %s", lec_name, res.key, res.description
                        )
                        result = res.download()
                        if result:
                            logging.info("  -> %s", result)
            else:
                # List mode (default)
                print(f"\n{course}:")  # noqa: T201
                for lec_name, res_list in sorted(resources.items()):
                    print(f"  {lec_name}:")  # noqa: T201
                    for res in res_list:
                        optional_marker = " (optional)" if res.optional else ""
                        print(  # noqa: T201
                            f"    - {res.key}: {res.description}{optional_marker}"
                        )

    finally:
        # Restore original HF_HUB_OFFLINE setting
        if hf_hub_offline is not None:
            os.environ["HF_HUB_OFFLINE"] = hf_hub_offline


def register_plugin_commands():
    """Register CLI command groups from all plugins."""
    plugins = discover_plugins()
    for name, plugin in plugins.items():
        cli_group = plugin.get_cli_group()
        if cli_group is not None:
            main.add_command(cli_group, name=name)


# Register plugin commands after main group is defined
register_plugin_commands()
