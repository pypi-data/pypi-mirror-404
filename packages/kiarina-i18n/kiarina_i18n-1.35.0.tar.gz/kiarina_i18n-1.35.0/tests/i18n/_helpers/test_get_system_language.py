from unittest.mock import patch

from kiarina.i18n import get_system_language


def test_get_system_language_from_lang_env():
    """Test language detection from LANG environment variable."""
    with patch.dict("os.environ", {"LANG": "ja_JP.UTF-8"}):
        assert get_system_language() == "ja"


def test_get_system_language_from_lc_all_env():
    """Test language detection from LC_ALL environment variable."""
    with patch.dict("os.environ", {"LC_ALL": "fr_FR.UTF-8"}, clear=True):
        assert get_system_language() == "fr"


def test_get_system_language_from_lc_messages_env():
    """Test language detection from LC_MESSAGES environment variable."""
    with patch.dict("os.environ", {"LC_MESSAGES": "de_DE.UTF-8"}, clear=True):
        assert get_system_language() == "de"


def test_get_system_language_from_language_env():
    """Test language detection from LANGUAGE environment variable."""
    with patch.dict("os.environ", {"LANGUAGE": "es_ES.UTF-8"}, clear=True):
        assert get_system_language() == "es"


def test_get_system_language_priority():
    """Test that LANG has priority over other variables."""
    with patch.dict(
        "os.environ",
        {
            "LANG": "ja_JP.UTF-8",
            "LC_ALL": "fr_FR.UTF-8",
            "LC_MESSAGES": "de_DE.UTF-8",
            "LANGUAGE": "es_ES.UTF-8",
        },
    ):
        assert get_system_language() == "ja"


def test_get_system_language_without_encoding():
    """Test language detection without encoding suffix."""
    with patch.dict("os.environ", {"LANG": "ja_JP"}, clear=True):
        assert get_system_language() == "ja"


def test_get_system_language_simple_code():
    """Test language detection with simple language code."""
    with patch.dict("os.environ", {"LANG": "ja"}, clear=True):
        assert get_system_language() == "ja"


def test_get_system_language_from_locale():
    """Test language detection from locale.getlocale() fallback."""
    with patch.dict("os.environ", {}, clear=True):
        with patch("locale.getlocale", return_value=("ja_JP", "UTF-8")):
            assert get_system_language() == "ja"


def test_get_system_language_from_locale_without_encoding():
    """Test language detection from locale without encoding."""
    with patch.dict("os.environ", {}, clear=True):
        with patch("locale.getlocale", return_value=("fr_FR", None)):
            assert get_system_language() == "fr"


def test_get_system_language_fallback_to_en():
    """Test fallback to 'en' when detection fails."""
    with patch.dict("os.environ", {}, clear=True):
        with patch("locale.getlocale", return_value=(None, None)):
            assert get_system_language() == "en"


def test_get_system_language_empty_env_var():
    """Test handling of empty environment variable."""
    with patch.dict("os.environ", {"LANG": ""}, clear=True):
        with patch("locale.getlocale", return_value=(None, None)):
            assert get_system_language() == "en"


def test_get_system_language_locale_exception():
    """Test fallback when locale.getlocale() raises exception."""
    with patch.dict("os.environ", {}, clear=True):
        with patch("locale.getlocale", side_effect=Exception("Locale error")):
            assert get_system_language() == "en"


def test_get_system_language_case_insensitive():
    """Test that language code is returned in lowercase."""
    with patch.dict("os.environ", {"LANG": "JA_JP.UTF-8"}, clear=True):
        assert get_system_language() == "ja"


def test_get_system_language_complex_format():
    """Test handling of complex locale format."""
    with patch.dict("os.environ", {"LANG": "zh_CN.GB2312"}, clear=True):
        assert get_system_language() == "zh"
