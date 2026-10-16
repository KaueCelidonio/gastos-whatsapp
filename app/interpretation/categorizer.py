"""Classificação de gastos em categorias a partir de palavras-chave."""

from __future__ import annotations

import json
from pathlib import Path

from app.interpretation.text import normalize


class Categorizer:
    def __init__(
        self, keywords_by_category: dict[str, list[str]], fallback: str = "Outros"
    ) -> None:
        self.fallback = fallback
        self._categories = list(keywords_by_category)
        self._keyword_to_category: dict[str, str] = {}
        for category, keywords in keywords_by_category.items():
            for keyword in keywords:
                self._keyword_to_category.setdefault(normalize(keyword), category)

    @classmethod
    def from_json(cls, path: Path) -> Categorizer:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(data["categorias"], data.get("fallback", "Outros"))

    @property
    def categories(self) -> list[str]:
        """Todas as categorias, com a categoria padrão por último."""
        return [*self._categories, self.fallback]

    def categorize(self, description: str) -> str:
        """Primeira palavra da descrição que for palavra-chave define a categoria."""
        words = normalize(description).split()
        for size in (3, 2, 1):  # palavras-chave compostas ("plano de saude") têm prioridade
            for i in range(len(words) - size + 1):
                phrase = " ".join(words[i : i + size])
                if phrase in self._keyword_to_category:
                    return self._keyword_to_category[phrase]
        return self.fallback

    def has_keyword(self, description: str) -> bool:
        return self.categorize(description) != self.fallback

    def find_category(self, name: str) -> str | None:
        """Encontra uma categoria pelo nome, ignorando maiúsculas e acentos."""
        wanted = normalize(name)
        for category in self.categories:
            if normalize(category) == wanted:
                return category
        return None
