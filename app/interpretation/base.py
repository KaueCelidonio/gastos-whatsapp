"""Contrato de qualquer interpretador de mensagens (por regras hoje, por IA amanhã)."""

from abc import ABC, abstractmethod

from app.interpretation.intents import Intent


class MessageInterpreter(ABC):
    @abstractmethod
    def interpret(self, text: str) -> Intent:
        """Transforma o texto livre do usuário em uma intenção."""
