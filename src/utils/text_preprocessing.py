import re
import unicodedata

CHARS_TO_REMOVE = set(
    [
        "\U0000f158",
        "\U0000f161",
        "\U0000e681",
        "\U0000e665",
        "\U0000f1a7",
        "\U0000f217",
        "\U0000feff",
    ]
)


def normalize_text(text: str) -> str:
    """
    Normalize a transcription text by removing uncertainty tags and cleaning whitespace.

    Steps performed:
        1. Remove content inside square brackets `[...]` (e.g., `[?]`, `[...]`).
        2. Remove content inside angle brackets `<...>` (e.g., `<unclear>`).
        3. Convert the entire string to lowercase.
        4. Replace newline characters with spaces.
        5. Collapse multiple spaces into a single space.
        6. Strip leading/trailing whitespace.

    Args:
        text (str): Raw transcription text (may contain markup or line breaks).

    Returns:
        str: Normalized text suitable for tokenization or lexicon extraction.
    """

    text = re.sub(r"\[[^\]]*\]", "", text)
    text = re.sub(r"<[^>]*>", "", text)

    normalized_text = text.lower()

    normalized_text = re.sub(r"\n+", " ", normalized_text)

    return re.sub(r"\s+", " ", normalized_text).strip()


def normalize_text_for_lm(text: str) -> str:
    """
    Normalize text specifically for training or scoring with a language model (KenLM).

    Steps performed:
        1. Convert to lowercase.
        2. Replace any sequence of digits (e.g., 1234) with the special token `<num>`.
        3. Remove all characters except letters, digits, whitespace, apostrophe,
           hyphen, angle brackets (preserving `<num>`) and the dash.
        4. Collapse multiple spaces into a single space and strip.

    Args:
        text (str): Input transcription (already optionally normalized).

    Returns:
        str: Text ready for LM training or perplexity scoring.
    """
    text = re.sub(r"\b\d+\b", "<num>", text.lower())
    text = re.sub(r"[^\w\s'<>\-]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize_words(text: str):
    """
    Split a string into a list of words using whitespace as delimiter.

    This is a simple whitespace tokenizer suitable for normalized texts
    where punctuation and spaces are already cleaned.

    Args:
        text (str): Normalized transcription text.

    Returns:
        list: List of word tokens (preserves original order).
    """
    return text.split()


def tokenize_chars(text: str):
    """
    Split a string into a list of characters, ignoring spaces.

    Spaces are removed entirely; every other character becomes a separate
    element in the returned list. Useful for character‑level analysis or
    generating character n‑grams.

    Args:
        text (str): Input text (may contain spaces).

    Returns:
        list: List of characters (spaces omitted).
    """
    return list(text.replace(" ", ""))


def clean_token(token: str) -> str:
    clean = unicodedata.normalize("NFC", token)

    clean = "".join(char for char in token if char not in CHARS_TO_REMOVE)
    return clean


if __name__ == "__main__":
    with open("data/lexicon/general_lexicon.txt", "r", encoding="utf-8") as file:
        lexicon = file.readlines()
    for token in lexicon:
        cleaned = clean_token(token)
        if cleaned:
            with open("./test.txt", "a", encoding="utf-8") as f:
                f.write(cleaned)
