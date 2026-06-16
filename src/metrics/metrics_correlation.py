import os
import sys
from pathlib import Path

import pandas as pd
import torch
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config.config_loader import load_config
from src.metrics.lexical import compute_ngram_ratios, compute_token_ratio, load_lexicon
from src.metrics.perplexity import PerplexityScorer
from src.metrics.pseudo_perplexity import PseudoPerplexityScorer

print("__CUDA Device Name:", torch.cuda.get_device_name(0))
config = load_config()
lexicon_path = os.path.join(config["lexicon_dir_output"], config["lexicon_output_file"])
kenlm_path = config["perplexity"]["lm_model_path"]

lexicon = load_lexicon(lexicon_path)
kenlm_scorer = PerplexityScorer(kenlm_path)
mlm_scorer = PseudoPerplexityScorer()

student_folder = "data/transcription/transcription_etudiant_ex_1"
results = []

for root, _, files in os.walk(student_folder):
    for file in tqdm(files, desc="Processing students"):
        if not file.endswith(".txt"):
            continue
        file_path = os.path.join(root, file)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        except UnicodeDecodeError:
            with open(file_path, "r", encoding="latin-1") as f:
                text = f.read()

        if not text.strip():
            token_ratio = ngram_ratio = perplexity = pseudo_ppl = float("nan")
        else:
            token_ratio = compute_token_ratio(text, lexicon)
            ngram_ratio = compute_ngram_ratios(text, lexicon)
            perplexity = kenlm_scorer.compute_perplexity(text)
            pseudo_ppl = mlm_scorer.compute_pseudo_perplexity(text[:2000])

        results.append(
            {
                "student": file.replace(".txt", ""),
                "token_ratio": token_ratio,
                "ngram_ratio": ngram_ratio,
                "perplexity": perplexity,
                "pseudo_perplexity": pseudo_ppl,
                "file_path": file_path,
            }
        )

df = pd.DataFrame(results)
df.to_csv("output_metrics.csv", index=False)
print(df.sort_values("perplexity"))
