from pathlib import Path


def load_transcriptions(model_dir, page_ids):
    """
    Load transcriptions for a single model.
    Args:
        model_dir: path to directory containing .txt files for each page
        page_ids: list of page identifiers (e.g., "page001")
    Returns:
        dict {page_id: full_text}
    """
    transcriptions = {}
    for page_id in page_ids:
        transcription_path = Path(model_dir + page_id)
        if transcription_path.exists():
            with open(transcription_path, "r", encoding="utf-8") as f:
                transcriptions[page_id] = f.readlines()
        else:
            print(f"Warning: missing {transcription_path}")

    return transcriptions


def load_ground_truth(gt_dir, page_ids):
    """
    Load Ground Trutg transcriptions (Validation only)

    Args:
        gt_dir: path to directory containing .txt files for each page
        page_ids: list of page identifiers (e.g., "page001")
    Returns:
        dict {page_id: full_text}
    """
    transcriptions = {}
    for page_id in page_ids:
        transcription_path = Path(gt_dir + page_id)
        if transcription_path.exists():
            with open(transcription_path, "r", encoding="utf-8") as f:
                transcriptions[page_id] = f.readlines()
        else:
            print(f"Warning: missing {transcription_path}")

    return transcriptions


if __name__ == "__main__":
    tr = load_transcriptions(
        "your/transcritpion/path/",
        [
            "voltaire_0_chatGPT.txt",
            "voltaire_0_claude.txt",
            "voltaire_0_deepseek.txt",
            "voltaire_0_gemini.txt",
            "voltaire_0.txt",
        ],
    )

    print(tr)
