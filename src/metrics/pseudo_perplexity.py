import torch
from transformers import AutoModelForMaskedLM, AutoTokenizer

from src.utils.text_preprocessing import normalize_text


class PseudoPerplexityScorer:
    def __init__(self, model_name: str = None, device: str = None):
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        if self.device:
            print("__CUDNN VERSION:", torch.backends.cudnn.version())
            print("__Number CUDA Devices:", torch.cuda.device_count())
            print("__CUDA Device Name:", torch.cuda.get_device_name(0))
            print(
                "__CUDA Device Total Memory [GB]:",
                torch.cuda.get_device_properties(0).total_memory / 1e9,
            )
        else:
            print("CUDA not available. Running on CPU.")

        priorities = [
            # ("magistermilitum/bert_medieval_multilingual", True, None),
            # ("dbamman/latin-bert", False, self._load_latin_bert),
            ("pstroe/roberta-base-latin-cased", True, None),
            ("google-bert/bert-base-multilingual-cased", True, None),
        ]
        # Si l'utilisateur a fourni un nom, on le place en premier
        if model_name:
            priorities.insert(0, (model_name, True, None))

        self.tokenizer = None
        self.model = None

        for name, use_auto, special_loader in priorities:
            try:
                if special_loader:
                    self.tokenizer, self.model = special_loader()
                elif use_auto:
                    self.tokenizer = AutoTokenizer.from_pretrained(name)
                    self.model = AutoModelForMaskedLM.from_pretrained(name)
                else:
                    continue
                self.model_name = name
                self.model.to(self.device)
                self.model.eval()
                print(f"Loaded {name} on {self.device}")
                break
            except Exception as e:
                print(f"Failed to load {name}: {e}")
                continue

        if self.model is None:
            raise RuntimeError("No MLM model could be loaded.")

    def _load_latin_bert(self):
        from transformers import BertForMaskedLM

        tokenizer = AutoTokenizer.from_pretrained(
            "latincy/latin-bert", trust_remote_code=True
        )
        model = BertForMaskedLM.from_pretrained("latincy/latin-bert")
        return tokenizer, model

    def compute_pseudo_perplexity(self, text, stride=256, max_length=512):
        window_size = max_length - 2
        norm_text = normalize_text(text)
        print(text)
        token_ids = self.tokenizer.encode(norm_text, add_special_tokens=False)
        # print(token_ids)
        cls_id = self.tokenizer.cls_token_id
        sep_id = self.tokenizer.sep_token_id
        mask_id = self.tokenizer.mask_token_id

        total_nll = 0.0
        total_tokens = 0
        for start in range(0, len(token_ids), stride):
            window = token_ids[start : start + window_size]
            if not window:
                break
            input_ids = [cls_id] + window + [sep_id]
            # print(input_ids)
            for i in range(1, len(input_ids) - 1):
                input_ids_masked = input_ids[: i - 1] + [mask_id] + input_ids[i + 1 :]
                # print(input_ids_masked)
                input_tensor = torch.tensor([input_ids_masked], device=self.device)
                with torch.no_grad():
                    masked_tensor = self.model(input_tensor)

                logits = masked_tensor.logits[0, i, :]
                # print(logits)

                log_probs = torch.log_softmax(logits, dim=-1)
                original_id = input_ids[i]
                token_log_prob = log_probs[original_id].item()
                total_nll -= token_log_prob
                total_tokens += 1
        avg_nll = total_nll / total_tokens
        ppl = torch.exp(torch.tensor(avg_nll)).item()

        return ppl


if __name__ == "__main__":
    scorer = PseudoPerplexityScorer()
    phrases = [
        "This is a test for bert_medieval_multilingual",
        "Ceci est un test d'estimation pour du français moderne",
        "qzeomigh qge hgmqohgei hzq ze mzegh i ioqezeiuqzehgqm  i",
    ]
    for text in phrases:
        ppl = scorer.compute_pseudo_perplexity(text=text)
        print(ppl)
