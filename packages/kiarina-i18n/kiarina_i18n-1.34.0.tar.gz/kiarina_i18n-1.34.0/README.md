# kiarina-i18n

Simple internationalization (i18n) utilities for Python applications.

## Purpose

`kiarina-i18n` provides a lightweight and straightforward approach to internationalization in Python applications.
It focuses on simplicity and predictability, avoiding complex grammar rules or plural forms.

For applications requiring advanced features like plural forms or complex localization,
consider using established tools like `gettext`.

## Installation

```bash
pip install kiarina-i18n
```

## Quick Start

### Basic Usage (Functional API)

```python
from kiarina.i18n import catalog, get_translator

# Configure the catalog
catalog.add_from_dict({
    "en": {
        "app.greeting": {
            "hello": "Hello, $name!",
            "goodbye": "Goodbye!"
        }
    },
    "ja": {
        "app.greeting": {
            "hello": "こんにちは、$name!",
            "goodbye": "さようなら!"
        }
    }
})

# Get a translator
t = get_translator("ja", "app.greeting")

# Translate with template variables
print(t("hello", name="World"))  # Output: こんにちは、World!
print(t("goodbye"))  # Output: さようなら!
```

### Automatic Language Detection

Use `get_system_language()` to automatically detect the user's system language:

```python
from kiarina.i18n import catalog, get_system_language, get_translator

# Configure the catalog
catalog.add_from_dict({
    "en": {"app.greeting": {"hello": "Hello, $name!"}},
    "ja": {"app.greeting": {"hello": "こんにちは、$name!"}},
    "fr": {"app.greeting": {"hello": "Bonjour, $name!"}},
})

# Automatically detect system language
language = get_system_language()  # Returns "ja" on Japanese systems, "en" on English systems, etc.

# Get translator for detected language
t = get_translator(language, "app.greeting")
print(t("hello", name="World"))  # Output varies based on system language
```

### Type-Safe Class-Based API (Recommended)

For better type safety and IDE support, use the class-based API:

```python
from kiarina.i18n import I18n, get_i18n, settings_manager

# Define your i18n class with explicit scope
class AppI18n(I18n, scope="app.greeting"):
    hello: str = "Hello, $name!"
    goodbye: str = "Goodbye!"
    welcome: str = "Welcome to our app!"

# Or let scope be auto-generated from module.class_name
# If defined in my_app/i18n.py, scope will be: my_app.i18n.UserProfileI18n
class UserProfileI18n(I18n):
    name: str = "Name"
    email: str = "Email"
    bio: str = "Biography"

# Configure the catalog
catalog.add_from_dict({
    "ja": {
        "app.greeting": {
            "hello": "こんにちは、$name!",
            "goodbye": "さようなら!",
            "welcome": "アプリへようこそ!"
        }
    }
})

# Get translated instance
t = get_i18n(AppI18n, "ja")

# Access translations with full type safety and IDE completion
print(t.hello)     # Output: こんにちは、$name!
print(t.goodbye)   # Output: さようなら!
print(t.welcome)   # Output: アプリへようこそ!

# Template variables are handled by the functional API
from kiarina.i18n import get_translator
translator = get_translator("ja", "app.greeting")
print(translator("hello", name="World"))  # Output: こんにちは、World!
```

**Benefits of Class-Based API:**
- **Type Safety**: IDE detects typos in field names
- **Auto-completion**: IDE suggests available translation keys
- **Self-documenting**: Class definition serves as documentation
- **Default Values**: Explicit fallback values when translation is missing
- **Immutable**: Translation instances are frozen and cannot be modified
- **Clean Syntax**: Scope is defined at class level, not as a field

### Using Catalog Files

#### From File System

```python
from kiarina.i18n import catalog, get_translator

# Load single file
catalog.add_from_file("i18n_catalog.yaml")

# Load all YAML files from directory (recursive)
catalog.add_from_dir("translations/")

t = get_translator("en", "app.greeting")
print(t("hello", name="Alice"))
```

