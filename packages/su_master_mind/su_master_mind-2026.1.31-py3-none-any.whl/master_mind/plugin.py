"""Plugin interface for master-mind course plugins.

This module defines the base classes that course plugins must implement
to be discovered and integrated into the master-mind CLI.
"""

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Dict, List, Optional

import click

# Environment variable for local cache path
_CACHE_ENV_VAR = "MASTER_MIND_DATA_PATH"


def _get_save_path(
    provider: str, resource_type: str, resource_id: str, name: str = None
) -> Optional[Path]:
    """Get the save path for a resource in the local cache.

    Args:
        provider: Provider name (e.g., "huggingface")
        resource_type: Resource type (e.g., "datasets" or "models")
        resource_id: Resource identifier (e.g., "distilbert-base-uncased")
        name: Optional configuration name (e.g., "sst2" for glue dataset)

    Returns:
        Path where the resource should be saved, or None if env var is not set
    """
    base_path = os.environ.get(_CACHE_ENV_VAR)
    if not base_path:
        return None

    safe_id = resource_id.replace("/", "-")
    if name:
        safe_id = f"{safe_id}-{name}"

    return Path(base_path) / provider / resource_type / safe_id


def _make_readonly(path: Path):
    """Make a directory tree read-only."""
    for root, dirs, files in os.walk(path):
        for d in dirs:
            os.chmod(os.path.join(root, d), 0o555)
        for f in files:
            os.chmod(os.path.join(root, f), 0o444)
    os.chmod(path, 0o555)


# Marker file to indicate successful download
DOWNLOAD_MARKER = ".downloaded.ok"


def _is_download_complete(path: Path) -> bool:
    """Check if a download is complete by looking for the marker file."""
    return (path / DOWNLOAD_MARKER).exists()


def _mark_download_complete(path: Path):
    """Create a marker file to indicate successful download."""
    marker = path / DOWNLOAD_MARKER
    marker.touch()
    os.chmod(marker, 0o444)


class DownloadableResource(ABC):
    """A downloadable resource for a course.

    Each resource represents a dataset, model, or other downloadable artifact
    that can be individually downloaded or listed.

    Subclasses must implement `resource_type` and `key` properties to enable
    hash-based duplicate detection. Two resources are considered equal if they
    have the same (resource_type, key) tuple.
    """

    @property
    @abstractmethod
    def resource_type(self) -> str:
        """Return a unique type identifier for this kind of resource.

        This is used together with `key` to compute hash and equality.
        Examples: "hf_model", "hf_dataset", "pyterrier_dataset"
        """
        pass

    @property
    @abstractmethod
    def key(self) -> str:
        """Return a unique identifier for this resource within its type."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Return a short description of this resource."""
        pass

    @property
    def optional(self) -> bool:
        """Return True if this resource is optional (not downloaded by default)."""
        return False

    @abstractmethod
    def download(self) -> str:
        """Download the resource.

        Returns:
            A short description of what was downloaded.
        """
        pass

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DownloadableResource):
            return NotImplemented
        return (self.resource_type, self.key) == (other.resource_type, other.key)

    def __hash__(self) -> int:
        return hash((self.resource_type, self.key))


class FunctionalResource(DownloadableResource):
    """A downloadable resource defined by a function.

    Convenience class for creating resources from simple functions.
    """

    def __init__(
        self,
        resource_type: str,
        key: str,
        description: str,
        download_fn: Callable[[], str],
        optional: bool = False,
    ) -> None:
        self._resource_type = resource_type
        self._key = key
        self._description = description
        self._download_fn = download_fn
        self._optional = optional

    @property
    def resource_type(self) -> str:
        return self._resource_type

    @property
    def key(self) -> str:
        return self._key

    @property
    def description(self) -> str:
        return self._description

    @property
    def optional(self) -> bool:
        return self._optional

    def download(self) -> str:
        return self._download_fn()


def make_pyterrier_dataset_resource(
    dataset_id: str, description: str, optional: bool = False
) -> DownloadableResource:
    """Create a downloadable resource for a PyTerrier/ir-datasets dataset.

    Args:
        dataset_id: The PyTerrier dataset identifier (e.g., "irds:lotte/technology/dev")
        description: A short description of the dataset
        optional: If True, this resource is optional (not downloaded by default)

    Returns:
        A DownloadableResource that downloads the dataset when called.
    """

    def download() -> str:
        import pyterrier as pt

        pt.get_dataset(dataset_id)
        return f"Downloaded {dataset_id}"

    return FunctionalResource(
        resource_type="pyterrier_dataset",
        key=dataset_id,
        description=description,
        download_fn=download,
        optional=optional,
    )


class CoursePlugin(ABC):
    """Base class for course plugins.

    Each course plugin must implement this interface to be discovered
    and integrated into the master-mind CLI.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the course identifier (e.g., 'llm', 'rl', 'deepl').

        This must match the entry point name.
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Return a human-readable description of the course."""
        pass

    @property
    def package_name(self) -> str:
        """Return the package name for installation.

        Default implementation returns 'su_master_mind' with course as extra.
        Plugin packages should override this to return their own package name.
        """
        return "su_master_mind"

    @property
    def package_extra(self) -> Optional[str]:
        """Return the extra name for pip install, if using extras.

        For built-in courses: returns course name (e.g., 'rl')
        For external plugins: returns None (they are standalone packages)
        """
        return self.name

    @property
    def is_builtin(self) -> bool:
        """Return True if this is a built-in course (uses extras on su_master_mind).

        Built-in courses require config file tracking since their entry points
        are always present. External courses are detected by package installation.
        """
        return self.package_extra is not None

    def get_cli_group(self) -> Optional[click.Group]:
        """Return a Click command group for course-specific commands.

        Returns None if no additional CLI commands are provided.
        Example: RL course provides 'master-mind rl stk-race'
        """
        return None

    def download_datasets(self) -> None:
        """Download datasets required for this course.

        Called when user runs 'master-mind download-datasets'.
        Default implementation does nothing.

        Note: New plugins should implement get_downloadable_resources() instead.
        This method is kept for backward compatibility.
        """
        pass

    def get_downloadable_resources(self) -> Dict[str, List[DownloadableResource]]:
        """Return downloadable resources organized by lecture/section.

        Returns:
            A dict mapping lecture/section names to lists of DownloadableResource.
            Return an empty dict to fall back to download_datasets() behavior.

        Example:
            {
                "lecture1": [resource1, resource2],
                "lecture2": [resource3],
            }
        """
        return {}

    def pre_install_check(self) -> bool:
        """Run pre-flight checks before installing course dependencies.

        Returns True if all checks pass, False otherwise.
        Should log appropriate error messages if checks fail.
        Default implementation returns True (no checks).
        """
        return True


class BuiltinCoursePlugin(CoursePlugin):
    """Base class for built-in courses that use extras on su_master_mind."""

    @property
    def package_name(self) -> str:
        return "su_master_mind"

    @property
    def package_extra(self) -> Optional[str]:
        return self.name


class ExternalCoursePlugin(CoursePlugin):
    """Base class for external course plugins that are separate packages."""

    @property
    def package_extra(self) -> Optional[str]:
        return None

    @property
    @abstractmethod
    def package_name(self) -> str:
        """External plugins must specify their package name."""
        pass
