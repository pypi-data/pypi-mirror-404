"""HuggingFace loading utilities with local cache support.

This module provides functions to load HuggingFace datasets and models,
first checking a local cache directory (for unreliable HF caching environments)
and falling back to HuggingFace Hub with a warning.

Loading Functions (for use in notebooks):
    from master_mind.teaching.hf import (
        load_hf_dataset, load_hf_model, load_hf_tokenizer, load_hf_processor, HFModel
    )

    # Direct loading
    tokenizer = load_hf_tokenizer("gpt2")
    model = load_hf_model("gpt2", GPT2LMHeadModel)
    dataset = load_hf_dataset("imdb", split="train")

    # Lazy loading with HFModel (cleaner for multiple models)
    hf_model = HFModel("gpt2")  # Uses AutoTokenizer/AutoModel
    tokenizer = hf_model.tokenizer  # Loads on first access
    model = hf_model.model          # Loads on first access

Resource Functions (for course plugins):
    from master_mind.teaching.hf import (
        make_hf_model_resource, make_hf_tokenizer_resource,
        make_hf_processor_resource, make_hf_dataset_resource
    )

    # Create downloadable resources for pre-caching
    resources = [
        make_hf_model_resource("gpt2", model_class="AutoModelForCausalLM"),
        make_hf_tokenizer_resource("gpt2"),
        make_hf_dataset_resource("imdb", ["train", "test"]),
    ]

Environment Variables:
    MASTER_MIND_DATA_PATH: Path to the shared local cache directory.
        If not set, falls back directly to HuggingFace Hub.
    MASTER_MIND_DATA_ENFORCE: If set (to any value), raises an error when
        a resource is not found in the local cache instead of falling back
        to HuggingFace Hub. Useful for verifying that all resources are cached.
"""

import logging
import os
from pathlib import Path
from typing import Any, List, Optional, Type

from master_mind.plugin import (
    DownloadableResource,
    FunctionalResource,
    _get_save_path,
    _is_download_complete,
    _mark_download_complete,
)

logger = logging.getLogger(__name__)

# Constants
ENV_VAR = "MASTER_MIND_DATA_PATH"
ENV_VAR_ENFORCE = "MASTER_MIND_DATA_ENFORCE"


class CacheMissError(Exception):
    """Raised when MASTER_MIND_DATA_ENFORCE is set and a resource is not in cache."""

    pass


def _is_enforce_mode() -> bool:
    """Check if cache enforcement mode is enabled."""
    return os.environ.get(ENV_VAR_ENFORCE) is not None


class HFModel:
    """Wrapper for HuggingFace models with lazy loading via cached properties.

    This class provides a cleaner alternative to lambda tuples for model loading.
    Models and tokenizers are loaded only when first accessed and cached for reuse.

    Example:
        >>> # Simple usage with AutoTokenizer/AutoModel
        >>> hf_model = HFModel("gpt2")
        >>> tokenizer = hf_model.tokenizer  # Loads once, cached
        >>> model = hf_model.model          # Loads once, cached
        >>>
        >>> # With explicit classes
        >>> from transformers import GPT2Tokenizer, GPT2LMHeadModel
        >>> hf_model = HFModel("gpt2", GPT2Tokenizer, GPT2LMHeadModel)
        >>> model.to(device)
    """

    def __init__(
        self,
        model_id: str,
        tokenizer_cls: Optional[Type] = None,
        model_cls: Optional[Type] = None,
    ):
        """Initialize model wrapper.

        Args:
            model_id: HuggingFace model ID
                (e.g., "gpt2", "HuggingFaceTB/SmolLM2-1.7B-Instruct")
            tokenizer_cls: Tokenizer class (e.g., GPT2Tokenizer, AutoTokenizer).
                If None, uses AutoTokenizer.
            model_cls: Model class (e.g., GPT2LMHeadModel, AutoModelForCausalLM).
                If None, uses AutoModel.
        """
        self.model_id = model_id
        self.tokenizer_cls = tokenizer_cls
        self.model_cls = model_cls

    @property
    def tokenizer(self):
        """Load tokenizer (cached after first access)."""
        if not hasattr(self, "_tokenizer"):
            self._tokenizer = load_hf_tokenizer(self.model_id, self.tokenizer_cls)
        return self._tokenizer

    @property
    def model(self):
        """Load model (cached after first access)."""
        if not hasattr(self, "_model"):
            self._model = load_hf_model(self.model_id, self.model_cls)
        return self._model


