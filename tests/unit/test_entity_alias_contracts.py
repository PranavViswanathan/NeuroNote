from __future__ import annotations

from pydantic import ValidationError
import pytest

from shared.contracts.python.v1.entity_alias import ConfirmEntityAliasRequest


def test_confirm_alias_request_rejects_invalid_fields() -> None:
    with pytest.raises(ValidationError):
        ConfirmEntityAliasRequest(
            alias_text="",
            canonical_entity_id="",
            canonical_name="",
            confidence=1.5,
        )


def test_confirm_alias_request_accepts_valid_fields() -> None:
    payload = ConfirmEntityAliasRequest(
        alias_text="ML",
        canonical_entity_id="concept-machine-learning",
        canonical_name="Machine Learning",
        confidence=0.95,
    )

    assert payload.alias_text == "ML"
    assert payload.confidence == 0.95
