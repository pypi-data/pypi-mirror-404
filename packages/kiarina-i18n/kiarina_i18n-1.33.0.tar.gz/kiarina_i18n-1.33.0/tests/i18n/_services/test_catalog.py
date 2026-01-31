import sys
import tempfile
from pathlib import Path

import pytest

from kiarina.i18n._services.catalog import Catalog


@pytest.fixture
def catalog_instance() -> Catalog:
    """Create a fresh Catalog instance for testing."""
    catalog = Catalog()
    catalog.clear()
    return catalog


def test_catalog_add_from_dict(catalog_instance: Catalog) -> None:
    """Test adding catalog data from dictionary."""
    data = {
        "en": {"app": {"title": "My App"}},
        "ja": {"app": {"title": "マイアプリ"}},
    }

    catalog_instance.add_from_dict(data)

    assert catalog_instance.get_text("en", "app", "title") == "My App"
    assert catalog_instance.get_text("ja", "app", "title") == "マイアプリ"


def test_catalog_add_from_dict_deep_merge(catalog_instance: Catalog) -> None:
    """Test that add_from_dict performs deep merge."""
    # First add
    catalog_instance.add_from_dict(
        {
            "en": {"app": {"title": "My App"}},
        }
    )

    # Second add (should merge, not replace)
    catalog_instance.add_from_dict(
        {
            "en": {"app": {"description": "My Description"}},
            "ja": {"app": {"title": "マイアプリ"}},
        }
    )

    # Both keys should exist
    assert catalog_instance.get_text("en", "app", "title") == "My App"
    assert catalog_instance.get_text("en", "app", "description") == "My Description"
    assert catalog_instance.get_text("ja", "app", "title") == "マイアプリ"


def test_catalog_add_from_file(catalog_instance: Catalog) -> None:
    """Test adding catalog data from YAML file."""
    yaml_content = """
en:
  app:
    title: "My App"
    description: "My Description"
ja:
  app:
    title: "マイアプリ"
    description: "マイ説明"
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        temp_path = f.name

    try:
        catalog_instance.add_from_file(temp_path)

        assert catalog_instance.get_text("en", "app", "title") == "My App"
        assert catalog_instance.get_text("en", "app", "description") == "My Description"
        assert catalog_instance.get_text("ja", "app", "title") == "マイアプリ"
        assert catalog_instance.get_text("ja", "app", "description") == "マイ説明"
    finally:
        Path(temp_path).unlink()


def test_catalog_add_from_file_empty_yaml(catalog_instance: Catalog) -> None:
    """Test adding catalog data from empty YAML file."""
    yaml_content = ""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        temp_path = f.name

    try:
        # Should not raise an error
        catalog_instance.add_from_file(temp_path)

        # Catalog should remain empty
        assert catalog_instance.get_text("en", "app", "title") is None
    finally:
        Path(temp_path).unlink()


def test_catalog_add_from_dir(catalog_instance: Catalog) -> None:
    """Test adding catalog data from directory."""
    temp_dir = Path(tempfile.mkdtemp())

    try:
        # Create YAML files
        (temp_dir / "en.yaml").write_text(
            """
en:
  app:
    title: "My App"
"""
        )
        (temp_dir / "ja.yml").write_text(
            """
ja:
  app:
    title: "マイアプリ"
"""
        )

        # Create subdirectory with more files
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        (subdir / "fr.yaml").write_text(
            """
fr:
  app:
    title: "Mon App"
"""
        )

        # Load from directory
        catalog_instance.add_from_dir(str(temp_dir))

        # Verify all files were loaded
        assert catalog_instance.get_text("en", "app", "title") == "My App"
        assert catalog_instance.get_text("ja", "app", "title") == "マイアプリ"
        assert catalog_instance.get_text("fr", "app", "title") == "Mon App"
    finally:
        import shutil

        shutil.rmtree(temp_dir)


def test_catalog_add_from_dir_not_directory(catalog_instance: Catalog) -> None:
    """Test error handling when path is not a directory."""
    with pytest.raises(NotADirectoryError, match="Not a directory"):
        catalog_instance.add_from_dir("/nonexistent/path")


def test_catalog_add_from_dir_no_yaml_files(catalog_instance: Catalog) -> None:
    """Test error handling when directory has no YAML files."""
    from pathlib import Path

    temp_dir = Path(tempfile.mkdtemp())

    try:
        # Create a file that's not YAML
        (temp_dir / "readme.txt").write_text("Not a YAML file")

        with pytest.raises(FileNotFoundError, match="No YAML files found"):
            catalog_instance.add_from_dir(str(temp_dir))
    finally:
        import shutil

        shutil.rmtree(temp_dir)


def test_catalog_add_from_package_file(catalog_instance: Catalog) -> None:
    """Test adding catalog data from package resource."""
    # Create temporary directory for test package
    temp_dir = Path(tempfile.mkdtemp())
    package_dir = temp_dir / "test_i18n_package"
    package_dir.mkdir()

    # Create __init__.py
    (package_dir / "__init__.py").write_text("")

    # Create catalog file
    catalog_file = package_dir / "translations.yaml"
    catalog_file.write_text(
        """
en:
  app:
    title: "My App"
ja:
  app:
    title: "マイアプリ"
