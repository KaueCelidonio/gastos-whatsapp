import json

from app.config import BASE_DIR, Settings


def test_settings_defaults(monkeypatch):
    for var in ("DATABASE_URL", "TIMEZONE", "CATEGORIES_FILE"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr("app.config.load_dotenv", lambda *a, **k: None)

    settings = Settings.from_env()

    assert settings.database_url.startswith("sqlite")
    assert settings.timezone.key == "America/Sao_Paulo"
    assert settings.categories_file == BASE_DIR / "config" / "categorias.json"


def test_categories_file_is_valid_json():
    data = json.loads((BASE_DIR / "config" / "categorias.json").read_text(encoding="utf-8"))
    assert data["fallback"] == "Outros"
    assert "Alimentação" in data["categorias"]
