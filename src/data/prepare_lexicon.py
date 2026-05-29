import argparse
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
lexicon_output_file = config["lexicon_output_file"]
lexicon_dir_output = config["lexicon_dir_output"]


parser = argparse.ArgumentParser()
parser.add_argument(
    "--download",
    action="store_true",
    help="Will download corpora from the `lexicon_corpora_source` listed in the config file. No download by default.",
)
parser.add_argument(
    "--input_dir",
    type=str,
    default=corpora_dir,
    help=f"Specify the dir to generate the lexicon from. Default is: {corpora_dir}",
)
parser.add_argument(
    "--output",
    type=str,
    default=lexicon_output_file,
    help=f"Specify the lexicon output file name. Will generate in {lexicon_dir_output}. Default name is: {lexicon_output_file}",
)

args = parser.parse_args()


def extract_transcription_from_xml(repo_path, concatenate=True):

    ns = {"alto": "http://www.loc.gov/standards/alto/ns-v4#"}
    transcription = []
    for roots, _, files in os.walk(f"{repo_path}"):
        for file in files:
            if file.endswith(".xml"):
                file_dir = f"{roots}/{file}"
                tree = ET.parse(file_dir)
                root = tree.getroot()

                string_elements = root.findall(".//alto:String", namespaces=ns)

                contents = [elem.get("CONTENT", "") for elem in string_elements]
                if not concatenate:
                    transcription.append(contents)
                    continue
                transcription.append(" ".join(contents))
    if not concatenate:
        return transcription
    return " ".join(transcription)


def extract_lexicon_from_transcription(transcription):
    pattern = r"[^\s.,;:!?()\[\]{}\"']+"
    mots = re.findall(pattern, transcription, flags=re.UNICODE)
    return mots


def create_lexicon():
    global corpora_dir, lexicon_output_file

    if args.output:
        lexicon_output_file = args.output

    lexicon = set()

    lexicon_output = os.path.join(lexicon_dir_output, lexicon_output_file)

    if os.path.exists(lexicon_output):
        with open(lexicon_output, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    lexicon.add(line.strip())

    if args.download:
        download_pbar = tqdm(corpora, unit="repository")
        for repository in download_pbar:
            download_pbar.set_description_str(f"Cloning {repository}")
            clone_repo(repository)
    else:
        print("\nSkipping download. Generating lexicon.")

    if args.input_dir and (args.input_dir != corpora_dir):
        corpora_dir = args.input_dir
        if not os.path.isdir(corpora_dir):
            print(f"Erreur : {corpora_dir} n'existe pas")
            return
        corpora = [
            d
            for d in os.listdir(corpora_dir)
            if os.path.isdir(os.path.join(corpora_dir, d))
        ]
        if not corpora:
            print("Aucun sous-dossier trouvé")
            return

    lexicon_pbar = tqdm(corpora, unit="corpus")
    for repository in lexicon_pbar:
        repo_path = os.path.join(corpora_dir, repository)
        lexicon_pbar.set_description_str(f"Extracting transcription from {repository}")
        transcription = extract_transcription_from_xml(repo_path)

        normalized_transcription = normalize_text(transcription)
        # print(normalized_transcription)

        lexicon_pbar.set_description_str("Extracting lexicon")

        new_words = extract_lexicon_from_transcription(normalized_transcription)
        lexicon.update(new_words)

    os.makedirs(os.path.dirname(lexicon_output), exist_ok=True)
    with open(lexicon_output, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(lexicon)))


if __name__ == "__main__":
    create_lexicon()
