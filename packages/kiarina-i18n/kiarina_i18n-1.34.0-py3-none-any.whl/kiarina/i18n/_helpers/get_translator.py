from .._models.translator import Translator
from .._services.catalog import catalog
from .._settings import settings_manager
from .._types.i18n_scope import I18nScope
from .._types.language import Language


def get_translator(language: Language, scope: I18nScope) -> Translator:
    """Get a translator for the specified language and scope.

    Args:
        language: Target language for translation.
        scope: Scope for translation keys (e.g., "kiarina.app.greeting").

    Returns:
        Translator instance configured for the specified language and scope.

    Example:
        >>> from kiarina.i18n import catalog, get_translator
        >>> catalog.add_from_dict({
        ...     "ja": {"app.greeting": {"hello": "こんにちは、$name!"}}
        ... })
        >>> t = get_translator("ja", "app.greeting")
        >>> t("hello", name="World")
        'こんにちは、World!'
    """
    settings = settings_manager.settings
    return Translator(
        catalog=catalog,
        language=language,
        scope=scope,
        fallback_language=settings.default_language,
    )
