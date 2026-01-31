import logging
import sys
import os


def rital():
    try:
        from datamaestro import prepare_dataset
    except ModuleNotFoundError:
        logging.info("Datamaestro n'est pas installé (cela ne devrait pas arriver)")
        sys.exit(1)

    for dataset_id in [
        "com.github.aagohary.canard",
        "irds.antique.train",
        "irds.antique.test",
    ]:
        logging.info("Preparing %s", dataset_id)
        prepare_dataset(dataset_id)

    try:
        from transformers import AutoTokenizer, AutoModelForMaskedLM
    except ModuleNotFoundError:
        logging.info("Datamaestro n'est pas installé (cela ne devrait pas arriver)")
        sys.exit(1)

    for hf_id in ["Luyu/co-condenser-marco", "huawei-noah/TinyBERT_General_4L_312D"]:
        AutoTokenizer.from_pretrained(hf_id)
        AutoModelForMaskedLM.from_pretrained(hf_id)


def llm():
    try:
        from transformers import (
            AutoTokenizer,
            AutoModelForCausalLM,
            AutoModelForSequenceClassification,
        )
    except ModuleNotFoundError:
        logging.info("Datamaestro n'est pas installé (cela ne devrait pas arriver)")
        sys.exit(1)

    try:
        import datasets
    except ModuleNotFoundError:
        logging.info("datasets n'est pas installé (cela ne devrait pas arriver)")
        sys.exit(1)

    try:
        import pyterrier as pt
    except ModuleNotFoundError:
        logging.info("pyterrier n'est pas installé (cela ne devrait pas arriver)")
        sys.exit(1)

    HF_MODELS = [
        # Course 2
        ("TinyLlama/TinyLlama-1.1B-Chat-v1.0", AutoModelForCausalLM),
        ("distilbert-base-uncased", AutoModelForSequenceClassification),
        (
            "distilbert-base-uncased-finetuned-sst-2-english",
            AutoModelForSequenceClassification,
        ),
        # Course 3
        ("Qwen/Qwen2.5-3B-Instruct-AWQ", AutoModelForCausalLM),
        ("Qwen/Qwen2.5-7B-Instruct-AWQ", AutoModelForCausalLM),
        ("HuggingFaceTB/SmolLM2-1.7B-Instruct", AutoModelForCausalLM),
    ]
    for hf_id, base_class in HF_MODELS:
        try:
            logging.info("[LLM] Installing %s", hf_id)
            AutoTokenizer.from_pretrained(hf_id)
            base_class.from_pretrained(hf_id)
        except Exception:
            logging.exception("[LLM] error while installing %s", hf_id)

    # IMDB
    logging.info("[LLM] Downloading IMDB")
    datasets.load_dataset("imdb", split="train")

    # Praticals 4 and 5
    logging.info("[LLM] Downloading ir-datasets 'lotte/technology/dev/search'")
    pt.get_dataset("irds:lotte/technology/dev/search")


def amal():
    try:
        from datamaestro import prepare_dataset
    except ModuleNotFoundError:
        logging.info("Datamaestro n'est pas installé (cela ne devrait pas arriver)")
        sys.exit(1)

    try:
        import datasets
    except ModuleNotFoundError:
        logging.info("datasets n'est pas installé (cela ne devrait pas arriver)")
        sys.exit(1)

    # From datamaestro
    for dataset_id in [
        "com.lecun.mnist",
        "edu.uci.boston",
        "org.universaldependencies.french.gsd",
        "edu.stanford.aclimdb",
        "edu.stanford.glove.6b.50",
    ]:
        logging.info("Preparing %s", dataset_id)
        prepare_dataset(dataset_id)

    # Hugging Face (CelebA)
    datasets.load_dataset(
        "nielsr/CelebA-faces", os.environ.get("HF_DATASETS_CACHEDIR", None)
    )
