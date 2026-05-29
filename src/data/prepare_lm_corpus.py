import os
import sys
from pathlib import Path

from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


from src.config.config_loader import load_config
from src.data.prepare_lexicon import extract_transcription_from_xml
from src.utils.text_preprocessing import normalize_text_for_lm

config = load_config()
corpora_dir = config["lexicon_corpora_dir_input"]
output_dir = config["perplexity"]["lm_corpus_path"]
os.makedirs(output_dir, exist_ok=True)

corpora = [
    d for d in os.listdir(corpora_dir) if os.path.isdir(os.path.join(corpora_dir, d))
]

corpus = []
for repository in tqdm(corpora, desc="Processing repositories"):
    repo_path = os.path.join(corpora_dir, repository)

    transcription_raw = extract_transcription_from_xml(repo_path, concatenate=False)
    for document in transcription_raw:
        for line in document:
            normalized_line = normalize_text_for_lm(line)
            corpus.append(normalized_line)

with open(os.path.join(output_dir, "corpus.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(corpus))
