# Changelog

All notable changes to kiarina-i18n will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.33.0] - 2026-01-31

### Changed
- No changes

## [1.32.0] - 2026-01-30

### Changed
- No changes

## [1.31.1] - 2026-01-29

### Changed
- No changes

## [1.31.0] - 2026-01-29

### Changed
- No changes

## [1.30.0] - 2026-01-27

### Changed
- No changes

## [1.29.0] - 2026-01-16

### Changed
- No changes

## [1.28.0] - 2026-01-16

### Changed
- No changes

## [1.27.0] - 2026-01-12

### Changed
- No changes

## [1.26.0] - 2026-01-09

### Added
- `get_system_language()` helper function for automatic system language detection
  - Detects language from environment variables (LANG, LC_ALL, LC_MESSAGES, LANGUAGE)
  - Falls back to locale.getlocale() if environment variables are not set
  - Returns "en" as final fallback

## [1.25.1] - 2026-01-08

### Changed
- No changes

## [1.25.0] - 2026-01-08

### Added
- Added `add_from_dir()` method to `Catalog` for loading catalogs from directories
- Added `add_from_package()` method to `Catalog` for loading catalogs from package resources

## [1.24.0] - 2026-01-08

### Changed
- **BREAKING**: Catalog management has been completely redesigned
  - Removed `I18nSettings.catalog` and `I18nSettings.catalog_file` fields
  - Removed `clear_cache()` helper function (use `catalog.clear()` instead)
  - Removed `_types/catalog.py` TypeAlias
  - Removed `_operations/get_catalog.py` and `_operations/load_catalog_file.py`
  - Added `Catalog` service class for managing translation data
  - Added `catalog.add_from_dict()` and `catalog.add_from_file()` methods
  - Catalog management is now completely user-controlled
  - Migration guide:
    - Before: `settings_manager.user_config = {"catalog": {...}}` and `clear_cache()`
    - After: `catalog.add_from_dict({...})` and `catalog.clear()`
  - This change reduces code by 248 lines and makes catalog management more explicit

## [1.23.0] - 2026-01-06

### Changed
- No changes

## [1.22.1] - 2026-01-06

### Changed
- No changes

## [1.22.0] - 2026-01-05

### Added
- **kiarina-i18n_pydantic**: Support for translating nested I18n models in `list[I18n]` and `dict[str, I18n]` fields
  - Nested I18n models are automatically translated recursively
  - Explicit scope inheritance: when parent scope is explicitly provided, it overrides nested model's own scope
  - Auto scope detection: when parent scope is not provided, nested models use their own `_scope`

## [1.21.1] - 2026-01-05

### Fixed
- **kiarina-i18n_pydantic**: Fixed bug where `default_factory` was lost in `translate_pydantic_model()` during field translation
  - Changed from manual attribute copying to `deepcopy` for complete FieldInfo preservation
  - All field attributes (default_factory, metadata, examples, etc.) are now correctly preserved

## [1.21.0] - 2025-12-30

### Changed
- No changes

## [1.20.1] - 2025-12-25

### Changed
- **Performance**: Optimized caching strategy to only cache file I/O operations
  - Removed `lru_cache` from `get_catalog()` and `get_translator()`
  - Added `load_catalog_file()` operation with caching for file loading only
  - Settings changes are now reflected immediately without requiring `clear_cache()`
  - `clear_cache()` now only clears the file loading cache

## [1.20.0] - 2025-12-19

### Removed
- **BREAKING**: Removed `create_pydantic_schema()` function from `kiarina.i18n_pydantic`
  - Use `I18n` subclass with `Field(description=...)` instead
  - Example: `class ArgsSchema(I18n, scope="tool.args"): name: str = Field(description="Name")`
  - Then use `translate_pydantic_model()` to translate at runtime

## [1.19.0] - 2025-12-19

### Added
- `kiarina.i18n_pydantic` subpackage with `create_pydantic_schema()` function for creating translated Pydantic model schemas
- Support for translating model docstrings, field descriptions, and field titles in Pydantic schemas
- Comprehensive test coverage for `create_pydantic_schema()` with various model configurations

## [1.18.2] - 2025-12-17

### Added
- `translate_pydantic_model()` now translates model `__doc__` (docstring) in addition to field descriptions
  - Use `__doc__` key in catalog to provide translated docstring
  - Falls back to original docstring if translation is missing

## [1.18.1] - 2025-12-16

### Added
- `clear_cache()` helper function for i18n cache management

## [1.18.0] - 2025-12-16

### Added
- `translate_pydantic_model()` function to translate Pydantic model field descriptions for LLM tool schemas
- `get_catalog()` helper function to get translation catalog independently for custom translation logic
- `translate_pydantic_model()` now supports omitting `scope` parameter when translating `I18n` subclasses (automatically uses `model._scope`)

### Changed
- **BREAKING**: `I18n` class now uses `scope` as a class parameter instead of an instance field
  - Old: `class MyI18n(I18n): scope: str = "my.module"`
  - New: `class MyI18n(I18n, scope="my.module")` or `class MyI18n(I18n)` (auto-generated)
  - This allows `scope` to be used as a regular translation key
  - Internal `_scope` attribute stores the scope value
  - If scope is not provided, it's automatically generated from module and class name
    - Example: `my_app.i18n.UserProfileI18n` → `my_app.i18n.UserProfileI18n`

## [1.17.0] - 2025-12-15

### Added
- `I18n` base class for type-safe translation definitions with Pydantic validation
- `get_i18n()` helper function to get translated instances with full type safety
- Class-based API for better IDE support and auto-completion
- Immutable translation instances (frozen=True) to prevent accidental modifications
- Self-documenting translation keys using class field definitions
- Automatic fallback to default values when translations are missing

### Changed
- Reorganized test files by target module (_helpers/, _models/)
- Converted class-based tests to function-based tests
- Added pytest fixtures for cache management in tests

## [1.16.0] - 2025-12-15

### Added
- Initial release of kiarina-i18n package
- `Translator` class for translation with fallback support
- `get_translator()` function with caching
- Template variable substitution using Python's string.Template
- Configuration management using pydantic-settings-manager
- Support for loading catalog from YAML file
- Type definitions for Language, I18nScope, I18nKey, and Catalog
