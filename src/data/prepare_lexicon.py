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
    """
    Extract all text from ALTO XML files in a directory tree.

    The function walks through the given directory, finds all `.xml` files,
    and extracts the content of every `<String>` element (using the ALTO
    namespace). If `concatenate` is True, all strings from a single file
    are joined with spaces and then all files are joined into a single
    string. If `concatenate` is False, the function returns a list where
    each element is a list of strings (one per file), preserving per‑file
    grouping of `<String>` elements.

    Args:
        repo_path (str): Root directory to search for ALTO XML files.
        concatenate (bool, optional): If True, return a single concatenated
            string for all files. If False, return a list of lists, each
            inner list containing the `<String>` contents of one file.
            Defaults to True.

    Returns:
        str or list: If `concatenate` is True, a single string containing
        all text from all XML files, with spaces between each `<String>`
        element. If `concatenate` is False, a list where each element is
        a list of strings (the extracted `<String>` contents of one file).

    Raises:
        ET.ParseError: If an XML file is malformed. The function does not
            catch the exception – the caller should handle it if needed.
    """
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
    """
    Extract unique word‑like tokens from a normalized transcription.

    The function uses a regular expression that matches any sequence of
    characters that are NOT spaces or common punctuation (.,;:!?()[]{}\"').
    This keeps letters, digits, medieval abbreviations (⁊, ꝑ, etc.), and
    internal punctuation (e.g., dots inside words). The returned list
    contains duplicates; it is intended to be used with a set for
    deduplication.

    Args:
        transcription (str): Normalized text (typically lowercased and
            stripped of XML markup or uncertainty brackets).

    Returns:
        list: A list of tokens (words/abbreviations) in the order they
        appear in the transcription.
    """
    pattern = r"[^\s.,;:!?()\[\]{}\"']+"
    mots = re.findall(pattern, transcription, flags=re.UNICODE)
    return mots


def create_lexicon():
    """
    Build a lexicon (word list) from medieval manuscript transcriptions.

    This is the main entry point for lexicon generation. It respects command‑line
    arguments provided via argparse (--download, --input_dir, --output).

    Workflow:
        1. Parse arguments and determine output file path.
        2. Load an existing lexicon from the output file (if it exists) to
           allow incremental updates.
        3. If `--download` is given, clone all repositories listed in the
           configuration key `lexicon_corpora_source` using the `clone_repo`
           function.
        4. Determine which directories to scan:
            - If `--input_dir` is provided and differs from the default,
              that directory is used, and its immediate subdirectories
              become the `corpora` list.
            - Otherwise, use the default `corpora_dir` and the list of
              repository names from the configuration.
        5. For each repository (subdirectory), walk through its content,
           extract text from all ALTO XML files using
           `extract_transcription_from_xml`, normalize the text with
           `normalize_text`, and extract word tokens with
           `extract_lexicon_from_transcription`.
        6. Update the global lexicon set with the new words.
        7. Save the sorted lexicon to the output file (overwriting the
           previous one).

    Command‑line arguments:
        --download      : If set, download missing corpora from GitHub.
        --input_dir DIR : Path to a directory containing subdirectories of
                          transcriptions (e.g., cloned repos). Overrides the
                          default `corpora_dir`.
        --output NAME   : Output file name (placed inside `lexicon_dir_output`
                          from configuration). Defaults to the config value.

    The function writes the final lexicon to:
        `{lexicon_dir_output}/{lexicon_output_file}`

    Note:
        - The output file is completely rewritten at the end, but existing
          words are first loaded to preserve previous extractions.
        - If `--download` is omitted, the function expects the directories
          to already exist; otherwise the lexicon may be empty.
        - The function uses global configuration values for default paths
          and repository lists.
    """
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
