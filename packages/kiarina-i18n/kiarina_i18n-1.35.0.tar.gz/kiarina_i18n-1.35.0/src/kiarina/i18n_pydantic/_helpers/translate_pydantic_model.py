from copy import deepcopy
from typing import Any, TypeVar, get_args, get_origin, overload

from pydantic import BaseModel, create_model

from ...i18n._helpers.get_translator import get_translator
from ...i18n._models.i18n import I18n

T = TypeVar("T", bound=BaseModel)


@overload
def translate_pydantic_model(
    model: type[T],
    language: str,
    scope: str,
) -> type[T]: ...


@overload
def translate_pydantic_model(
    model: type[I18n],
    language: str,
    scope: None = None,
) -> type[I18n]: ...


def translate_pydantic_model(
    model: type[T],
    language: str,
    scope: str | None = None,
) -> type[T]:
    """
    Translate Pydantic model field descriptions.

    This function creates a new model class with translated field descriptions
    while preserving all other field attributes and model configuration.

    Args:
        model: Pydantic model class to translate
        language: Target language code (e.g., "ja", "en")
        scope: Translation scope (e.g., "hoge.fields").
               If model is an I18n subclass and scope is None, uses model._scope.

    Returns:
        New model class with translated field descriptions

    Example:
        ```python
        # With explicit scope
        from pydantic import BaseModel, Field
        from kiarina.i18n import translate_pydantic_model, settings_manager

        class Hoge(BaseModel):
            name: str = Field(description="Your Name")
            age: int = Field(description="Your Age")

        # Configure catalog
        settings_manager.user_config = {
            "catalog": {
                "ja": {
                    "hoge.fields": {
                        "name": "あなたの名前",
                        "age": "あなたの年齢",
                    }
                }
            }
        }

        # Translate model
        HogeJa = translate_pydantic_model(Hoge, "ja", "hoge.fields")
        print(HogeJa.model_fields["name"].description)  # "あなたの名前"

        # With I18n subclass (scope auto-detected)
        from kiarina.i18n import I18n

        class HogeI18n(I18n, scope="hoge.fields"):
            name: str = "Your Name"
            age: str = "Your Age"

        HogeI18nJa = translate_pydantic_model(HogeI18n, "ja")
        print(HogeI18nJa.model_fields["name"].description)  # "あなたの名前"
        ```
    """
    # Keep track of the original scope argument for nested model translation
    nested_scope = scope

    # Auto-detect scope from I18n subclass if not provided
    if scope is None:
        if issubclass(model, I18n):
            scope = model._scope
        else:
            raise ValueError(
                "scope parameter is required when model is not an I18n subclass"
            )

    translator = get_translator(language, scope)

    # Translate __doc__ (use original as fallback)
    original_doc = model.__doc__ or ""
    translated_doc = translator("__doc__", default=original_doc)

    # Build new fields with translated descriptions
    new_fields: dict[str, Any] = {}

    for field_name, field_info in model.model_fields.items():
        # Translate description (use original as fallback)
        original_desc = field_info.description or ""
        translated_desc = translator(field_name, default=original_desc)

        # Create a deep copy of the field info to preserve all attributes
        new_field_info = deepcopy(field_info)

        # Update only the description
        new_field_info.description = translated_desc

        # Check if field type contains nested I18n models and translate them
        # Pass the original scope argument (None = use nested model's _scope)
        translated_annotation = _translate_nested_model(
            field_info.annotation, language, nested_scope
        )

        new_fields[field_name] = (translated_annotation, new_field_info)

    # Create new model with translated fields
    # Preserve model config
    translated_model = create_model(
        model.__name__,
        __config__=model.model_config,
        __doc__=translated_doc,
        __base__=model.__base__,
        __module__=model.__module__,
        **new_fields,
    )

    return translated_model  # type: ignore


def _translate_nested_model(
    annotation: Any,
    language: str,
    scope: str | None,
) -> Any:
    """
    Translate nested I18n models in type annotations.

    Supports:
    - list[I18n]
    - dict[str, I18n]

    Args:
        annotation: Type annotation to check and translate
        language: Target language code
        scope: Translation scope to use for nested models.
               If None, nested I18n models will use their own _scope.
               If provided, overrides nested model's _scope (scope inheritance).

    Returns:
        Translated type annotation if nested I18n model found, otherwise original annotation
    """
    origin = get_origin(annotation)
    args = get_args(annotation)

    # Check for list[I18n]
    if origin is list and len(args) == 1:
        inner_type = args[0]
        if isinstance(inner_type, type) and issubclass(inner_type, I18n):
            # Pass scope to nested model (None = use nested model's _scope)
            translated_inner = translate_pydantic_model(inner_type, language, scope)
            return list[translated_inner]  # type: ignore

    # Check for dict[str, I18n]
    if origin is dict and len(args) == 2:
        key_type, value_type = args
        if (
            key_type is str
            and isinstance(value_type, type)
            and issubclass(value_type, I18n)
        ):
            # Pass scope to nested model (None = use nested model's _scope)
            translated_value = translate_pydantic_model(value_type, language, scope)
            return dict[str, translated_value]  # type: ignore

    # Return original annotation if not a supported nested type
    return annotation