"""
    )

    # Add package to sys.path
    sys.path.insert(0, str(temp_dir))

    try:
        # Load from package resource
        catalog_instance.add_from_package_file("test_i18n_package", "translations.yaml")

        # Verify data was loaded
        assert catalog_instance.get_text("en", "app", "title") == "My App"
        assert catalog_instance.get_text("ja", "app", "title") == "マイアプリ"

    finally:
        # Cleanup
        sys.path.remove(str(temp_dir))
        import shutil

        shutil.rmtree(temp_dir)


def test_catalog_add_from_package_file_not_found(
    catalog_instance: Catalog,
) -> None:
    """Test error handling when package is not found."""
    with pytest.raises(FileNotFoundError, match="Package not found"):
        catalog_instance.add_from_package_file("nonexistent", "file.yaml")


def test_catalog_add_from_package_file_file_not_found(
    catalog_instance: Catalog,
) -> None:
    """Test error handling when file in package is not found."""
    temp_dir = Path(tempfile.mkdtemp())
    package_dir = temp_dir / "test_package"
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text("")

    sys.path.insert(0, str(temp_dir))

    try:
        with pytest.raises(FileNotFoundError, match="Package resource not found"):
            catalog_instance.add_from_package_file("test_package", "nonexistent.yaml")

    finally:
        sys.path.remove(str(temp_dir))
        import shutil

        shutil.rmtree(temp_dir)


def test_catalog_add_from_package_dir(catalog_instance: Catalog) -> None:
    """Test adding catalog data from package directory."""
    # Create temporary directory for test package
    temp_dir = Path(tempfile.mkdtemp())
    package_dir = temp_dir / "test_i18n_package_dir"
    package_dir.mkdir()

    # Create __init__.py
    (package_dir / "__init__.py").write_text("")

    # Create catalog files
    (package_dir / "en.yaml").write_text(
        """
en:
  app:
    title: "My App"
"""
    )
    (package_dir / "ja.yml").write_text(
        """
ja:
  app:
    title: "マイアプリ"
"""
    )

    # Add package to sys.path
    sys.path.insert(0, str(temp_dir))

    try:
        # Load from package directory
        catalog_instance.add_from_package_dir("test_i18n_package_dir")

        # Verify data was loaded
        assert catalog_instance.get_text("en", "app", "title") == "My App"
        assert catalog_instance.get_text("ja", "app", "title") == "マイアプリ"

    finally:
        # Cleanup
        sys.path.remove(str(temp_dir))
        import shutil

        shutil.rmtree(temp_dir)


def test_catalog_add_from_package_dir_with_empty_yaml(
    catalog_instance: Catalog,
) -> None:
    """Test adding catalog data from package directory with empty YAML file."""
    # Create temporary directory for test package
    temp_dir = Path(tempfile.mkdtemp())
    package_dir = temp_dir / "test_i18n_package_empty"
    package_dir.mkdir()

    # Create __init__.py
    (package_dir / "__init__.py").write_text("")

    # Create empty YAML file
    (package_dir / "empty.yaml").write_text("")

    # Create valid YAML file
    (package_dir / "en.yaml").write_text(
        """
en:
  app:
    title: "My App"
"""
    )

    # Add package to sys.path
    sys.path.insert(0, str(temp_dir))

    try:
        # Should not raise an error
        catalog_instance.add_from_package_dir("test_i18n_package_empty")

        # Verify valid data was loaded
        assert catalog_instance.get_text("en", "app", "title") == "My App"

    finally:
        # Cleanup
        sys.path.remove(str(temp_dir))
        import shutil

        shutil.rmtree(temp_dir)


def test_catalog_add_from_package_dir_not_found(
    catalog_instance: Catalog,
) -> None:
    """Test error handling when package is not found."""
    with pytest.raises(FileNotFoundError, match="Package not found"):
        catalog_instance.add_from_package_dir("nonexistent_package_12345")


def test_catalog_clear(catalog_instance: Catalog) -> None:
    """Test clearing catalog data."""
    catalog_instance.add_from_dict(
        {
            "en": {"app": {"title": "My App"}},
        }
    )

    assert catalog_instance.get_text("en", "app", "title") == "My App"

    catalog_instance.clear()

    assert catalog_instance.get_text("en", "app", "title") is None


def test_catalog_get_text_not_found(catalog_instance: Catalog) -> None:
    """Test get_text returns None when translation is not found."""
    assert catalog_instance.get_text("en", "app", "nonexistent") is None
    assert catalog_instance.get_text("nonexistent", "app", "title") is None
    assert catalog_instance.get_text("en", "nonexistent", "title") is None


def test_catalog_singleton_behavior() -> None:
    """Test that catalog behaves as a singleton at module level."""
    from kiarina.i18n._services.catalog import catalog as catalog1
    from kiarina.i18n._services.catalog import catalog as catalog2

    # Should be the same instance
    assert catalog1 is catalog2

    # Clear for clean state
    catalog1.clear()

    # Add data via catalog1
    catalog1.add_from_dict(
        {
            "en": {"test": {"key": "value"}},
        }
    )

    # Should be accessible via catalog2
    assert catalog2.get_text("en", "test", "key") == "value"

    # Clear for next tests
    catalog1.clear()
