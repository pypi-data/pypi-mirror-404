from kiarina.i18n import catalog, get_translator


def test_get_translator_basic(sample_catalog):
    """Test get_translator function."""
    catalog.add_from_dict(sample_catalog)

    t = get_translator("en", "app.greeting")
    assert t("hello", name="World") == "Hello, World!"


def test_get_translator_creates_new_instances(sample_catalog):
    """Test that get_translator creates new instances (no caching)."""
    catalog.add_from_dict(sample_catalog)

    t1 = get_translator("en", "app.greeting")
    t2 = get_translator("en", "app.greeting")

    assert t1 is not t2
    assert t1("hello", name="World") == t2("hello", name="World")


def test_get_translator_different_languages(sample_catalog):
    """Test get_translator with different languages."""
    catalog.add_from_dict(sample_catalog)

    t_en = get_translator("en", "app.greeting")
    t_ja = get_translator("ja", "app.greeting")

    assert t_en("hello", name="World") == "Hello, World!"
    assert t_ja("hello", name="世界") == "こんにちは、世界!"


def test_get_translator_different_scopes(sample_catalog):
    """Test get_translator with different scopes."""
    catalog.add_from_dict(sample_catalog)

    t_greeting = get_translator("en", "app.greeting")
    t_error = get_translator("en", "app.error")

    assert t_greeting("hello", name="World") == "Hello, World!"
    assert t_error("not_found") == "Not found"
