import pytest

from app.interpretation.categorizer import Categorizer


@pytest.mark.parametrize(
    ("description", "category"),
    [
        ("almoço", "Alimentação"),
        ("Janta com amigos", "Alimentação"),
        ("ifood", "Alimentação"),
        ("uber", "Transporte"),
        ("99", "Transporte"),
        ("Ônibus", "Transporte"),
        ("gasolina no posto", "Transporte"),
        ("mercado", "Mercado"),
        ("atacadao", "Mercado"),
        ("conta de luz", "Moradia"),
        ("aluguel", "Moradia"),
        ("Farmácia", "Saúde"),
        ("consulta", "Saúde"),
        ("cinema", "Lazer"),
        ("Netflix", "Assinaturas"),
        ("presente da mãe", "Outros"),
    ],
)
def test_categorize(categorizer, description, category):
    assert categorizer.categorize(description) == category


def test_keywords_match_whole_words_only(categorizer):
    # "bar" não pode casar dentro de "barbearia"
    assert categorizer.categorize("barbearia") == "Outros"


def test_multi_word_keyword_has_priority():
    categorizer = Categorizer({"Saúde": ["plano de saúde"], "Outros gastos": ["plano"]})
    assert categorizer.categorize("plano de saude") == "Saúde"


def test_categories_lists_fallback_last(categorizer):
    assert categorizer.categories[0] == "Alimentação"
    assert categorizer.categories[-1] == "Outros"


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("alimentação", "Alimentação"),
        ("ALIMENTACAO", "Alimentação"),
        ("saude", "Saúde"),
        ("outros", "Outros"),
        ("viagens", None),
    ],
)
def test_find_category(categorizer, name, expected):
    assert categorizer.find_category(name) == expected
