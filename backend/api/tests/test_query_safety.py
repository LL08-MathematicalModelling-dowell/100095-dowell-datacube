import pytest

from api.infrastructure.query_safety import (
    assert_mutating_filter_allowed,
    prepare_update_document,
    plain_fields_for_partial_update,
    validate_filter,
)


def test_prepare_update_document_plain_fields():
    doc, sample = prepare_update_document({"status": "active"})
    assert doc == {"$set": {"status": "active"}}
    assert sample == {"status": "active"}


def test_prepare_update_document_operator_passthrough():
    payload = {"$set": {"status": "active"}, "$inc": {"n": 1}}
    doc, sample = prepare_update_document(payload)
    assert doc == payload
    assert sample == {"status": "active"}


def test_reject_forbidden_filter_operator():
    with pytest.raises(ValueError, match="not allowed"):
        validate_filter({"$where": "true"})


def test_mutating_filter_requires_id_for_single_update():
    with pytest.raises(ValueError, match="_id"):
        assert_mutating_filter_allowed({"status": "active"}, update_many=False)


def test_mutating_filter_allows_broad_when_update_many():
    assert_mutating_filter_allowed({"status": "active"}, update_many=True)


def test_plain_fields_from_set_only():
    fields = plain_fields_for_partial_update({"$set": {"a": 1}})
    assert fields == {"a": 1}
