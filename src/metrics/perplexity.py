import sys
from pathlib import Path

import kenlm

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config.config_loader import load_config
from src.utils.text_preprocessing import normalize_text_for_lm

config = load_config()
lm_model_path = config["perplexity"]["lm_model_path"]


class PerplexityScorer:
    def __init__(self, model_path: str):
        self.model = kenlm.Model(model_path)

    def compute_perplexity(self, text: str) -> float:
        if not text.strip():
            return float("inf")
        norm = normalize_text_for_lm(text)
        ppl = self.model.perplexity(norm)
        return ppl


def compute_perplexity(transcription: str, model_path: str) -> float:
    scorer = PerplexityScorer(model_path)
    return scorer.compute_perplexity(transcription)


if __name__ == "__main__":
    scorer = PerplexityScorer(lm_model_path)
    test_file = "data/transcription/transcription_etudiant_ex_1/DOC_D/transcription_ouazar__docuementD.txt"

    with open(test_file, "r", encoding="utf-8") as f:
        raw_text = f.read()

    ppl = scorer.compute_perplexity(raw_text)
    print(f"Perplexity: {ppl:.2f}")