def _log_loaded(resource_type: str, resource_id: str, source: str):
    """Log that a resource was loaded, adapting to notebook or terminal environment."""
    message = f"Loaded {resource_type} '{resource_id}' from {source}"
    logger.info(message)

    # In notebooks, also display as gray HTML
    try:
        from IPython.display import HTML, display
        from IPython import get_ipython

        if get_ipython() is not None:
            html = f'<span style="color: #666; font-size: 0.9em;">ℹ️ {message}</span>'
            display(HTML(html))
    except (ImportError, AttributeError):
        # Not in a notebook, logging is sufficient
        pass


def _get_cache_path() -> Optional[Path]:
    """Get the local cache path from environment variable."""
    path = os.environ.get(ENV_VAR)
    if path:
        return Path(path)
    return None


def _get_hf_cache_dir() -> Optional[str]:
    """Get HuggingFace cache directory within MASTER_MIND_DATA_PATH."""
    base_path = os.environ.get(ENV_VAR)
    if not base_path:
        return None
    cache_dir = Path(base_path) / "huggingface"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return str(cache_dir)


def _sanitize_id(hf_id: str) -> str:
    """Convert HuggingFace ID to filesystem-safe directory name.

    Replaces "/" with "-" to create valid directory names.
    """
    return hf_id.replace("/", "-")


def _warn_cache_miss(resource_type: str, resource_id: str, cache_path: Optional[Path]):
    """Warn if cache was configured but resource not found.

    Raises:
        CacheMissError: If MASTER_MIND_DATA_ENFORCE is set and cache_path is configured.
    """
    if cache_path:
        # User expected local cache but it wasn't there
        message = (
            f"{resource_type} '{resource_id}' not found in local cache at {cache_path}"
        )
        if _is_enforce_mode():
            raise CacheMissError(message)
        logger.warning(message)
    else:
        logger.debug(
            f"{resource_type} '{resource_id}': no local cache configured, "
            f"set {ENV_VAR} to enable"
        )


def load_hf_dataset(
    dataset_id: str,
    name: Optional[str] = None,
    split: Optional[str] = None,
    **kwargs,
) -> Any:
    """Load a HuggingFace dataset, checking local cache first.

    Args:
        dataset_id: HuggingFace dataset identifier (e.g., "imdb", "jxie/flickr8k")
        name: Dataset configuration name (e.g., "sst2" for glue)
        split: Specific split to load (e.g., "train", "validation")
        **kwargs: Additional arguments passed to load_dataset/load_from_disk

    Returns:
        Dataset or DatasetDict depending on whether split is specified

    Example:
        >>> dataset = load_hf_dataset("imdb", split="train")
        >>> flickr = load_hf_dataset("jxie/flickr8k")  # returns DatasetDict
        >>> sst2 = load_hf_dataset("glue", name="sst2", split="validation")
    """
    from datasets import DatasetDict, load_dataset, load_from_disk

    cache_path = _get_cache_path()

    if cache_path:
        # Build local path: huggingface/datasets/<sanitized-id>[-<name>]/[<split>/]
        safe_id = _sanitize_id(dataset_id)
        if name:
            safe_id = f"{safe_id}-{name}"
        local_base = cache_path / "huggingface" / "datasets" / safe_id

        if local_base.exists():
            if split:
                # Load specific split
                split_path = local_base / split
                if _is_download_complete(split_path):
                    result = load_from_disk(str(split_path))
                    _log_loaded("dataset", dataset_id, "local cache")
                    return result
            else:
                # Load all splits as DatasetDict
                splits = {}
                for p in sorted(local_base.iterdir()):
                    if p.is_dir() and _is_download_complete(p):
                        splits[p.name] = load_from_disk(str(p))
                if splits:
                    _log_loaded("dataset", dataset_id, "local cache")
                    return DatasetDict(splits)

    # Fall back to HuggingFace Hub
    _warn_cache_miss("Dataset", dataset_id, cache_path)
    result = load_dataset(dataset_id, name, split=split, **kwargs)
    _log_loaded("dataset", dataset_id, "HuggingFace Hub")
    return result


def load_hf_model(
    model_id: str,
    model_class: Optional[Type] = None,
    **kwargs,
) -> Any:
    """Load a HuggingFace model, checking local cache first.

    Args:
        model_id: HuggingFace model identifier (e.g., "distilbert-base-uncased")
        model_class: Optional model class to use. If None, uses AutoModel.
        **kwargs: Additional arguments passed to from_pretrained()

    Returns:
        The loaded model

    Example:
        >>> from transformers import AutoModelForCausalLM
        >>> model = load_hf_model("TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        ...                       AutoModelForCausalLM, device_map="auto")
    """
    if model_class is None:
        from transformers import AutoModel

        model_class = AutoModel

    cache_path = _get_cache_path()

    if cache_path:
        safe_id = _sanitize_id(model_id)
        local_path = cache_path / "huggingface" / "models" / safe_id

        if _is_download_complete(local_path):
            result = model_class.from_pretrained(str(local_path), **kwargs)
            _log_loaded("model", model_id, "local cache")
            return result

    # Fall back to HuggingFace Hub
    _warn_cache_miss("Model", model_id, cache_path)
    result = model_class.from_pretrained(model_id, **kwargs)
    _log_loaded("model", model_id, "HuggingFace Hub")
    return result