Example `i18n_catalog.yaml`:

```yaml
en:
  app.greeting:
    hello: "Hello, $name!"
    goodbye: "Goodbye!"
ja:
  app.greeting:
    hello: "こんにちは、$name!"
    goodbye: "さようなら!"
```

#### From Package Resources

When you want to bundle translation files with your Python package:

```python
from kiarina.i18n import catalog

# Load single file from package
catalog.add_from_package_file("myapp.i18n", "catalogs/en.yaml")
catalog.add_from_package_file("myapp.i18n", "catalogs/ja.yaml")

# Load all YAML files from package directory (non-recursive)
catalog.add_from_package_dir("myapp.i18n.catalogs")
```

**Package Structure Example:**

```
myapp/
├── __init__.py
└── i18n/
    ├── __init__.py
    ├── catalogs/
    │   ├── __init__.py
    │   ├── en.yaml
    │   └── ja.yaml
    └── en.yaml  # Also loaded by add_from_package_dir("myapp.i18n")
```

### Pydantic Integration for LLM Tools

#### Basic Usage

For LLM tool schemas, use `translate_pydantic_model` to create language-specific tool schemas at runtime:

```python
from pydantic import Field
from langchain.tools import BaseTool, tool
from kiarina.i18n import I18n, get_i18n, settings_manager
from kiarina.i18n_pydantic import translate_pydantic_model

# Step 1: Define argument schema with I18n
class ArgsSchema(I18n, scope="hoge_tool.args_schema"):
    """Hoge tool for processing data."""
    name: str = Field(description="Your Name")
    age: int = Field(description="Your Age")

# Step 2: Define tool with default schema
@tool(args_schema=ArgsSchema)
def hoge_tool(name: str, age: int) -> str:
    """Process user data"""
    return f"Processed: {name}, {age}"

# Step 3: Configure translations
catalog.add_from_dict({
    "ja": {
        "hoge_tool.args_schema": {
            "__doc__": "データ処理用のHogeツール。",
            "name": "あなたの名前",
            "age": "あなたの年齢",
        }
    },
    "en": {
        "hoge_tool.args_schema": {
            "__doc__": "Hoge tool for processing data.",
            "name": "Your Name",
            "age": "Your Age",
        }
    }
})

# Step 4: Create language-specific tools at runtime
def get_tool(language: str) -> BaseTool:
    """Get tool with translated schema for the specified language."""
    # Translate the schema (scope is auto-detected from I18n subclass)
    translated_schema = translate_pydantic_model(hoge_tool.args_schema, language)

    # Create a copy of the tool with translated schema
    translated_tool = hoge_tool.model_copy(update={"args_schema": translated_schema})

    return translated_tool

# Step 5: Use language-specific tools
tool_ja = get_tool("ja")  # Japanese version
tool_en = get_tool("en")  # English version

# The tool schema will have language-specific descriptions
schema_ja = tool_ja.args_schema.model_json_schema()
print(tool_ja.args_schema.__doc__)  # "データ処理用のHogeツール。"
print(schema_ja["properties"]["name"]["description"])  # "あなたの名前"

schema_en = tool_en.args_schema.model_json_schema()
print(tool_en.args_schema.__doc__)  # "Hoge tool for processing data."
print(schema_en["properties"]["name"]["description"])  # "Your Name"
```

**Benefits:**
- **Simple Structure**: ArgsSchema is both I18n and Pydantic model
- **Type Safety**: Full IDE completion for field names and types
- **Dynamic Translation**: Schema is translated at runtime with `translate_pydantic_model`
- **Clean Syntax**: Scope is defined at class level
- **Easy Translation**: Single catalog entry covers all translations

#### Nested I18n Models

`translate_pydantic_model` supports translating nested I18n models in `list[I18n]` and `dict[str, I18n]` fields:

