import os
from pathlib import Path

import torch

from src.data.prepare_lexicon import (
    extract_lexicon_from_transcription,
    extract_transcription_from_xml,
)
from src.utils.text_preprocessing import normalize_text


class HTRModel:
    """Chargeur générique pour différents moteurs HTR."""

    def __init__(
        self, model_name: str, model_type: str = "kraken", device: str = "cuda"
    ):
        self.model_name = model_name
        self.model_type = model_type
        self.device = device if torch.cuda.is_available() else "cpu"
        self.model = self._load_model()

    def _load_model(self):
        if self.model_type == "kraken":
            from kraken import b64a

            self.model = b64a.load_model(self.model_name)
            return self.model
        elif self.model_type == "trocr":
            from transformers import TrOCRProcessor, VisionEncoderDecoderModel

            self.processor = TrOCRProcessor.from_pretrained(self.model_name)
            self.model = VisionEncoderDecoderModel.from_pretrained(self.model_name)
            self.model.to(self.device)
            return self.model
        else:
            raise ValueError(f"Type de modèle non supporté: {self.model_type}")

    def transcribe(self, image_path: str) -> str:
        """Transcrit une image et retourne le texte brut."""
        from PIL import Image

        if self.model_type == "kraken":
            im = Image.open(image_path)
            pred = self.model.recognize(im)
            return pred[0][0]  # texte
        elif self.model_type == "trocr":
            pixel_values = self.processor(
                Image.open(image_path), return_tensors="pt"
            ).pixel_values.to(self.device)
            generated_ids = self.model.generate(pixel_values)
            return self.processor.batch_decode(generated_ids, skip_special_tokens=True)[
                0
            ]
        else:
            raise NotImplementedError

    def transcribe_folder(
        self, folder_path: str, page_ids: list[str]
    ) -> dict[str, str]:
        """Transcrit toutes les images correspondant aux page_ids."""
        results = {}
        for pid in page_ids:
            img_path = None
            for ext in [".png", ".jpg", ".jpeg", ".tiff"]:
                candidate = Path(folder_path) / f"{pid}{ext}"
                if candidate.exists():
                    img_path = candidate
                    break
            if img_path:
                results[pid] = self.transcribe(str(img_path))
            else:
                print(f"Image manquante pour {pid} dans {folder_path}")
        return results


if __name__ == "__main__":
    model = HTRModel("magistermilitum/tridis_HTR", model_type="trocr")

    xml_root = (
        "./data/corpora/CREMMA-MSS-17/data/correspondance-dom-bernard-de-montfaucon"
    )
    if os.path.isdir(xml_root):
        all_file_contents = extract_transcription_from_xml(xml_root, concatenate=False)
        for idx, content_list in enumerate(all_file_contents):
            file_text = " ".join(content_list)
            print(f"Fichier {idx} : {file_text[:100]}...")

        full_corpus = extract_transcription_from_xml(xml_root, concatenate=True)
        normalized_full = normalize_text(full_corpus)
        words = extract_lexicon_from_transcription(normalized_full)
        print(f"Nombre de mots uniques dans le corpus : {len(set(words))}")
    else:
        print(f"Le dossier {xml_root} n'existe pas.")
