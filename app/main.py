"""Ponto de entrada da API. Rode com: uvicorn app.main:app --reload"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.channels.whatsapp.router import router as whatsapp_router
from app.config import get_settings
from app.dependencies import Container

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def create_app(container: Container | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.container = container or Container.from_settings(get_settings())
        yield
        await app.state.container.aclose()

    app = FastAPI(
        title="Assistente de Gastos pelo WhatsApp",
        description="Registra e consulta gastos pessoais por mensagens de texto.",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(whatsapp_router)

    @app.get("/health", tags=["infra"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
