"""Tests for the HuggingFace loading utilities."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from master_mind.teaching.hf import (
    _get_cache_path,
    _get_hf_cache_dir,
    _sanitize_id,
    make_hf_model_resource,
    make_hf_tokenizer_resource,
    make_hf_processor_resource,
    make_hf_dataset_resource,
    ENV_VAR,
)


class TestGetCachePath:
    """Tests for _get_cache_path function."""

    def test_returns_none_when_env_not_set(self):
        """Test that None is returned when env var is not set."""
        with patch.dict(os.environ, {}, clear=True):
            assert _get_cache_path() is None

    def test_returns_path_when_env_set(self):
        """Test that Path is returned when env var is set."""
        with patch.dict(os.environ, {ENV_VAR: "/some/path"}):
            result = _get_cache_path()
            assert result == Path("/some/path")


class TestGetHfCacheDir:
    """Tests for _get_hf_cache_dir function."""

    def test_returns_none_when_env_not_set(self):
        """Test that None is returned when env var is not set."""
        with patch.dict(os.environ, {}, clear=True):
            assert _get_hf_cache_dir() is None

    def test_returns_huggingface_subdir(self, tmp_path):
        """Test that huggingface subdirectory is returned."""
        with patch.dict(os.environ, {ENV_VAR: str(tmp_path)}):
            result = _get_hf_cache_dir()
            expected = tmp_path / "huggingface"
            assert result == str(expected)
            assert expected.exists()


class TestSanitizeId:
    """Tests for _sanitize_id function."""

    def test_replaces_slash_with_dash(self):
        """Test that / is replaced with -."""
        assert _sanitize_id("org/model") == "org-model"

    def test_handles_multiple_slashes(self):
        """Test handling of multiple slashes."""
        assert _sanitize_id("org/sub/model") == "org-sub-model"

    def test_no_change_without_slash(self):
        """Test that IDs without slash are unchanged."""
        assert _sanitize_id("model-name") == "model-name"


# Parametrize data for transformers resource tests
TRANSFORMERS_RESOURCES = [
    (make_hf_model_resource, "model", "AutoModel"),
    (make_hf_tokenizer_resource, "tokenizer", "AutoTokenizer"),
    (make_hf_processor_resource, "processor", "AutoProcessor"),
]


@pytest.mark.parametrize("make_fn,resource_type,default_class", TRANSFORMERS_RESOURCES)
class TestMakeHfTransformersResources:
    """Tests for make_hf_model/tokenizer/processor_resource functions."""

    def test_creates_resource_with_correct_key(
        self, make_fn, resource_type, default_class
    ):
        """Test that resource has correct key."""
        resource = make_fn("bert-base-uncased")
        assert resource.key == "bert-base-uncased"

    def test_creates_resource_with_default_description(
        self, make_fn, resource_type, default_class
    ):
        """Test that resource has auto-generated description when not provided."""
        resource = make_fn("bert-base-uncased")
        assert resource.description == f"HuggingFace {resource_type}: bert-base-uncased"

    def test_creates_resource_with_custom_description(
        self, make_fn, resource_type, default_class
    ):
        """Test that resource uses provided description."""
        resource = make_fn("bert-base-uncased", "Custom description")
        assert resource.description == "Custom description"

    def test_optional_flag(self, make_fn, resource_type, default_class):
        """Test that optional flag is set correctly."""
        resource = make_fn("bert-base-uncased", optional=True)
        assert resource.optional is True

    def test_download_uses_local_cache_when_complete(
        self, make_fn, resource_type, default_class, tmp_path
    ):
        """Test that download uses local cache when download is complete."""
        model_path = tmp_path / "huggingface" / "models" / "bert-base-uncased"
        model_path.mkdir(parents=True)
        (model_path / ".downloaded.ok").touch()

        mock_transformers = MagicMock()

        with patch.dict(os.environ, {ENV_VAR: str(tmp_path)}):
            with patch.dict("sys.modules", {"transformers": mock_transformers}):
                resource = make_fn("bert-base-uncased")
                result = resource.download()
                assert "Already exists" in result
                getattr(
                    mock_transformers, default_class
                ).from_pretrained.assert_not_called()

    def test_download_falls_back_to_hf_when_no_cache_path(
        self, make_fn, resource_type, default_class
    ):
        """Test that download falls back to HF when no cache path."""
        mock_class = MagicMock()
        mock_transformers = MagicMock()
        setattr(mock_transformers, default_class, mock_class)

        with patch.dict(os.environ, {}, clear=True):
            with patch.dict("sys.modules", {"transformers": mock_transformers}):
                resource = make_fn("bert-base-uncased")
                result = resource.download()
                assert "Cached" in result
                mock_class.from_pretrained.assert_called_once()


class TestMakeHfModelResourceCustomClass:
    """Test custom class parameter for make_hf_model_resource."""

    def test_model_custom_class(self):
        """Test that custom model class is used."""
        mock_causal_lm = MagicMock()
        mock_transformers = MagicMock()
        mock_transformers.AutoModelForCausalLM = mock_causal_lm

        with patch.dict(os.environ, {}, clear=True):
            with patch.dict("sys.modules", {"transformers": mock_transformers}):
                resource = make_hf_model_resource(
                    "gpt2", model_class="AutoModelForCausalLM"
                )
                resource.download()
                mock_causal_lm.from_pretrained.assert_called_once()


class TestMakeHfDatasetResource:
    """Tests for make_hf_dataset_resource function."""

    def test_creates_resource_with_correct_key_single_split(self):
        """Test that resource has correct key for single split."""
        resource = make_hf_dataset_resource("imdb", "train")
        assert resource.key == "imdb/train"

    def test_creates_resource_with_correct_key_multiple_splits(self):
        """Test that resource has correct key for multiple splits."""
        resource = make_hf_dataset_resource("imdb", ["train", "test"])
        assert resource.key == "imdb/train+test"

    def test_creates_resource_with_name_in_key(self):
        """Test that config name is included in key."""
        resource = make_hf_dataset_resource("glue", "validation", name="sst2")
        assert resource.key == "glue/sst2/validation"

    def test_creates_resource_with_correct_description(self):
        """Test that resource has correct description."""
        resource = make_hf_dataset_resource("imdb", "train", "IMDB dataset")
        assert resource.description == "IMDB dataset"

    def test_creates_resource_with_default_description(self):
        """Test that resource has auto-generated description when not provided."""
        resource = make_hf_dataset_resource("imdb", "train")
        assert resource.description == "HuggingFace dataset: imdb"

    def test_optional_flag(self):
        """Test that optional flag is set correctly."""
        resource = make_hf_dataset_resource("imdb", "train", optional=True)
        assert resource.optional is True

    def test_download_uses_local_cache_when_complete(self, tmp_path):
        """Test that download uses local cache when download is complete."""
        dataset_path = tmp_path / "huggingface" / "datasets" / "imdb" / "train"
        dataset_path.mkdir(parents=True)
        (dataset_path / ".downloaded.ok").touch()

        mock_datasets = MagicMock()

        with patch.dict(os.environ, {ENV_VAR: str(tmp_path)}):
            with patch.dict("sys.modules", {"datasets": mock_datasets}):
                resource = make_hf_dataset_resource("imdb", "train")
                result = resource.download()
                assert "already exists" in result
                # Ensure no HF calls were made
                mock_datasets.load_dataset.assert_not_called()

    def test_download_falls_back_to_hf_when_no_cache_path(self):
        """Test that download falls back to HF when no cache path."""
        mock_datasets = MagicMock()

        with patch.dict(os.environ, {}, clear=True):
            with patch.dict("sys.modules", {"datasets": mock_datasets}):
                resource = make_hf_dataset_resource("imdb", "train")
                result = resource.download()
                assert "Cached" in result
                mock_datasets.load_dataset.assert_called_once()
