import re


def normalize_text(text: str) -> str:
    """
    Normalize transcription:
    - lower case
    - remove tags like [...], [?], <...>
    - keep only letters, spaces, punctuation (basic)

    """
    # Remove uncertainty tags
    text = re.sub(r"\[[^\]]*\]", "", text)
    text = re.sub(r"<[^>]*>", "", text)

    # Lowercase the text
    normalized_text = text.lower()

    # Remove new lines, multiple spaces
    normalized_text = re.sub(r"\n+", " ", normalized_text)

    return re.sub(r"\s+", " ", normalized_text).strip()


def normalize_text_for_lm(text: str) -> str:
    text = re.sub(r"\b\d+\b", "<num>", text.lower())
    text = re.sub(r"[^\w\s'<>\-]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize_words(text: str):
    """
    Découpe le texte au niveau des espaces"""
    return text.split()


def tokenize_chars(text: str):
    """
    Retourne une liste de caractères présents dans la transcription
    """
    return list(text.replace(" ", ""))
