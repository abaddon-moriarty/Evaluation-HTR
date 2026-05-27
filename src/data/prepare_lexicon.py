import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config.config_loader import load_config
from src.data.download_corpora import clone_repo
from src.utils.text_preprocessing import normalize_text

config = load_config()

corpora = config["lexicon_corpora_source"]
corpora_dir = config["lexicon_corpora_dir_input"]
lexicon_output = config["lexicon_dir_output"]

lexicon = set()


def extract_transcription_from_xml():
    ns = {"alto": "http://www.loc.gov/standards/alto/ns-v4#"}
    transcription = []
    for roots, dirs, files in os.walk(f"{corpora_dir}cremma-medieval"):
        for file in files:
            if file.endswith("chocomufin.xml"):
                file_dir = f"{roots}/{file}"
                tree = ET.parse(file_dir)
                root = tree.getroot()

                string_elements = root.findall(".//alto:String", namespaces=ns)

                contents = [elem.get("CONTENT", "") for elem in string_elements]
                transcription.append(" ".join(contents))
    print(transcription)
    return " ".join(transcription)


def extract_lexicon_from_transcription(transcription):
    pattern = r"[^\s.,;:!?()\[\]{}\"']+"
    mots = re.findall(pattern, transcription, flags=re.UNICODE)
    return mots


def create_lexicon():
    """
    Parcourt récursivement tous les dossiers des siècles.
    Pour chaque fichier .txt :
    Applique normalize_text.
    Extrait les mots via regex (lettres + accents + ligatures).
    Ajoute chaque mot à un ensemble global.
    Sauvegarde l’ensemble trié dans data/lexicon_global.txt.
    (Optionnel) Sauvegarde aussi un lexique par siècle si vous avez activé l’option.
    4.6 – Gérer les erreurs de téléchargement
    Si un dépôt est inaccessible, affichez un message d’avertissement mais continuez avec les autres. Vous pouvez aussi proposer à l’utilisateur de télécharger manuellement et de placer les fichiers aux bons endroits.
    """

    for repository in tqdm(corpora, unit="corpus"):
        clone_repo(repository)
        transcription = extract_transcription_from_xml()
        normalized_transcription = normalize_text(transcription)
        print(normalized_transcription)
        lexicon.update(extract_lexicon_from_transcription(normalized_transcription))
    with open(lexicon_output, "w+", encoding="utf-8") as f:
        f.write("\n".join(sorted(lexicon)))


if __name__ == "__main__":
    create_lexicon()
