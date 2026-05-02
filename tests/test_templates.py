"""Tests des templates de rédaction."""

from __future__ import annotations

import pytest

from app.templates import (
    TEMPLATES,
    TONE_HINTS,
    Tone,
    build_messages,
    get_template,
    list_templates,
)


def test_list_templates_non_empty() -> None:
    items = list_templates()
    assert len(items) >= 6
    for item in items:
        assert {"id", "label", "description"} <= set(item.keys())
        assert all(isinstance(v, str) and v for v in item.values())


def test_get_template_known() -> None:
    t = get_template("email_relance")
    assert t.id == "email_relance"
    assert "relance" in t.label.lower()


def test_get_template_unknown_raises() -> None:
    with pytest.raises(KeyError):
        get_template("template_inexistant")


def test_tone_hints_cover_all_tones() -> None:
    assert set(TONE_HINTS.keys()) == {"formel", "neutre", "direct"}
    for hint in TONE_HINTS.values():
        assert hint.strip()


@pytest.mark.parametrize("template_id", list(TEMPLATES.keys()))
@pytest.mark.parametrize("tone", ["formel", "neutre", "direct"])
def test_build_messages_shape(template_id: str, tone: Tone) -> None:
    messages = build_messages(template_id, "Contexte de test pour BoostIA.", tone)
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    # Le contexte doit apparaître dans le message utilisateur
    assert "Contexte de test pour BoostIA." in messages[1]["content"]
    # Le tone hint correspondant doit être injecté
    assert TONE_HINTS[tone] in messages[1]["content"]


def test_build_messages_strips_context() -> None:
    messages = build_messages("email_relance", "   contexte avec espaces   ", "neutre")
    assert "contexte avec espaces" in messages[1]["content"]
    # Pas de chaîne avec espaces de bord
    assert "   contexte avec espaces   " not in messages[1]["content"]


def test_build_messages_invalid_tone_raises() -> None:
    with pytest.raises(ValueError):
        build_messages("email_relance", "ctx", "informel")  # type: ignore[arg-type]


def test_build_messages_invalid_template_raises() -> None:
    with pytest.raises(KeyError):
        build_messages("not_a_template", "ctx", "neutre")
