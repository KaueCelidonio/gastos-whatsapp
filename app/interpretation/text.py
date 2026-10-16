"""Normalização de texto para comparação: minúsculas, sem acentos, espaços simples."""

import unicodedata


def strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def normalize(text: str) -> str:
    return " ".join(strip_accents(text).lower().split())