def load_hf_tokenizer(
    model_id: str,
    tokenizer_class: Optional[Type] = None,
    **kwargs,
) -> Any:
    """Load a HuggingFace tokenizer, checking local cache first.

    Args:
        model_id: HuggingFace model identifier
        tokenizer_class: Optional tokenizer class. If None, uses AutoTokenizer.
        **kwargs: Additional arguments passed to from_pretrained()

    Returns:
        The loaded tokenizer

    Example:
        >>> tokenizer = load_hf_tokenizer("distilbert-base-uncased")
    """
    if tokenizer_class is None:
        from transformers import AutoTokenizer

        tokenizer_class = AutoTokenizer

    cache_path = _get_cache_path()

    if cache_path:
        safe_id = _sanitize_id(model_id)
        local_path = cache_path / "huggingface" / "tokenizers" / safe_id

        if _is_download_complete(local_path):
            result = tokenizer_class.from_pretrained(str(local_path), **kwargs)
            _log_loaded("tokenizer", model_id, "local cache")
            return result

    # Fall back to HuggingFace Hub
    # If MASTER_MIND_DATA_PATH was set, use fallback cache dir to avoid HF cache issues
    fallback_cache = _get_hf_cache_dir() if cache_path else None
    _warn_cache_miss("Tokenizer", model_id, cache_path)
    if fallback_cache:
        kwargs.setdefault("cache_dir", fallback_cache)
    result = tokenizer_class.from_pretrained(model_id, **kwargs)
    _log_loaded("tokenizer", model_id, "HuggingFace Hub")
    return result


def load_hf_processor(
    model_id: str,
    processor_class: Optional[Type] = None,
    **kwargs,
) -> Any:
    """Load a HuggingFace processor, checking local cache first.

    Args:
        model_id: HuggingFace model identifier
        processor_class: Optional processor class. If None, uses AutoProcessor.
        **kwargs: Additional arguments passed to from_pretrained()

    Returns:
        The loaded processor

    Example:
        >>> from transformers import CLIPProcessor
        >>> processor = load_hf_processor("openai/clip-vit-base-patch32", CLIPProcessor)
    """
    if processor_class is None:
        from transformers import AutoProcessor

        processor_class = AutoProcessor

    cache_path = _get_cache_path()

    if cache_path:
        safe_id = _sanitize_id(model_id)
        local_path = cache_path / "huggingface" / "processors" / safe_id

        if _is_download_complete(local_path):
            result = processor_class.from_pretrained(str(local_path), **kwargs)
            _log_loaded("processor", model_id, "local cache")
            return result

    # Fall back to HuggingFace Hub
    # If MASTER_MIND_DATA_PATH was set, use fallback cache dir to avoid HF cache issues
    fallback_cache = _get_hf_cache_dir() if cache_path else None
    _warn_cache_miss("Processor", model_id, cache_path)
    if fallback_cache:
        kwargs.setdefault("cache_dir", fallback_cache)
    result = processor_class.from_pretrained(model_id, **kwargs)
    _log_loaded("processor", model_id, "HuggingFace Hub")
    return result


def _make_hf_resource(
    resource_type: str,
    resource_name: str,
    default_class: str,
    model_id: str,
    description: Optional[str],
    class_name: Optional[str],
    optional: bool,
    subdir: str = "models",
) -> DownloadableResource:
    """Shared helper for creating HuggingFace resource downloaders."""
    if description is None:
        description = f"HuggingFace {resource_name}: {model_id}"
    if class_name is None:
        class_name = default_class

    def download() -> str:
        import transformers

        save_path = _get_save_path("huggingface", subdir, model_id)

        # If no save path configured, just warm up HF cache
        if save_path is None:
            hf_cache = _get_hf_cache_dir()
            cls = getattr(transformers, class_name)
            cls.from_pretrained(model_id, cache_dir=hf_cache)
            return f"Cached {resource_name} {model_id} (HF cache)"

        if _is_download_complete(save_path):
            return f"Already exists: {save_path}"

        save_path.mkdir(parents=True, exist_ok=True)

        cls = getattr(transformers, class_name)
        obj = cls.from_pretrained(model_id)
        obj.save_pretrained(save_path)

        _mark_download_complete(save_path)
        return f"Saved {resource_name} to {save_path}"

    return FunctionalResource(
        resource_type=resource_type,
        key=model_id,
        description=description,
        download_fn=download,
        optional=optional,
    )


