# HTR Model Evaluation without Ground Truth

**Work in progress**: Un-official implementation of the method described in **"Evaluation of HTR models without Ground Truth Material"** (Ströbel et al., LREC 2022).
[Official repository](https://github.com/pstroe/atr-eval) is not yet available, so we are building our own.

## Current status (May 2026)
- [x] **Lexicon builder** – downloads medieval corpora from GitHub (CREMMA‑medieval, CREMMA‑MSS‑15/16/17, etc.) and builds a word list from ALTO XML files.
- [x] **Lexicon‑based metrics** – token ratio and character n‑gram ratio (implemented in `src/metrics/lexical.py`).
- [x] **Statistical language model perplexity with KenLM** – implemented in `src/metrics/perplexity.py`. Training instructions are provided below.
- [x] **Pseudo‑perplexity with MLM (masked language model)** – implemented in `src/metrics/pseudo_perplexity.py`. Supports multiple models with automatic fallback (medieval BERT, Latin BERT, multilingual BERT).
- [x] **Evaluation script** – runs all metrics on student transcriptions and exports results as CSV (src/metrics/metrics_correlation.py).
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

## Adding lexical metrics (token ratio & character n‑gram ratio)

Once you have a lexicon (e.g., `data/lexicon/global_lexicon.txt`), you can evaluate how much of a transcription’s vocabulary is covered by known words (token ratio) and how well its character sequences match substrings of real words (n‑gram ratio).

### Implementation files
- `src/metrics/lexical.py` – contains `compute_token_ratio` and `compute_ngram_ratios`.
- `src/utils/text_preprocessing.py` – provides `normalize_text` and `tokenize_words`.


### How to use

```python
from src.metrics.lexical import load_lexicon, compute_token_ratio, compute_ngram_ratios

# Load the lexicon (set of words)
lexicon = load_lexicon("data/lexicon/global_lexicon.txt")

# Read a student transcription
with open("student_transcription.txt", "r", encoding="utf-8") as f:
    transcript = f.read()

# Token ratio (percentage of known words)
token_ratio = compute_token_ratio(transcript, lexicon)
print(f"Token ratio: {token_ratio*100:.2f}%")

# Character n‑gram ratio (average for n=2…7)
ngram_ratio = compute_ngram_ratios(transcript, lexicon)
print(f"Character n‑gram ratio: {ngram_ratio*100:.2f}%")
```

### What the numbers mean

- **Token ratio** – high values (e.g., > 70%) indicate that most words are already in the lexicon, suggesting a clean transcription with few out‑of‑vocabulary or erroneous words.
- **Character n‑gram ratio** – usually slightly lower than token ratio, because it considers every short character sequence. A high value (close to token ratio) means the transcription uses plausible letter combinations typical of the language.

Both metrics are **unsupervised** – they do not require ground truth. Lower ratios generally signal more errors or unusual spellings, but they are most useful when **comparing multiple models** on the same pages.


---

## Statistical language model perplexity with KenLM

Perplexity measures how predictable a text is according to a language model. Lower perplexity means the transcription follows the patterns of the training corpus (more “fluent”).

### Step 1 – Install KenLM and train a custom language model

We use **KenLM** because it is fast and works well with n‑gram models on medieval texts.

#### 1.1 Install system dependencies (Fedora / Linux)

```bash
sudo dnf install -y gcc-c++ cmake make boost-devel eigen3-devel xz-devel
```

(For Debian/Ubuntu: `sudo apt install build-essential cmake libboost-system-dev libeigen3-dev liblzma-dev`)

#### 1.2 Clone and compile KenLM

```bash
git clone https://github.com/kpu/kenlm.git
cd kenlm
mkdir -p build && cd build
cmake ..
make -j 4
```

The tools `lmplz` (training) and `build_binary` (conversion) will be in `kenlm/build/bin/`. You may add this directory to your `PATH` for convenience.

#### 1.3 Prepare a training corpus

You need a large collection of plain‑text lines (one line = one manuscript line or one sentence) that represents the language of your evaluation pages.  
A practical method: use the same ALTO XML files you already downloaded for the lexicon, but extract **one line per `<TextLine>`** (not per file).

Create a script (e.g., `scripts/prepare_lm_corpus.py`) that:

- Walks through `data/corpora/`
- For every `.xml` file, extracts `<TextLine>` and inside it, joins all `<String CONTENT>` values with spaces.
- Normalises each line using `normalize_text_for_lm` (lowercase, digits → `<num>`, remove punctuation).
- Writes each line to `corpus.txt`.

Then run:

```bash
python scripts/prepare_lm_corpus.py   # (you need to write it)
```

#### 1.4 Train the n‑gram model (trigram recommended for medieval data)

```bash
./kenlm/build/bin/lmplz -o 3 --verbose_header \
    --text ./kenlm_data/corpus.txt \
    --arpa ./kenlm_data/model.arpa
```

If you encounter a `BadDiscountException` (due to sparse data), add `--discount_fallback`.

#### 1.5 Convert to binary for fast loading

```bash
./kenlm/build/bin/build_binary ./kenlm_data/model.arpa ./kenlm_data/model.bin
```

#### 1.6 Update `config.yaml`

Add or verify this entry:

```yaml
perplexity:
  lm_corpus_path: "./kenlm_data/corpus.txt"   # optional, for reference
  lm_model_path: "./kenlm_data/model.bin"
```

### Step 2 – Compute perplexity on transcriptions

We provide `src/metrics/perplexity.py` with a `PerplexityScorer` class.

```python
from src.metrics.perplexity import PerplexityScorer

scorer = PerplexityScorer("kenlm_data/model.bin")
with open("student_transcription.txt", "r") as f:
    text = f.read()
ppl = scorer.compute_perplexity(text)
print(f"Perplexity: {ppl:.2f}")
```

### Step 3 – Interpreting perplexity
- **Lower is better** – a perfect copy of the training text would have the lowest possible perplexity.
- Absolute values are not meaningful; you **compare perplexities of different models** on the same set of unlabeled pages. The model with the lowest perplexity is considered best by this metric.

---
## Pseudo‑perplexity with MLM (Masked Language Model)

Pseudo‑perplexity (Salazar et al., 2020) measures text fluency using a masked language model (MLM) without requiring a dedicated training corpus. It works by masking each token one by one and computing the model's confidence in the original token.

### Implementation

`src/metrics/pseudo_perplexity.py` provides a `PseudoPerplexityScorer` class that:
- Automatically attempts to load the best available model from a priority list:
  1. User‑specified model (via `model_name` argument)
  2. `magistermilitum/bert_medieval_multilingual` – medieval multilingual BERT
  3. `dbamman/latin-bert` – Latin BERT
  4. `pstroe/roberta-base-latin-cased` – Latin RoBERTa
  5. `google-bert/bert-base-multilingual-cased` – fallback multilingual BERT
- Processes text in sliding windows (default stride = 256, max_length = 512) to handle long documents.
- Returns the pseudo‑perplexity value (lower = more fluent).

### How to use

```python
from src.metrics.pseudo_perplexity import PseudoPerplexityScorer

# Auto‑selects best available model
scorer = PseudoPerplexityScorer()

# Or specify a particular model
scorer = PseudoPerplexityScorer(model_name="magistermilitum/bert_medieval_multilingual")

with open("student_transcription.txt", "r") as f:
    text = f.read()

pppl = scorer.compute_pseudo_perplexity(text)
print(f"Pseudo‑perplexity: {pppl:.2f}")
```

### Performance considerations

- The calculation masks each token sequentially, which can be slow for long texts. For initial testing, consider truncating to the first 500–1000 characters.
- The model is loaded once and reused across calls – cache the scorer instance.
- If you have a dedicated GPU, set `device="cuda"` to speed up inference.

### Interpreting pseudo‑perplexity

- **Lower is better** – the MLM is more confident in the token predictions, indicating the text follows expected language patterns.
- Like KenLM perplexity, absolute values are model‑dependent; use them for **ranking** multiple transcriptions, not as an absolute quality score.

---


---

## Running the Full Evaluation

Once all metrics are ready, you can run the complete evaluation on all transcription files. You must have multiple models evaluating the same page(s), otherwise you cannot compare the results.

### Command

```bash
python -m src.metrics.metrics_correlation
```

### What it does

The script:
1. Loads the lexicon, KenLM model, and MLM model.
2. Walks through `data/transcription/transcription_etudiant_ex_1/`.
3. For each `.txt` file, computes:
   - Token ratio
   - Character n‑gram ratio
   - KenLM perplexity
   - Pseudo‑perplexity
4. Exports results to `student_metrics.csv`.

### Output example

| Student                                  | Token ratio | N‑gram ratio | Perplexity | Pseudo‑perplexity |
|------------------------------------------|-------------|--------------|------------|-------------------|
| transcription_1_Document_E     | 0.752       | 0.480        | 3016.29    | 1.26e⁸            |
| Transcription_2_docB      | 0.737       | 0.469        | 3148.49    | 3.94e⁸            |
| transcription_3_doc_B         | 0.712       | 0.459        | 5204.21    | 1.24e⁸            |
| transcription_4_documentC        | 0.499       | 0.419        | 21039.33   | 3.91e⁷            |

### Interpreting the output

- **Low perplexity + high token ratio** → likely the best transcriptions
- **High perplexity + low token ratio** → transcriptions with many errors or out‑of‑vocabulary words.
- **Pseudo‑perplexity** values are on a different scale – they are useful for ranking but not directly comparable to KenLM perplexity.

---

## Next Steps: Combining Metrics and Ranking Models

Once we have a small ground‑truth validation set, we can compute the Spearman correlation between each metric's ranking and the true CER ranking.

The four unsupervised metrics (token ratio, character n‑gram ratio, KenLM perplexity, pseudo‑perplexity) can be computed for every page and every model. We can then:

1. **Rank models** by each metric (e.g., highest token ratio = rank 1; lowest perplexity = rank 1).
2. **Compute Spearman correlation** between the metric’s ranking and the true CER ranking on a small validation set (where GT exists).
3. **Select the metric with the highest correlation** to evaluate models on the real test pages (which have no GT).

This is exactly the method described in Ströbel et al. (LREC 2022).

---

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