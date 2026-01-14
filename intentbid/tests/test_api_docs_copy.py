from intentbid.app.api.api_docs import API_DOCUMENTATION


def _doc_by_slug(slug):
    for doc in API_DOCUMENTATION:
        if doc["slug"] == slug:
            return doc
    raise AssertionError(f"Missing API doc slug: {slug}")


def test_api_docs_use_aggregator_language():
    rfo_create = _doc_by_slug("rfo-create")
    offer_create = _doc_by_slug("offer-create")
    rfo_best = _doc_by_slug("rfo-best")

    assert "buyer request" in rfo_create["description"]["en"].lower()
    assert "vendor offer" in offer_create["description"]["en"].lower()
    assert "vendor offer" in rfo_best["description"]["en"].lower()


def test_api_docs_include_list_and_profile_placeholders():
    slugs = {doc["slug"] for doc in API_DOCUMENTATION}

    expected = {
        "rfo-list",
        "buyer-rfo-list",
        "vendor-offers-list",
        "vendor-profile-get",
        "vendor-profile-update",
    }

    missing = expected - slugs
    assert not missing, f"Missing API doc placeholders: {sorted(missing)}"
