"""
Perplexity scoring using a KenLM language model.

This module provides a class and utility function to compute the perplexity
of a transcription given a pre‑trained KenLM n‑gram model. The perplexity
measures how well the language model predicts the sequence of words; lower
values indicate more fluent or predictable text.

The module expects a KenLM binary model file (.arpa.bin) created with the
`lmplz` and `build_binary` tools. The training corpus should be representative
of the target medieval manuscripts (Old French, Middle French, Latin).

Example:
    >>> from src.metrics.perplexity import PerplexityScorer
    >>> scorer = PerplexityScorer("path/to/model.arpa.bin")
    >>> ppl = scorer.compute_perplexity("Le chat dort sur le tapis.")
    >>> print(f"Perplexity: {ppl:.2f}")
"""

import sys
from pathlib import Path

import kenlm

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config.config_loader import load_config
from src.utils.text_preprocessing import normalize_text_for_lm

config = load_config()
lm_model_path = config["perplexity"]["lm_model_path"]


class PerplexityScorer:
    """
    A wrapper for a KenLM language model that computes perplexity on a text.

    The class loads a KenLM binary model and provides a method to compute
    perplexity after normalising the input text using the same rules applied
    during LM training (lowercase, digit replacement, punctuation removal).

    Attributes:
        model (kenlm.Model): The loaded KenLM model.
    """
    def __init__(self, model_path: str):
        """
        Initialise the perplexity scorer by loading a KenLM binary model.

        Args:
            model_path (str): Path to the KenLM binary model file (.arpa.bin).

        Raises:
            RuntimeError: If the model file does not exist or is corrupted.
        """
        self.model = kenlm.Model(model_path)

    def compute_perplexity(self, text: str) -> float:
        """
        Compute the perplexity of a given text.

        The text is normalised using `normalize_text_for_lm` (lowercase,
        digits replaced by <num>, punctuation removed) before being scored
        by the KenLM model. If the input is empty, returns infinity.

        Args:
            text (str): Raw transcription text (may contain markup or line breaks).

        Returns:
            float: Perplexity value (geometric mean of inverse probabilities).
                   Lower values indicate better text fluency.
                   Returns `float('inf')` for empty input.
        """
        if not text.strip():
            return float("inf")
        norm = normalize_text_for_lm(text)
        ppl = self.model.perplexity(norm)
        return ppl


def compute_perplexity(transcription: str, model_path: str) -> float:
    """
    Convenience function to compute perplexity without instantiating the class.

    This function creates a PerplexityScorer internally and calls its method.

    Args:
        transcription (str): Raw transcription text.
        model_path (str): Path to the KenLM binary model file.

    Returns:
        float: Perplexity value (lower is better). Returns infinity for empty text.
    """
    scorer = PerplexityScorer(model_path)
    return scorer.compute_perplexity(transcription)


if __name__ == "__main__":
    scorer = PerplexityScorer(lm_model_path)
    test_file = "data/transcription/transcription_etudiant_ex_1/DOC_D/transcription_ouazar__docuementD.txt"

    with open(test_file, "r", encoding="utf-8") as f:
        raw_text = f.read()

    ppl = scorer.compute_perplexity(raw_text)
    print(f"Perplexity: {ppl:.2f}")
