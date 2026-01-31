"""Tests for the modular resource download feature."""

import pytest
from unittest.mock import MagicMock, patch
from click.testing import CliRunner

from master_mind.plugin import (
    CoursePlugin,
    FunctionalResource,
)
from master_mind.__main__ import main


class TestFunctionalResource:
    """Tests for FunctionalResource class."""

    def test_key_property(self):
        """Test that key property returns the correct value."""
        resource = FunctionalResource(
            resource_type="test_type",
            key="test-key",
            description="Test description",
            download_fn=lambda: "done",
        )
        assert resource.key == "test-key"

    def test_description_property(self):
        """Test that description property returns the correct value."""
        resource = FunctionalResource(
            resource_type="test_type",
            key="test-key",
            description="Test description",
            download_fn=lambda: "done",
        )
        assert resource.description == "Test description"

    def test_resource_type_property(self):
        """Test that resource_type property returns the correct value."""
        resource = FunctionalResource(
            resource_type="test_type",
            key="test-key",
            description="Test description",
            download_fn=lambda: "done",
        )
        assert resource.resource_type == "test_type"

    def test_download_calls_function(self):
        """Test that download() calls the provided function."""
        mock_fn = MagicMock(return_value="Download complete")
        resource = FunctionalResource(
            resource_type="test_type",
            key="test-key",
            description="Test description",
            download_fn=mock_fn,
        )

        result = resource.download()

        mock_fn.assert_called_once()
        assert result == "Download complete"


class TestCoursePluginResourceDetection:
    """Tests for detecting whether a plugin uses structured resources."""

    def test_base_plugin_has_no_custom_resources(self):
        """Test that base CoursePlugin returns empty dict."""

        class MinimalPlugin(CoursePlugin):
            @property
            def name(self) -> str:
                return "minimal"

            @property
            def description(self) -> str:
                return "Minimal plugin"

        plugin = MinimalPlugin()
        assert plugin.get_downloadable_resources() == {}

    def test_plugin_with_custom_resources(self):
        """Test plugin that overrides get_downloadable_resources."""

        class CustomPlugin(CoursePlugin):
            @property
            def name(self) -> str:
                return "custom"

            @property
            def description(self) -> str:
                return "Custom plugin"

            def get_downloadable_resources(self):
                return {
                    "lecture1": [
                        FunctionalResource("test", "res1", "Resource 1", lambda: "done")
                    ]
                }

        plugin = CustomPlugin()
        resources = plugin.get_downloadable_resources()
        assert "lecture1" in resources
        assert len(resources["lecture1"]) == 1
        assert resources["lecture1"][0].key == "res1"

    def test_method_override_detection(self):
        """Test that we can detect if get_downloadable_resources is overridden."""

        class LegacyPlugin(CoursePlugin):
            @property
            def name(self) -> str:
                return "legacy"

            @property
            def description(self) -> str:
                return "Legacy plugin"

            def download_datasets(self) -> None:
                pass

        class ModernPlugin(CoursePlugin):
            @property
            def name(self) -> str:
                return "modern"

            @property
            def description(self) -> str:
                return "Modern plugin"

            def get_downloadable_resources(self):
                return {"lecture1": []}

        legacy = LegacyPlugin()
        modern = ModernPlugin()

        # Check if method is overridden
        legacy_overrides = (
            type(legacy).get_downloadable_resources
            is not CoursePlugin.get_downloadable_resources
        )
        modern_overrides = (
            type(modern).get_downloadable_resources
            is not CoursePlugin.get_downloadable_resources
        )

        assert not legacy_overrides
        assert modern_overrides


