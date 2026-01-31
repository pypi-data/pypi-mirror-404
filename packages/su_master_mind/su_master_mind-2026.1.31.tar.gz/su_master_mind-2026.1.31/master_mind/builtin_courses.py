"""Built-in course plugin implementations.

This module defines the plugin implementations for courses that are
built into the su_master_mind package (using extras).
"""

import logging
import shutil
import sys
from typing import Dict, List, Optional
import click

from .plugin import BuiltinCoursePlugin, DownloadableResource, FunctionalResource


class DeeplCoursePlugin(BuiltinCoursePlugin):
    """Deep Learning course plugin."""

    @property
    def name(self) -> str:
        return "deepl"

    @property
    def description(self) -> str:
        return "Deep Learning course"

    def download_datasets(self) -> None:
        pass


class RLCoursePlugin(BuiltinCoursePlugin):
    """Reinforcement Learning course plugin."""

    @property
    def name(self) -> str:
        return "rl"

    @property
    def description(self) -> str:
        return "Reinforcement Learning course"

    def get_cli_group(self) -> Optional[click.Group]:
        """Return the RL-specific CLI command group."""
        from .cli.rl import rl_group

        return rl_group

    def get_downloadable_resources(self) -> Dict[str, List[DownloadableResource]]:
        return {}

    def pre_install_check(self) -> bool:
        """Check that swig is installed."""
        if sys.platform == "win32":
            has_swig = shutil.which("swig.exe")
        else:
            has_swig = shutil.which("swig")

        if not has_swig:
            logging.error(
                "swig n'est pas installé: sous linux utilisez le "
                "gestionnaire de paquets:\n - sous windows/conda : "
                "conda install swig\n - sous ubuntu: sudo apt install swig"
            )
            return False
        return True


class ADLCoursePlugin(BuiltinCoursePlugin):
    """Advanced Deep Learning course plugin."""

    @property
    def name(self) -> str:
        return "adl"

    @property
    def description(self) -> str:
        return "Advanced Deep Learning course"

    def download_datasets(self) -> None:
        pass


class RitalCoursePlugin(BuiltinCoursePlugin):
    """Information Retrieval course plugin."""

    @property
    def name(self) -> str:
        return "rital"

    @property
    def description(self) -> str:
        return "Information Retrieval course"

    def get_downloadable_resources(self) -> Dict[str, List[DownloadableResource]]:
        def make_datamaestro_resource(
            dataset_id: str, desc: str
        ) -> DownloadableResource:
            def download() -> str:
                from datamaestro import prepare_dataset

                prepare_dataset(dataset_id)
                return f"Prepared {dataset_id}"

            return FunctionalResource(
                resource_type="datamaestro",
                key=dataset_id,
                description=desc,
                download_fn=download,
            )

        def make_hf_model_resource(
            hf_id: str, desc: str, model_class_name: str = "AutoModelForMaskedLM"
        ) -> DownloadableResource:
            def download() -> str:
                from transformers import AutoTokenizer
                import transformers

                model_class = getattr(transformers, model_class_name)
                AutoTokenizer.from_pretrained(hf_id)
                model_class.from_pretrained(hf_id)
                return f"Downloaded {hf_id}"

            return FunctionalResource(
                resource_type="hf_model",
                key=hf_id,
                description=desc,
                download_fn=download,
            )

        return {
            "datasets": [
                make_datamaestro_resource(
                    "com.github.aagohary.canard", "CANARD conversational QA dataset"
                ),
                make_datamaestro_resource(
                    "irds.antique.train", "ANTIQUE QA dataset (train)"
                ),
                make_datamaestro_resource(
                    "irds.antique.test", "ANTIQUE QA dataset (test)"
                ),
            ],
            "models": [
                make_hf_model_resource(
                    "Luyu/co-condenser-marco", "Co-Condenser model for MS MARCO"
                ),
                make_hf_model_resource(
                    "huawei-noah/TinyBERT_General_4L_312D", "TinyBERT 4-layer model"
                ),
            ],
        }
