from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path

import yaml

from .._types.i18n_key import I18nKey
from .._types.i18n_scope import I18nScope
from .._types.language import Language


class Catalog:
    """Service for managing translation catalog.

    This class provides methods to add catalog data from dictionaries or YAML files,
    and retrieve translation text for a given language, scope, and key.

    Example:
        >>> from kiarina.i18n import catalog
        >>>
        >>> # Add from dict
        >>> catalog.add_from_dict({
        ...     "en": {"app": {"title": "My App"}},
        ...     "ja": {"app": {"title": "マイアプリ"}},
        ... })
        >>>
        >>> # Add from file
        >>> catalog.add_from_file("translations.yaml")
        >>>
        >>> # Get text
        >>> catalog.get_text("ja", "app", "title")
        'マイアプリ'
        >>>
        >>> # Clear all
        >>> catalog.clear()
    """

    def __init__(self) -> None:
        self._data: dict[Language, dict[I18nScope, dict[I18nKey, str]]] = {}

    def add_from_dict(
        self,
        data: dict[Language, dict[I18nScope, dict[I18nKey, str]]],
    ) -> None:
        """Add catalog data from dictionary (deep merge).

        Args:
            data: Catalog data to add.

        Example:
            >>> catalog.add_from_dict({
            ...     "en": {"app": {"title": "My App"}},
            ...     "ja": {"app": {"title": "マイアプリ"}},
            ... })
        """
        self._data = self._deep_merge(self._data, data)

    def add_from_file(self, file_path: str) -> None:
        """Add catalog data from YAML file (deep merge).

        Args:
            file_path: Path to YAML file containing catalog data.

        Example:
            >>> catalog.add_from_file("translations.yaml")
        """
        with open(file_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

            if data is not None:
                self.add_from_dict(data)

    def add_from_dir(self, dir_path: str) -> None:
        """Add catalog data from all YAML files in directory (deep merge).

        Recursively loads all *.yaml and *.yml files in the directory.

        Args:
            dir_path: Path to directory containing YAML files.

        Example:
            >>> catalog.add_from_dir("translations/")
        """
        dir_path_obj = Path(dir_path)

        if not dir_path_obj.is_dir():
            raise NotADirectoryError(f"Not a directory: {dir_path}")

        # Find all YAML files recursively
        yaml_files = sorted(dir_path_obj.rglob("*.yaml")) + sorted(
            dir_path_obj.rglob("*.yml")
        )

        if not yaml_files:
            raise FileNotFoundError(f"No YAML files found in directory: {dir_path}")

        for yaml_file in yaml_files:
            self.add_from_file(str(yaml_file))

    def add_from_package_file(self, package: str, file_path: str) -> None:
        """Add catalog data from package resource YAML file (deep merge).

        Args:
            package: Package name (e.g., "myapp.i18n")
            file_path: Path to YAML file within the package (e.g., "catalogs/en.yaml")

        Example:
            >>> catalog.add_from_package_file("myapp.i18n", "catalogs/en.yaml")
        """
        try:
            resource_files = files(package)
            resource_file = resource_files.joinpath(file_path)

            if not resource_file.is_file():
                raise FileNotFoundError(
                    f"Package resource not found: {package}/{file_path}"
                )

            content = resource_file.read_text(encoding="utf-8")
            data = yaml.safe_load(content)

            if data is not None:
                self.add_from_dict(data)

        except ModuleNotFoundError as e:
            raise FileNotFoundError(
                f"Package not found: '{package}' does not exist"
            ) from e

    def add_from_package_dir(self, package: str) -> None:
        """Add catalog data from all YAML files in package directory (deep merge).

        Loads all *.yaml and *.yml files directly under the package directory.
        Does not search subdirectories recursively.

        Args:
            package: Package name (e.g., "myapp.i18n" or "myapp.i18n.catalogs")

        Example:
            >>> # Load from package
            >>> catalog.add_from_package_dir("myapp.i18n")
            >>>
            >>> # Load from subpackage
            >>> catalog.add_from_package_dir("myapp.i18n.catalogs")
        """
        try:
            resource_dir = files(package)

            # Find all YAML files in the directory (not recursive)
            yaml_files: list[Traversable] = []

            try:
                for item in resource_dir.iterdir():
                    if item.is_file() and item.name.endswith((".yaml", ".yml")):
                        yaml_files.append(item)

            except (FileNotFoundError, OSError):
                # Package directory doesn't exist or can't be accessed
                raise FileNotFoundError(f"Package directory not accessible: {package}")

            if not yaml_files:
                raise FileNotFoundError(f"No YAML files found in package: {package}")

            # Sort for consistent ordering
            yaml_files.sort(key=lambda p: str(p))

            for yaml_file in yaml_files:
                content = yaml_file.read_text(encoding="utf-8")
                data = yaml.safe_load(content)

                if data is not None:
                    self.add_from_dict(data)

        except ModuleNotFoundError as e:
            raise FileNotFoundError(
                f"Package not found: '{package}' does not exist"
            ) from e

    def clear(self) -> None:
        """Clear all catalog data.

        Example:
            >>> catalog.clear()
        """
        self._data = {}

    def get_text(
        self,
        language: Language,
        scope: I18nScope,
        key: I18nKey,
    ) -> str | None:
        """Get translation text from catalog.

        Args:
            language: Target language.
            scope: Translation scope.
            key: Translation key.

        Returns:
            Translation text if found, None otherwise.

        Example:
            >>> catalog.get_text("ja", "app", "title")
            'マイアプリ'
        """
        return self._data.get(language, {}).get(scope, {}).get(key)

    def _deep_merge(
        self,
        base: dict[Language, dict[I18nScope, dict[I18nKey, str]]],
        update: dict[Language, dict[I18nScope, dict[I18nKey, str]]],
    ) -> dict[Language, dict[I18nScope, dict[I18nKey, str]]]:
        """Deep merge two catalog dictionaries.

        Args:
            base: Base dictionary.
            update: Dictionary to merge into base.

        Returns:
            Merged dictionary.
        """
        result = base.copy()

        for language, scopes in update.items():
            if language not in result:
                result[language] = {}

            for scope, keys in scopes.items():
                if scope not in result[language]:
                    result[language][scope] = {}

                result[language][scope].update(keys)

        return result


# Module-level singleton instance
catalog = Catalog()