class TestDuplicateResourceDetection:
    """Tests for duplicate resource detection using equality and hash."""

    def test_same_object_detected_as_duplicate(self):
        """Test that the same resource object in multiple lectures is detected."""
        shared_resource = FunctionalResource(
            resource_type="test",
            key="shared",
            description="Shared resource",
            download_fn=lambda: "done",
        )

        resources = {
            "lecture1": [shared_resource],
            "lecture2": [shared_resource],
        }

        # Simulate the download loop with hash-based duplicate detection
        downloaded: set = set()
        download_count = 0

        for lec_name, res_list in resources.items():
            for res in res_list:
                if res in downloaded:
                    continue
                downloaded.add(res)
                download_count += 1

        assert download_count == 1

    def test_equal_resources_detected_as_duplicate(self):
        """Test that equal resources (same type+key) are detected as duplicates."""
        resource1 = FunctionalResource(
            resource_type="test",
            key="shared",
            description="Shared resource 1",
            download_fn=lambda: "done1",
        )
        resource2 = FunctionalResource(
            resource_type="test",
            key="shared",
            description="Shared resource 2",
            download_fn=lambda: "done2",
        )

        # Different objects but equal by (resource_type, key)
        assert resource1 == resource2
        assert hash(resource1) == hash(resource2)

        resources = {
            "lecture1": [resource1],
            "lecture2": [resource2],
        }

        downloaded: set = set()
        download_count = 0

        for lec_name, res_list in resources.items():
            for res in res_list:
                if res in downloaded:
                    continue
                downloaded.add(res)
                download_count += 1

        assert download_count == 1

    def test_different_keys_not_duplicate(self):
        """Test that resources with different keys are not duplicates."""
        resource1 = FunctionalResource(
            resource_type="test",
            key="res1",
            description="Resource 1",
            download_fn=lambda: "done",
        )
        resource2 = FunctionalResource(
            resource_type="test",
            key="res2",
            description="Resource 2",
            download_fn=lambda: "done",
        )

        assert resource1 != resource2

        resources = {
            "lecture1": [resource1],
            "lecture2": [resource2],
        }

        downloaded: set = set()
        download_count = 0

        for lec_name, res_list in resources.items():
            for res in res_list:
                if res in downloaded:
                    continue
                downloaded.add(res)
                download_count += 1

        assert download_count == 2

    def test_different_types_not_duplicate(self):
        """Test that resources with different types but same key are not duplicates."""
        resource1 = FunctionalResource(
            resource_type="hf_model",
            key="bert-base",
            description="Model",
            download_fn=lambda: "done",
        )
        resource2 = FunctionalResource(
            resource_type="hf_dataset",
            key="bert-base",
            description="Dataset",
            download_fn=lambda: "done",
        )

        assert resource1 != resource2

        resources = {
            "lecture1": [resource1],
            "lecture2": [resource2],
        }

        downloaded: set = set()
        download_count = 0

        for lec_name, res_list in resources.items():
            for res in res_list:
                if res in downloaded:
                    continue
                downloaded.add(res)
                download_count += 1

        assert download_count == 2


class MockPlugin(CoursePlugin):
    """Mock plugin for CLI testing."""

    def __init__(self, name: str, resources: dict):
        self._name = name
        self._resources = resources

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return f"{self._name} plugin"

    def get_downloadable_resources(self):
        return self._resources