def make_hf_model_resource(
    model_id: str,
    description: Optional[str] = None,
    model_class: Optional[str] = None,
    optional: bool = False,
) -> DownloadableResource:
    """Create a downloadable resource for a HuggingFace model.

    Args:
        model_id: The HuggingFace model identifier (e.g., "bert-base-uncased")
        description: A short description of the model. If None, uses a generic one.
        model_class: Name of transformers model class (e.g., "AutoModelForCausalLM").
            If None, uses "AutoModel".
        optional: If True, this resource is optional (not downloaded by default)
    """
    return _make_hf_resource(
        "hf_model", "model", "AutoModel", model_id, description, model_class, optional
    )


def make_hf_tokenizer_resource(
    model_id: str,
    description: Optional[str] = None,
    tokenizer_class: Optional[str] = None,
    optional: bool = False,
) -> DownloadableResource:
    """Create a downloadable resource for a HuggingFace tokenizer.

    Args:
        model_id: The HuggingFace model identifier (e.g., "bert-base-uncased")
        description: A short description of the tokenizer. If None, uses a generic one.
        tokenizer_class: Name of transformers tokenizer class (e.g., "GPT2Tokenizer").
            If None, uses "AutoTokenizer".
        optional: If True, this resource is optional (not downloaded by default)
    """
    return _make_hf_resource(
        "hf_tokenizer",
        "tokenizer",
        "AutoTokenizer",
        model_id,
        description,
        tokenizer_class,
        optional,
        subdir="tokenizers",
    )


def make_hf_processor_resource(
    model_id: str,
    description: Optional[str] = None,
    processor_class: Optional[str] = None,
    optional: bool = False,
) -> DownloadableResource:
    """Create a downloadable resource for a HuggingFace processor.

    Args:
        model_id: The HuggingFace model identifier (e.g.,
        "openai/clip-vit-base-patch32") description: A short description of the
        processor. If None, uses a generic one. processor_class: Name of
        transformers processor class (e.g., "CLIPProcessor").
            If None, uses "AutoProcessor".
        optional: If True, this resource is optional (not downloaded by default)
    """
    return _make_hf_resource(
        "hf_processor",
        "processor",
        "AutoProcessor",
        model_id,
        description,
        processor_class,
        optional,
        subdir="processors",
    )


def make_hf_dataset_resource(
    dataset_id: str,
    splits: str | List[str],
    description: Optional[str] = None,
    name: Optional[str] = None,
    optional: bool = False,
) -> DownloadableResource:
    """Create a downloadable resource for a HuggingFace dataset.

    Downloads the dataset and saves it to the local cache directory specified
    by MASTER_MIND_DATA_PATH environment variable.

    Args:
        dataset_id: The HuggingFace dataset identifier (e.g., "imdb")
        splits: The dataset split(s) to download (string or list of strings)
        description: A short description of the dataset. If None, uses a generic one.
        name: Dataset configuration name (e.g., "sst2" for glue)
        optional: If True, this resource is optional (not downloaded by default)
    """
    # Normalize splits to a list
    splits_list = [splits] if isinstance(splits, str) else list(splits)
    if description is None:
        description = f"HuggingFace dataset: {dataset_id}"

    def download() -> str:
        import datasets

        save_path = _get_save_path("huggingface", "datasets", dataset_id, name)

        # If no save path configured, just warm up HF cache
        if save_path is None:
            hf_cache = _get_hf_cache_dir()
            for split in splits_list:
                datasets.load_dataset(dataset_id, name, split=split, cache_dir=hf_cache)
            return f"Cached {dataset_id} splits {splits_list} (HF cache)"

        save_path.mkdir(parents=True, exist_ok=True)

        results = []
        for split in splits_list:
            split_dir = save_path / split
            if _is_download_complete(split_dir):
                results.append(f"{split}: already exists")
                continue

            # Load and save the specific split
            split_dir.mkdir(parents=True, exist_ok=True)
            dataset = datasets.load_dataset(dataset_id, name, split=split)
            dataset.save_to_disk(str(split_dir))
            _mark_download_complete(split_dir)
            results.append(f"{split}: saved")

        return f"Saved to {save_path} ({', '.join(results)})"

    splits_str = "+".join(splits_list)
    key = (
        f"{dataset_id}/{splits_str}"
        if not name
        else f"{dataset_id}/{name}/{splits_str}"
    )

    return FunctionalResource(
        resource_type="hf_dataset",
        key=key,
        description=description,
        download_fn=download,
        optional=optional,
    )