```python
from pydantic import Field
from kiarina.i18n import I18n, settings_manager
from kiarina.i18n_pydantic import translate_pydantic_model

# Define nested I18n model
class FileArg(I18n, scope="file_arg"):
    file_path: str = "File path"
    start_line: int = "Start line"
    end_line: int = "End line"

# Define parent I18n model with nested list
class ArgsSchema(I18n, scope="args_schema"):
    """Tool arguments"""
    files: list[FileArg] = "List of files"
    dir_path: str = "Directory path"

# Configure translations
catalog.add_from_dict({
    "ja": {
        "file_arg": {
            "file_path": "ファイルパス",
            "start_line": "開始行",
            "end_line": "終了行",
        },
        "args_schema": {
            "__doc__": "ツール引数",
            "files": "ファイルのリスト",
            "dir_path": "ディレクトリパス",
        }
    }
})

# Translate parent model (nested models are automatically translated)
ArgsSchemaJa = translate_pydantic_model(ArgsSchema, "ja")

# Both parent and nested fields are translated
schema = ArgsSchemaJa.model_json_schema()
print(ArgsSchemaJa.__doc__)  # "ツール引数"
print(schema["properties"]["files"]["description"])  # "ファイルのリスト"
print(schema["$defs"]["FileArg"]["properties"]["file_path"]["description"])  # "ファイルパス"
```

**Supported Nested Types:**
- `list[I18n]` - List of I18n models
- `dict[str, I18n]` - Dictionary with string keys and I18n model values

**Note:** Only I18n subclasses are translated recursively. Regular BaseModel subclasses remain unchanged.

## API Reference

### Class-Based API

#### `I18n`

Base class for defining i18n translations with type safety.

**Usage:**
```python
from kiarina.i18n import I18n

# Explicit scope
class MyI18n(I18n, scope="my.module"):
    title: str = "Default Title"
    description: str = "Default Description"

# Auto-generated scope (from module.class_name)
# If defined in my_app/i18n.py, scope will be: my_app.i18n.UserProfileI18n
class UserProfileI18n(I18n):
    name: str = "Name"
    email: str = "Email"
```

**Features:**
- **Immutable**: Instances are frozen and cannot be modified
- **Type-safe**: Full type hints and validation
- **Self-documenting**: Field names are translation keys, field values are defaults
- **Clean Syntax**: Scope is defined at class level using inheritance parameter
- **Auto-scope**: Automatically generates scope from module and class name if not provided

#### `get_i18n(i18n_class: type[T], language: str) -> T`

Get a translated i18n instance.

**Parameters:**
- `i18n_class`: I18n class to instantiate (not instance!)
- `language`: Target language code (e.g., "en", "ja")

**Returns:**
- Translated i18n instance with all fields translated

**Example:**
```python
from kiarina.i18n import I18n, get_i18n

class AppI18n(I18n, scope="app"):
    title: str = "My App"

t = get_i18n(AppI18n, "ja")
print(t.title)  # Translated title
```

### Pydantic Model Translation (kiarina.i18n_pydantic)

#### `translate_pydantic_model(model: type[T], language: str, scope: str | None = None) -> type[T]`

Translate Pydantic model field descriptions.

**Parameters:**
- `model`: Pydantic model class to translate
- `language`: Target language code (e.g., "ja", "en")
- `scope`: Translation scope (e.g., "hoge.fields"). Optional if `model` is an `I18n` subclass (automatically uses `model._scope`)

**Returns:**
- New model class with translated field descriptions

**Example:**
```python
from pydantic import BaseModel, Field
from kiarina.i18n import I18n, translate_pydantic_model

# With explicit scope (for regular BaseModel)
class Hoge(BaseModel):
    name: str = Field(description="Your Name")

HogeJa = translate_pydantic_model(Hoge, "ja", "hoge.fields")

# With I18n subclass (scope auto-detected)
class HogeI18n(I18n, scope="hoge.fields"):
    name: str = "Your Name"

HogeI18nJa = translate_pydantic_model(HogeI18n, "ja")  # scope is optional
```

