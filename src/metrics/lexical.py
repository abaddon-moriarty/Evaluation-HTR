import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config.config_loader import load_config
from src.utils.text_preprocessing import normalize_text, tokenize_words

config = load_config()

lexicon_dir = os.path.join(config["lexicon_dir_output"], config["lexicon_output_file"])


def load_lexicon(lexicon_path):
    """
    Charge un lexique depuis un fichier texte.

    Args:
        lexicon_path (str): Chemin vers le fichier contenant un mot par ligne.

    Returns:
        set: Ensemble des mots (chaînes) présents dans le fichier,
             les lignes vides sont ignorées.
    """
    with open(lexicon_path, "r", encoding="utf-8") as f:
        lexicon = {line.strip() for line in f if line.strip()}
    return lexicon


# 5.2 Token ratio
def compute_token_ratio(transcription, lexicon) -> float:
    """
    Calcule le ratio de tokens (mots) de la transcription qui appartiennent au lexique.

    La transcription est d'abord normalisée (minuscules, suppression des balises,
    etc.), puis tokenisée par espaces. Le ratio est le nombre de mots présents
    dans le lexique divisé par le nombre total de mots.

    Args:
        transcription (str): Texte brut de la transcription.
        lexicon (set): Ensemble des mots valides (lexique).

    Returns:
        float: Ratio compris entre 0.0 et 1.0. Retourne 0.0 si aucun mot.

    Example:
        >>> lexicon = {"le", "chat"}
        >>> compute_token_ratio("Le chat dort", lexicon)
        0.6666666666666666
    """
    normalized_transcription = normalize_text(transcription)
    words = tokenize_words(normalized_transcription)
    len_total = len(words)
    known_words = [word for word in words if word in lexicon]
    len_known = len(known_words)
    ratio = len_known / len_total if len_total > 0 else 0.0
    print(f"Found {len_known} words total")

    return ratio


# 5.3 N‑gram ratio (caractères)
def compute_ngram_ratios(transcription, lexicon, n_min=2, n_max=7) -> float:
    """
    Calcule le ratio moyen des n‑grammes de caractères (n de n_min à n_max)
    qui apparaissent comme sous‑chaîne d'au moins un mot du lexique.

    La transcription est normalisée, les espaces supprimés. Pour chaque longueur n,
    on génère tous les n‑grammes glissants. Un n‑gramme est considéré "connu"
    s'il est une sous‑chaîne d'un mot du lexique (ex. "bo" est connu si "bonjour"
    est dans le lexique). Le ratio pour un n est le nombre de n‑grammes connus
    divisé par le nombre total de n‑grammes de cette longueur. La fonction
    retourne la moyenne de ces ratios sur toutes les longueurs de n_min à n_max.

    Args:
        transcription (str): Texte brut de la transcription.
        lexicon (set): Ensemble des mots du lexique.
        n_min (int): Longueur minimale des n‑grammes (défaut 2).
        n_max (int): Longueur maximale des n‑grammes (défaut 7).

    Returns:
        float: Moyenne des ratios pour chaque n, comprise entre 0.0 et 1.0.
               Retourne 0.0 si la transcription est vide ou trop courte.

    Example:
        >>> lexicon = {"bonjour", "le"}
        >>> # "bonjour" contient "bo", "on", "nj", ... et "le" contient "le"
        >>> compute_ngram_ratios("bonjour le monde", lexicon)
        0.xxx
    """
    # Remarque : un n‑gramme de caractères est considéré comme connu s’il apparaît comme sous‑chaîne d’au moins un mot du lexique (et non pas comme mot entier). Implémentez une vérification par appartenance à une chaîne.
    normalized_transcription = normalize_text(transcription)
    ngram_transcription = re.sub(r"\s+", "", normalized_transcription)
    ngrams = []
    for n in range(n_min, n_max + 1):
        for i in range(len(ngram_transcription) - n + 1):
            ngrams.append(ngram_transcription[i : i + n])
    known_ngrams = [ngram for ngram in ngrams if any(ngram in word for word in lexicon)]
    print(f"Found {len(known_ngrams)} n_grams total")
    ratio = len(known_ngrams) / len(ngrams) if len(ngrams) > 0 else 0.0
    return ratio


if __name__ == "__main__":
    lexicon = sorted(load_lexicon(lexicon_dir))
    with open(
        "data/transcription/transcription_etudiant_ex_1/DOC_D/transcription_ouazar__docuementD.txt",
        "r",
        encoding="utf-8",
    ) as f:
        transcription = f.read()
        print(transcription[:500])

    ratio = compute_token_ratio(transcription, lexicon)
    print(round(ratio * 100, 2), "%")

    ngram_ratio = compute_ngram_ratios(transcription, lexicon)
    print(round(ngram_ratio * 100, 2), "%")
