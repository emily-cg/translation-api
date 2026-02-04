from typing import Optional, Any, Dict, Tuple

import os
import threading

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

SUPPORTED_MODELS: Dict[Tuple[str, str], str] = {
    ("en", "fr"): "Helsinki-NLP/opus-mt-en-fr",
    ("en", "es"): "Helsinki-NLP/opus-mt-en-es",
}
MAX_INPUT_TOKENS = int(os.getenv("MAX_INPUT_TOKENS", "512"))
MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "256"))


class UnsupportedLanguagePairError(ValueError):
    pass


class ModelUnavailableError(RuntimeError):
    pass


class TranslatorService:
    def __init__(self, model_map: Dict[Tuple[str, str], str]):
        self._model_map = model_map
        self._cache: Dict[Tuple[str, str], Tuple[Any, Any]] = {}
        self._lock = threading.Lock()
        self._last_error: Optional[Exception] = None

    def normalize_lang(self, lang: str) -> str:
        return lang.strip().lower()

    def supported_pairs_str(self) -> str:
        pairs = sorted(f"{src}->{tgt}" for src, tgt in self._model_map.keys())
        return ", ".join(pairs)

    def supported_pairs(self) -> Tuple[Tuple[str, str], ...]:
        return tuple(sorted(self._model_map.keys()))

    def _load_pair(self, pair: Tuple[str, str]) -> None:
        model_id = self._model_map[pair]
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_id)
        model.eval()
        self._cache[pair] = (tokenizer, model)

    def load_all(self) -> None:
        with self._lock:
            for pair in self._model_map.keys():
                if pair in self._cache:
                    continue
                try:
                    self._load_pair(pair)
                except OSError as exc:
                    self._last_error = exc
                    raise ModelUnavailableError(
                        "Translation model is unavailable. Download the model and try again."
                    ) from exc
            self._last_error = None

    def translate(self, text: str, source_lang: str, target_lang: str) -> Tuple[str, str]:
        pair = (self.normalize_lang(source_lang), self.normalize_lang(target_lang))
        if pair not in self._model_map:
            raise UnsupportedLanguagePairError(
                f"Supported language pairs: {self.supported_pairs_str()}"
            )

        if pair not in self._cache:
            with self._lock:
                if pair not in self._cache:
                    try:
                        self._load_pair(pair)
                        self._last_error = None
                    except OSError as exc:
                        self._last_error = exc
                        raise ModelUnavailableError(
                            "Translation model is unavailable. Download the model and try again."
                        ) from exc

        tokenizer, model = self._cache[pair]
        with torch.no_grad():
            inputs = tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=MAX_INPUT_TOKENS,
                )
            outputs = model.generate(**inputs, max_new_tokens=MAX_NEW_TOKENS)
        translation = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return translation, self._model_map[pair]

    def is_available(self) -> bool:
        return self._last_error is None

    def unavailable_reason(self) -> Optional[str]:
        if self._last_error is None:
            return None
        return str(self._last_error)

    def model_id_for_pair(self, source_lang: str, target_lang: str) -> Optional[str]:
        pair = (self.normalize_lang(source_lang), self.normalize_lang(target_lang))
        return self._model_map.get(pair)


translator_service = TranslatorService(SUPPORTED_MODELS)
