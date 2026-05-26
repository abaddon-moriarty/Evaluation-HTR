from src.data.loader import load_transcriptions
from src.utils.text_preprocessing import normalize_text, tokenize_chars, tokenize_words

tr = load_transcriptions(
    "/home/barachiel/Documents/Projects/Evaluation HTR/data/",
    [
        "voltaire_0_chatGPT.txt",
        "voltaire_0_claude.txt",
        "voltaire_0_deepseek.txt",
        "voltaire_0_gemini.txt",
    ],
)

if __name__ == "__main__":
    for key, value in tr.items():
        print("*" * 40)
        print(f"Transcription de: {key}")
        print("*" * 40)
        print(f"\nRaw:\n{value}")

        text = normalize_text(value)
        print(f"\nNormalised:\n{text}")

        tr_tokens = tokenize_words(text)
        print(f"\nTokens:\n{tr_tokens}")

        tr_letters = tokenize_chars(text)
        print(f"\nLettres:\n{tr_letters}")

        break
