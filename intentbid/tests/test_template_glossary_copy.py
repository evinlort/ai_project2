from pathlib import Path


def _assert_terms_in_templates(template_dir: Path, buyer_term: str, offer_term: str) -> None:
    for path in template_dir.glob("*.html"):
        contents = path.read_text(encoding="utf-8")
        assert buyer_term in contents, f"Missing buyer term in {path.name}"
        assert offer_term in contents, f"Missing offer term in {path.name}"


def test_vendor_templates_include_aggregator_terms():
    repo_root = Path(__file__).resolve().parents[2]
    template_dir = repo_root / "intentbid" / "app" / "templates"

    _assert_terms_in_templates(template_dir, "Buyer request (RFO)", "Vendor offer")


def test_buyer_templates_include_aggregator_terms():
    repo_root = Path(__file__).resolve().parents[2]
    template_dir = repo_root / "intentbid" / "app" / "templates" / "buyer"

    _assert_terms_in_templates(template_dir, "Buyer request (RFO)", "Vendor offer")


def test_ru_templates_include_aggregator_terms():
    repo_root = Path(__file__).resolve().parents[2]
    template_dir = repo_root / "intentbid" / "app" / "templates" / "ru"

    _assert_terms_in_templates(template_dir, "Запрос покупателя (RFO)", "Оффер продавца")
