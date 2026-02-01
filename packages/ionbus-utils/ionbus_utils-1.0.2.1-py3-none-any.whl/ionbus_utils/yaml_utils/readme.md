# PDYaml

A Pydantic BaseModel extension that adds YAML support, automatic parent-child relationships, and hierarchical value lookup.


<!-- TOC start (generated with https://bitdowntoc.derlin.ch/) -->

- [Features](#features)
- [Installation](#installation)
   * [Required Packages](#required-packages)
   * [Python Version Compatibility](#python-version-compatibility)
- [Quick Start](#quick-start)
- [Comprehensive Example](#comprehensive-example)
- [Key Concepts](#key-concepts)
   * [Auto-naming](#auto-naming)
   * [Parent-Child Relationships](#parent-child-relationships)
   * [Hierarchical Value Lookup](#hierarchical-value-lookup)
   * [Tree Initialization](#tree-initialization)
   * [Factory Methods](#factory-methods)
- [API Reference](#api-reference)
   * [PDYaml Class](#pdyaml-class)
      + [Fields](#fields)
      + [Methods](#methods)
      + [Factory Methods](#factory-methods-1)
- [Pydantic v2 Compatibility](#pydantic-v2-compatibility)
   * [Common Pydantic Features](#common-pydantic-features)
   * [Additional Pydantic Features](#additional-pydantic-features)
- [Serialization](#serialization)
   * [model_dump() - Convert to Dictionary](#model_dump---convert-to-dictionary)
   * [model_dump_json() - Convert to JSON String](#model_dump_json---convert-to-json-string)
   * [model_dump_yaml() - Convert to YAML String](#model_dump_yaml---convert-to-yaml-string)
   * [Serialization with Nested Objects](#serialization-with-nested-objects)
   * [Round-trip Example](#round-trip-example)
- [Running Tests](#running-tests)
- [License](#license)

<!-- TOC end -->



## Features

- **Auto-naming**: Automatically generates unique names for instances using a class-wide counter
- **Parent-child relationships**: Automatically sets parent references for nested PDYaml objects
- **Hierarchical value lookup**: Search for values up the parent chain with `get_value()`
- **YAML loading**: Factory methods for loading from YAML files or strings
- **Tree initialization**: Controlled initialization after the full object tree is constructed
- **Type-safe**: Full type hint support with proper return types for factory methods

## Installation

### Required Packages

- **pydantic** (v2.x)
- **pyyaml**

### Python Version Compatibility

- **Python 3.10+**: Works out of the box
- **Python 3.8 and 3.9**: Requires `eval-type-backport` package
  ```bash
  conda install -c conda-forge eval-type-backport
  ```

## Quick Start

```python
from ionbus.yaml_utils import PDYaml

# Simple class definition
class Config(PDYaml):
    timeout: int = 30
    retries: int = 3

# Load from YAML string (recommended for nested structures)
yaml_str = """
timeout: 45
retries: 5
"""
config = Config.from_yaml_string(yaml_str)
print(config.name)  # Output: Config_1

# Or use constructor for programmatic construction
config2 = Config(timeout=60, retries=5)
print(config2.name)  # Output: Config_2

# tree_init() is called automatically in both cases!
```

## Comprehensive Example

Here's a complete example demonstrating all features:

```python
from ionbus.yaml_utils import PDYaml
from pydantic import Field


# Define configuration classes
class DatabaseConfig(PDYaml):
    """Database connection configuration."""
    host: str
    port: int
    timeout: int = 30
    max_connections: int = 10


class ServerConfig(PDYaml):
    """Server configuration."""
    name: str
    host: str
    port: int
    debug: bool = False


class ApplicationConfig(PDYaml):
    """
    Main application configuration with default values
    and nested components.
    """
    version: str
    environment: str

    # Optional default values (used by get_value)
    default_values: ServerConfig | None = None

    # Singleton child
    primary_database: DatabaseConfig | None = None

    # List of children
    servers: list[ServerConfig] = Field(default_factory=list)

    # Dictionary of children (keys become child names)
    databases: dict[str, DatabaseConfig] = Field(default_factory=dict)

    def tree_init(self):
        """
        Custom initialization called after the tree is fully constructed.
        This runs after all parent-child relationships are established.
        The base class automatically handles calling tree_init on all
        children recursively.
        """
        print(f"Application '{self.name}' initialized")
        print(f"  Version: {self.version}")
        print(f"  Environment: {self.environment}")
        print(f"  Servers: {len(self.servers)}")
        print(f"  Databases: {len(self.databases)}")


# Load configuration from YAML
yaml_config = """
name: MyApp
version: "1.0.0"
environment: production

# Default values for all servers
default_values:
  debug: false
  port: 8080

# Primary database
primary_database:
  host: db.example.com
  port: 5432
  max_connections: 50

# List of servers
servers:
  - name: api-server
    host: api.example.com
    port: 443
  - name: web-server
    host: www.example.com
    port: 80
    debug: true

# Dictionary of databases
databases:
  users:
    host: users-db.example.com
    port: 5432
  analytics:
    host: analytics-db.example.com
    port: 5432
    timeout: 60
"""

# Load the application configuration
app = ApplicationConfig.from_yaml_string(yaml_config)
# Output: Application 'MyApp' initialized
#           Version: 1.0.0
#           Environment: production
#           Servers: 2
#           Databases: 2

# Access nested objects
print(app.primary_database.host)  # db.example.com
print(app.servers[0].name)        # api-server
print(app.databases["users"].host) # users-db.example.com

# Parent-child relationships are automatically set
print(app.servers[0].parent.name)  # MyApp
print(app.databases["users"].parent.name)  # MyApp

# Dictionary keys override child names
print(app.databases["users"].name)  # users (not DatabaseConfig_X)

# Hierarchical value lookup with get_value()
# Search order: self -> self.default_values -> parent chain -> default
print(app.servers[0].get_value("debug"))  # False (from app.default_values)
print(app.servers[1].get_value("debug"))  # True (from self)
print(app.servers[0].get_value("port"))   # 443 (from self)
print(app.servers[0].get_value("missing", "default"))  # default

# Type hints work correctly
config: ApplicationConfig = ApplicationConfig.from_yaml_file("config.yaml")
```

## Key Concepts

### Auto-naming

If no `name` is provided, PDYaml automatically generates one using the class name and a global counter:

```python
server1 = ServerConfig(host="localhost", port=8080)
server2 = ServerConfig(host="localhost", port=8081)
print(server1.name)  # ServerConfig_1
print(server2.name)  # ServerConfig_2
```

### Parent-Child Relationships

Parent references are automatically set for:
- **Singleton fields**: Single PDYaml object
- **List fields**: List of PDYaml objects
- **Dict fields**: Dictionary with PDYaml values (keys become child names)

```python
yaml_str = """
version: "1.0"
environment: dev
servers:
  - host: localhost
    port: 8080
"""
app = ApplicationConfig.from_yaml_string(yaml_str)

# Parent is automatically set
assert app.servers[0].parent is app
```

### Hierarchical Value Lookup

`get_value()` searches for values in this order:
1. The object's own attributes (if not None)
2. The object's `default_values` field (if present and value exists)
3. Parent's `get_value()` (recursive)
4. Default parameter value

```python
# Server doesn't have 'timeout', but primary_database does
timeout = app.servers[0].get_value("timeout")
# Searches: servers[0] -> app.default_values -> app -> None
# Returns the default parameter or None
```

### Tree Initialization

`tree_init()` is called after the entire object tree is constructed and all parent-child relationships are established. Override this method to perform initialization that requires the full tree structure.

**Recommended: Use factory methods** where `tree_init()` is called automatically:

```python
# From YAML - tree_init called automatically
app = ApplicationConfig.from_yaml_string(yaml_str)

# Or use constructor - tree_init also called automatically!
app = ApplicationConfig(
    version="1.0",
    servers=[ServerConfig(host="localhost", port=8080)]
)
```

**Note on inline construction**: The `tree_init()` function will not run correctly if the children are created before the parents.  In this case, use one of the factory methods (`create()`, `from_yaml_string()`, or `from_yaml_file()`.)

**Example: Using tree_init for computed fields with hierarchical lookup**:

```python

class Rectangle(PDYaml):
    length: float | None = None
    width: float | None = None
    area: float = 0.0

    def tree_init(self):
        # Use hierarchical lookup to get length/width from parent if not set.
        #
        # NOTE: If, for example, self.length exists, self.get_value("length")
        # will return self.length.  In this case, the line is a effectively a
        # no-op and therefore there is no need to put an explicit check
        # `if self.length is None:`
        # before the assignment.

        self.length = self.get_value("length", 0.0)
        self.width = self.get_value("width", 0.0)

        # Calculate computed field
        self.area = self.length * self.width

# Example with parent providing default dimensions
class Container(PDYaml):
    length: float = 10.0
    width: float = 5.0
    rectangle: Rectangle | None = None

yaml_str = """
length: 20.0
width: 15.0
rectangle:
  # No length/width specified - will use parent values via get_value
"""
container = Container.from_yaml_string(yaml_str)
# container.rectangle.area = 300.0 (calculated from parent values)
```

### Factory Methods

Load from YAML files, URLs, or strings:

```python
# From local YAML file
config = ApplicationConfig.from_yaml_file("config.yaml")

# From URL
config = ApplicationConfig.from_yaml_file("https://example.com/config.yaml")

# From YAML string
yaml_str = """
version: "1.0"
environment: dev
"""
config = ApplicationConfig.from_yaml_string(yaml_str)
```

## API Reference

### PDYaml Class

#### Fields
- `name: str` - Instance name (auto-generated if not provided)
- `parent: PDYaml | None` - Parent object reference (auto-set)

#### Methods
- `get_value(name: str, default: Any = None) -> Any`
  - Hierarchical value lookup

- `model_dump(**kwargs) -> dict`
  - Convert to dictionary (inherited from Pydantic BaseModel)

- `model_dump_json(**kwargs) -> str`
  - Convert to JSON string (inherited from Pydantic BaseModel)

- `model_dump_yaml(**kwargs) -> str`
  - Convert to YAML string (PDYaml-specific method)

#### Factory Methods
- `create(cls, **kwargs) -> T`
  - Create instance from keyword arguments, calls tree_init automatically
  - Equivalent to using constructor directly

- `from_yaml_string(cls, yaml_str: str) -> T`
  - Load from YAML string, calls tree_init automatically

- `from_yaml_file(cls, file_path: str) -> T`
  - Load from YAML file or URL (http://, https://, ftp://), calls tree_init automatically

## Pydantic v2 Compatibility

PDYaml is fully compatible with Pydantic v2 features. All standard Pydantic fields, validators, serialization options, and configuration work seamlessly with PDYaml classes.

### Common Pydantic Features

```python
from ionbus.yaml_utils import PDYaml
from pydantic import Field, field_validator, computed_field

class ServerConfig(PDYaml):
    # Field with validation constraints
    host: str = Field(min_length=1, max_length=255)
    port: int = Field(ge=1, le=65535, description="Server port number")

    # Optional field with default factory
    tags: list[str] = Field(default_factory=list)

    # Field with alias for YAML keys
    max_connections: int = Field(default=100, alias="maxConnections")

    # Excluded field (not in dict/json output)
    internal_id: str = Field(default="", exclude=True)

    # Field validator
    @field_validator('host')
    @classmethod
    def validate_host(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("Host cannot be empty")
        return v.lower()

    # Computed field (read-only property)
    @computed_field
    @property
    def connection_string(self) -> str:
        return f"{self.host}:{self.port}"

# Load from YAML with aliases
yaml_str = """
host: API.EXAMPLE.COM
port: 8080
maxConnections: 200
tags: [web, api]
"""
config = ServerConfig.from_yaml_string(yaml_str)

print(config.host)                # "api.example.com" (validated, lowercased)
print(config.max_connections)     # 200 (from alias)
print(config.connection_string)   # "api.example.com:8080" (computed)
```

### Additional Pydantic Features

All Pydantic v2 features work with PDYaml:
- **Field validators**: `@field_validator`, `@model_validator`
- **Computed fields**: `@computed_field`
- **Field constraints**: `min_length`, `max_length`, `ge`, `le`, `gt`, `lt`, etc.
- **Field configuration**: `alias`, `exclude`, `description`, `default_factory`
- **Model configuration**: `ConfigDict` settings
- **Serialization**: `model_dump()`, `model_dump_json()`
- **Custom types**: Any Pydantic-compatible type annotations

For complete documentation on Pydantic v2 features, see:
- [Pydantic v2 Documentation](https://docs.pydantic.dev/latest/)
- [Field Types](https://docs.pydantic.dev/latest/concepts/types/)
- [Validators](https://docs.pydantic.dev/latest/concepts/validators/)
- [Fields](https://docs.pydantic.dev/latest/concepts/fields/)

## Serialization

PDYaml provides three main serialization methods for converting objects back to data formats.

**Key Properties:**
- ✅ **Deterministic**: Multiple serializations of the same object produce identical output
- ✅ **Field Order Preserved**: Fields appear in the order they're defined in the class
- ✅ **Parent Exclusion**: Parent references are automatically excluded to prevent circular references

### `model_dump()` - Convert to Dictionary

Inherited from Pydantic's BaseModel. Converts the object tree to a Python dictionary.

```python
class Config(PDYaml):
    timeout: int = 30
    retries: int = 3

config = Config(timeout=60, retries=5)

# Convert to dictionary
data = config.model_dump()
print(data)
# {'name': 'Config_1', 'timeout': 60, 'retries': 3}

# With options
data = config.model_dump(
    exclude={'name'},      # Exclude specific fields
    exclude_none=True,     # Skip None values
    by_alias=True          # Use field aliases
)
```

**Note**: The `parent` field is automatically excluded to prevent circular references.

### `model_dump_json()` - Convert to JSON String

Inherited from Pydantic's BaseModel. Converts the object tree to a JSON string.

```python
# Convert to JSON
json_str = config.model_dump_json()
print(json_str)
# '{"name":"Config_1","timeout":60,"retries":3}'

# With formatting
json_str = config.model_dump_json(indent=2)
# {
#   "name": "Config_1",
#   "timeout": 60,
#   "retries": 3
# }

# With options
json_str = config.model_dump_json(
    exclude={'name'},
    exclude_none=True
)
```

### `model_dump_yaml()` - Convert to YAML String

**PDYaml-specific method**. Converts the object tree to a YAML string.

```python
# Convert to YAML
yaml_str = config.model_dump_yaml()
print(yaml_str)
# name: Config_1
# retries: 3
# timeout: 60

# With options
yaml_str = config.model_dump_yaml(
    exclude={'name'},           # Exclude specific fields
    default_flow_style=True,    # Use inline style
    sort_keys=True              # Sort keys alphabetically
)
```

### Serialization with Nested Objects

All three methods handle nested PDYaml objects automatically:

```python
class Server(PDYaml):
    host: str
    port: int

class Application(PDYaml):
    version: str
    servers: list[Server] = Field(default_factory=list)

yaml_str = """
version: "1.0"
servers:
  - host: localhost
    port: 8080
  - host: api.example.com
    port: 443
"""

app = Application.from_yaml_string(yaml_str)

# All methods serialize the entire tree
data = app.model_dump()
json_str = app.model_dump_json(indent=2)
yaml_str = app.model_dump_yaml()

# Parent references are automatically excluded
assert app.servers[0].parent is app  # ✓ Parent exists
# But 'parent' is NOT in the serialized output
```

### Round-trip Example

```python
# Load from YAML
original_yaml = """
version: "1.0"
timeout: 30
"""
config = Config.from_yaml_string(original_yaml)

# Modify
config.timeout = 60

# Save back to YAML
new_yaml = config.model_dump_yaml()
print(new_yaml)
# name: Config_1
# timeout: 60
# version: '1.0'
```

## Running Tests

```bash
conda run -n your_env python test_pdyaml.py
```

## License

This implementation is provided as-is for use in your projects.