class TestDownloadDatasetsCommand:
    """Tests for the download-datasets CLI command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration."""
        config = MagicMock()
        config.get_active_courses.return_value = []
        config.builtin_courses = []
        config.get_migration_packages.return_value = []
        return config

    @pytest.fixture
    def mock_resources(self):
        """Create mock resources for testing."""
        return {
            "lecture1": [
                FunctionalResource(
                    "test", "dataset1", "First dataset", lambda: "Downloaded 1"
                ),
                FunctionalResource(
                    "test", "model1", "First model", lambda: "Downloaded model"
                ),
            ],
            "lecture2": [
                FunctionalResource(
                    "test", "dataset2", "Second dataset", lambda: "Downloaded 2"
                ),
            ],
        }

    def test_list_resources_default(self, runner, mock_config, mock_resources):
        """Test that listing is the default behavior."""
        mock_plugin = MockPlugin("testcourse", mock_resources)
        mock_config.get_active_courses.return_value = ["testcourse"]

        with patch("master_mind.__main__.Configuration", return_value=mock_config):
            with patch(
                "master_mind.__main__.discover_plugins",
                return_value={"testcourse": mock_plugin},
            ):
                with patch("master_mind.__main__.migrate_courses_if_needed"):
                    result = runner.invoke(main, ["download-datasets"])

                    assert result.exit_code == 0, f"Error: {result.output}"
                    assert "testcourse:" in result.output
                    assert "lecture1:" in result.output
                    assert "dataset1:" in result.output
                    assert "First dataset" in result.output
                    assert "lecture2:" in result.output
                    assert "dataset2:" in result.output

    def test_filter_by_lecture_download(self, runner, mock_config):
        """Test --lecture with --download filters and downloads resources."""
        download_calls = []

        def track_download(name):
            def fn():
                download_calls.append(name)
                return f"Downloaded {name}"

            return fn

        resources = {
            "lecture1": [
                FunctionalResource("test", "d1", "Dataset 1", track_download("d1")),
            ],
            "lecture2": [
                FunctionalResource("test", "d2", "Dataset 2", track_download("d2")),
            ],
        }
        mock_plugin = MockPlugin("testcourse", resources)
        mock_config.get_active_courses.return_value = ["testcourse"]

        with patch("master_mind.__main__.Configuration", return_value=mock_config):
            with patch(
                "master_mind.__main__.discover_plugins",
                return_value={"testcourse": mock_plugin},
            ):
                with patch("master_mind.__main__.migrate_courses_if_needed"):
                    result = runner.invoke(
                        main,
                        ["download-datasets", "--lecture", "lecture1", "--download"],
                    )

                    assert result.exit_code == 0, f"Error: {result.output}"
                    assert "d1" in download_calls
                    assert "d2" not in download_calls

    def test_filter_by_key(self, runner, mock_config):
        """Test --key option downloads specific resource."""
        download_calls = []

        def track_download(name):
            def fn():
                download_calls.append(name)
                return f"Downloaded {name}"

            return fn

        resources = {
            "lecture1": [
                FunctionalResource("test", "d1", "Dataset 1", track_download("d1")),
                FunctionalResource("test", "d2", "Dataset 2", track_download("d2")),
            ],
        }
        mock_plugin = MockPlugin("testcourse", resources)
        mock_config.get_active_courses.return_value = ["testcourse"]

        with patch("master_mind.__main__.Configuration", return_value=mock_config):
            with patch(
                "master_mind.__main__.discover_plugins",
                return_value={"testcourse": mock_plugin},
            ):
                with patch("master_mind.__main__.migrate_courses_if_needed"):
                    result = runner.invoke(main, ["download-datasets", "--key", "d1"])

                    assert result.exit_code == 0, f"Error: {result.output}"
                    assert download_calls == ["d1"]

    def test_filter_by_course(self, runner, mock_config):
        """Test --course option filters by course."""
        plugin1 = MockPlugin(
            "course1",
            {"lec": [FunctionalResource("test", "r1", "Res 1", lambda: "done")]},
        )
        plugin2 = MockPlugin(
            "course2",
            {"lec": [FunctionalResource("test", "r2", "Res 2", lambda: "done")]},
        )
        mock_config.get_active_courses.return_value = ["course1", "course2"]

        with patch("master_mind.__main__.Configuration", return_value=mock_config):
            with patch(
                "master_mind.__main__.discover_plugins",
                return_value={"course1": plugin1, "course2": plugin2},
            ):
                with patch("master_mind.__main__.migrate_courses_if_needed"):
                    result = runner.invoke(
                        main, ["download-datasets", "--course", "course1"]
                    )

                    assert result.exit_code == 0, f"Error: {result.output}"
                    assert "course1:" in result.output
                    assert "r1:" in result.output
                    assert "course2:" not in result.output

    def test_duplicate_resources_downloaded_once(self, runner, mock_config):
        """Test that shared resources are only downloaded once."""
        download_count = {"count": 0}

        def counting_download():
            download_count["count"] += 1
            return "Downloaded"

        shared_resource = FunctionalResource(
            "test", "shared", "Shared resource", counting_download
        )

        resources = {
            "lecture1": [shared_resource],
            "lecture2": [shared_resource],
        }
        mock_plugin = MockPlugin("testcourse", resources)
        mock_config.get_active_courses.return_value = ["testcourse"]

        with patch("master_mind.__main__.Configuration", return_value=mock_config):
            with patch(
                "master_mind.__main__.discover_plugins",
                return_value={"testcourse": mock_plugin},
            ):
                with patch("master_mind.__main__.migrate_courses_if_needed"):
                    result = runner.invoke(main, ["download-datasets", "--download"])

                    assert result.exit_code == 0, f"Error: {result.output}"
                    assert download_count["count"] == 1

    def test_legacy_plugin_fallback(self, runner, mock_config):
        """Test that legacy plugins fall back to download_datasets()."""

        class LegacyPlugin(CoursePlugin):
            download_called = False

            @property
            def name(self) -> str:
                return "legacy"

            @property
            def description(self) -> str:
                return "Legacy plugin"

            def download_datasets(self) -> None:
                LegacyPlugin.download_called = True

        plugin = LegacyPlugin()
        mock_config.get_active_courses.return_value = ["legacy"]

        with patch("master_mind.__main__.Configuration", return_value=mock_config):
            with patch(
                "master_mind.__main__.discover_plugins",
                return_value={"legacy": plugin},
            ):
                with patch("master_mind.__main__.migrate_courses_if_needed"):
                    result = runner.invoke(main, ["download-datasets", "--download"])

                    assert result.exit_code == 0, f"Error: {result.output}"
                    assert LegacyPlugin.download_called
