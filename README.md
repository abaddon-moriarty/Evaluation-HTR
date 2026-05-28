# HTR Model Evaluation without Ground Truth

**Work in progress**: Un-official implementation of the method described in **"Evaluation of HTR models without Ground Truth Material"** (Ströbel et al., LREC 2022).
[Official repository](https://github.com/pstroe/atr-eval) is not yet available, so we are building our own.

## Current status (May 2026)
- [x] **Lexicon builder** – downloads medieval corpora from GitHub (CREMMA‑medieval, CREMMA‑MSS‑15/16/17, etc.) and builds a word list from ALTO XML files.
- [ ] **Lexicon‑based metrics** (token ratio, n‑gram ratio) – planned
- [ ] **Statistical language model perplexity with KenLM** – planned
- [ ] **Pseudo‑perplexity with BERT (masked language model)** – planned
- [ ] **Model ranking & Spearman correlation** to validate metrics against a reference ranking – planned
- [ ] **Integrating modularity** easily adding custom metrics – planned
- [ ] **Evaluation script** – planned
- [ ] **Export results as CSV/JSON** – planned

This package allows you to rank multiple HTR models (e.g., Kraken, TrOCR) based solely on their transcriptions of unlabeled historical documents. It computes several automatic metrics (lexical ratios, perplexity, pseudo-perplexity) and evaluates their correlation with true CER rankings on a small validation set (if available). The method is especially useful when no ground truth exists for the test pages.

## Installation

```bash
git clone https://github.com/abaddon-moriarty/Evaluation-HTR.git
cd Evaluation-HTR
```


## Building a Lexicon (current working part)

### Sources used

We automatically download transcriptions from the following public repositories:
- [CREMMA‑medieval](https://github.com/htR-United/cremma-medieval) (13th–14th c.)
- [CREMMA‑MSS‑15](https://github.com/HTR-United/CREMMA-MSS-15) (15th c.)
- [CREMMA‑MSS‑16](https://github.com/HTR-United/CREMMA-MSS-16) (16th c.)
- [CREMMA‑MSS‑17](https://github.com/HTR-United/CREMMA-MSS-17) (17th c.)
- Additional corpora listed in `config.yaml` under `lexicon_corpora_source`.

These repositories contain ALTO XML files (from eScriptorium) that provide line‑level transcriptions.

### Command

```bash
python src/data/prepare_lexicon.py --download --output my_lexicon.txt
```

Options:
- `--download` : clone / update all repositories from GitHub (skip if already present). If omitted, the downloading step is skipped entirely
- `--input_dir` : (optional) use a local directory to generate the lexicon instead of using all corpora. The script will process every subfolder as a separate corpus. This allows you to build a lexicon from a specific century or from your own transcriptions. **This option does NOT trigger downloading** – it only changes what folders are read.
- `--output` : name of the output lexicon file (saved in `data/lexicon/`). Default: `lexicon_global.txt`.

### How it works

1. If `--download` is given, the script downloads all configured repositories into `data/corpora/` (skipping those already present).
2. It then determines which folders to scan:
   - If `--input_dir` is provided (and different from the default `data/corpora/`), it sets the scan list to **all immediate subdirectories** of that folder.
   - Otherwise, it uses the names of the downloaded repositories (extracted from the URLs) as the scan list.
3. For each folder in the scan list, it recursively walks through the directory, reads every `.xml` file, extracts the text from `<String CONTENT="...">` tags (ALTO format), and concatenates it.
4. The raw text is normalised (lowercase, removal of `[...]` and similar markup).
5. Words are extracted using a regular expression that keeps letters, digits, common abbreviations (`⁊`, `ꝑ`, etc.) and ignores punctuation.
6. All unique words are stored in a set, sorted, and saved as a newline‑separated file.

### Example

```bash
# Download all corpora and build a global lexicon
python src/data/prepare_lexicon.py --download --output global_lexicon.txt

# Use only already downloaded corpora (no network)
python src/data/prepare_lexicon.py --output local_lexicon.txt

# Process a custom folder with your own XML files
python src/data/prepare_lexicon.py --input_dir ./my_corpora --output my_lexicon.txt

# Build a lexicon from a custom folder (e.g., only 15th‑century manuscripts)
python src/data/prepare_lexicon.py --input_dir ./my_15th_century_data --output lexicon_15c.txt

# Combine: first download, then restrict to a subfolder (e.g., one specific manuscript)
python src/data/prepare_lexicon.py --download --input_dir data/corpora/CREMMA-MSS-15 --output mss15_lexicon.txt
```

In the last example, the download still fetches all repos, but the lexicon is built **only** from the `CREMMA‑MSS‑15` folder (because `--input_dir` overrides the scan list).

### Adding your own corpus
Simply place your ALTO XML files inside a folder (or a tree of subfolders), then use `--input_dir /path/to/your/folder`. The script will treat each **immediate subfolder** as a separate source and merge all words into a single lexicon.

> The transcription is pulled from xml files, extracting `<String CONTENT>` tag. If using custom corpora, make sure they contain this tag.


## Reference

If you use this code, please cite:

```
@inproceedings{strobel-etal-2022-evaluation,
    title = "Evaluation of {HTR} models without Ground Truth Material",
    author = {Ströbel, Phillip  and Clematide, Simon  and Volk, Martin},
    booktitle = "Proceedings of the Thirteenth Language Resources and Evaluation Conference",
    year = "2022",
    publisher = "European Language Resources Association",
    url = "https://aclanthology.org/2022.lrec-1.467",
    pages = "4382--4391"
}
```