### Catalog Management

The `catalog` object provides methods to manage translation data:

**Example:**
```python
from kiarina.i18n import catalog

# Add catalog data
catalog.add_from_dict({
    "en": {"app": {"title": "My App"}},
})

# Clear catalog (useful for testing)
catalog.clear()
```

### Functional API

#### `get_system_language() -> str`

Get the system's default language code.

This function attempts to detect the system's language preference by checking:
1. Environment variables (LANG, LC_ALL, LC_MESSAGES, LANGUAGE)
2. locale.getlocale() as fallback
3. Returns "en" if detection fails

**Returns:**
- Language code (e.g., "en", "ja", "fr")

**Example:**
```python
from kiarina.i18n import get_system_language, get_translator

language = get_system_language()  # Auto-detect system language
t = get_translator(language, "app.greeting")
```

#### `get_translator(language: str, scope: str) -> Translator`

Get a translator for the specified language and scope.

**Parameters:**
- `language`: Target language code (e.g., "en", "ja", "fr")
- `scope`: Translation scope (e.g., "app.greeting", "app.error")

**Returns:**
- `Translator`: Translator instance configured for the specified language and scope

**Example:**
```python
t = get_translator("ja", "app.greeting")
```

### `Translator(catalog, language, scope, fallback_language="en")`

Translator class for internationalization support.

**Parameters:**
- `catalog`: Translation catalog mapping languages to scopes to keys to translations
- `language`: Target language for translation
- `scope`: Scope for translation keys
- `fallback_language`: Fallback language when translation is not found (default: "en")

**Methods:**
- `__call__(key, default=None, **kwargs)`: Translate a key with optional template variables

**Example:**
```python
from kiarina.i18n import Translator

catalog = {
    "en": {"app.greeting": {"hello": "Hello, $name!"}},
    "ja": {"app.greeting": {"hello": "こんにちは、$name!"}}
}

t = Translator(catalog=catalog, language="ja", scope="app.greeting")
print(t("hello", name="World"))  # Output: こんにちは、World!
```

### Translation Behavior

1. **Primary lookup**: Searches for the key in the target language
2. **Fallback lookup**: If not found, searches in the fallback language
3. **Default value**: If still not found, uses the provided default value
4. **Error handling**: If no default is provided, returns `"{scope}#{key}"` and logs an error

## Configuration

### Catalog Management

The catalog is managed separately from settings using the `catalog` singleton:

```python
from kiarina.i18n import catalog

# Add from dictionary
catalog.add_from_dict({
    "en": {"app.greeting": {"hello": "Hello!"}},
    "ja": {"app.greeting": {"hello": "こんにちは!"}}
})

# Add from YAML file
catalog.add_from_file("translations.yaml")

# Multiple files can be merged
catalog.add_from_file("base.yaml")
catalog.add_from_file("app-specific.yaml")
catalog.add_from_file("user-overrides.yaml")

# Clear all catalog data
catalog.clear()
```

### Settings Configuration

Settings only manage the default language:

```yaml
# config.yaml
kiarina.i18n:
  default_language: "en"
```

```python
from pydantic_settings_manager import load_user_configs
import yaml

with open("config.yaml") as f:
    config = yaml.safe_load(f)

load_user_configs(config)
```

### Settings Fields

- `default_language` (str): Default language to use when translation is not found (default: "en")

## Testing

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=kiarina.i18n --cov-report=html
```

## Dependencies

- `pydantic>=2.0.0`
- `pydantic-settings>=2.0.0`
- `pydantic-settings-manager>=2.3.0`
- `pyyaml>=6.0.0`

## License

This project is licensed under the MIT License - see the [LICENSE](../../LICENSE) file for details.

## Related Projects

- [kiarina-python](https://github.com/kiarina/kiarina-python) - Parent monorepo containing all kiarina packages
