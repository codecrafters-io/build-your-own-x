"""
Character-level tokenizer.

Maps every unique character in the training corpus to an integer id.
Simple, requires no external libraries, and good enough for a tiny LLM.
"""


class CharTokenizer:
    def __init__(self, text: str):
        chars = sorted(set(text))
        self.vocab_size = len(chars)
        self._stoi = {ch: i for i, ch in enumerate(chars)}
        self._itos = {i: ch for i, ch in enumerate(chars)}

    def encode(self, text: str) -> list[int]:
        return [self._stoi[ch] for ch in text]

    def decode(self, ids: list[int]) -> str:
        return "".join(self._itos[i] for i in ids)
