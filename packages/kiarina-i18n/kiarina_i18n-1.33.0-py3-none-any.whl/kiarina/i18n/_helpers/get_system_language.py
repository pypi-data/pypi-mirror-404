import locale
import os


def get_system_language() -> str:
    """
    Get the system's default language code.

    This function attempts to detect the system's language preference by checking:
    1. Environment variables (LANG, LC_ALL, LC_MESSAGES, LANGUAGE)
    2. locale.getlocale() as fallback
    3. Returns "en" if detection fails

    Returns:
        Language code (e.g., "en", "ja", "fr")

    Example:
        ```python
        from kiarina.i18n import get_system_language, get_translator

        # Automatically use system language
        language = get_system_language()
        t = get_translator(language, "app.greeting")
        print(t("hello", name="World"))
        ```
    """
    # First, try environment variables (most reliable for runtime changes)
    try:
        for env_var in ("LANG", "LC_ALL", "LC_MESSAGES", "LANGUAGE"):
            lang = os.environ.get(env_var)
            if lang:
                # Extract language code (e.g., "ja_JP.UTF-8" -> "ja")
                language_code = lang.split("_")[0].split(".")[0]
                if language_code:
                    return language_code.lower()
    except Exception:  # pragma: no cover
        pass

    # Fallback: try locale.getlocale()
    try:
        current_locale = locale.getlocale()[0]

        if current_locale:
            # Extract language code (e.g., "ja_JP" -> "ja")
            language_code = current_locale.split("_")[0]
            return language_code.lower()
    except Exception:  # pragma: no cover
        pass

    # Final fallback
    return "en"
