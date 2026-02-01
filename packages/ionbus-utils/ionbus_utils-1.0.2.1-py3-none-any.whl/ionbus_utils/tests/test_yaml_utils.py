"""Tests for yaml_utils module (PDYaml)."""

from __future__ import annotations

import site
from pathlib import Path
from typing import Any

import pytest
from pydantic import Field

parent_dir = Path(__file__).absolute().parent.parent.parent
site.addsitedir(str(parent_dir))

from ionbus_utils.yaml_utils import PDYaml


class SimpleConfig(PDYaml):
    """Simple config for testing."""

    value: int = 0
    message: str = ""


class ChildConfig(PDYaml):
    """Child config for testing parent-child relationships."""

    value: int = 0


class ParentConfig(PDYaml):
    """Parent config with children."""

    child: ChildConfig | None = None
    children: list[ChildConfig] = Field(default_factory=list)
    child_dict: dict[str, ChildConfig] = Field(default_factory=dict)


class DefaultValuesConfig(PDYaml):
    """Config with default_values for hierarchical lookup."""

    timeout: int | None = None
    default_values: SimpleConfig | None = None


class TreeInitConfig(PDYaml):
    """Config for testing tree_init."""

    value: int = 0
    computed: int = 0

    def tree_init(self):
        self.computed = self.value * 2


class TestPDYamlBasics:
    """Tests for basic PDYaml functionality."""

    def test_auto_naming(self):
        """Test automatic name generation."""
        config = SimpleConfig(value=1)
        assert config.name.startswith("SimpleConfig_")

    def test_explicit_naming(self):
        """Test explicit name is preserved."""
        config = SimpleConfig(name="my_config", value=1)
        assert config.name == "my_config"

    def test_fields_are_set(self):
        """Test fields are properly set."""
        config = SimpleConfig(value=42, message="hello")
        assert config.value == 42
        assert config.message == "hello"

    def test_default_values(self):
        """Test default values are used."""
        config = SimpleConfig()
        assert config.value == 0
        assert config.message == ""


class TestFromYamlString:
    """Tests for from_yaml_string factory method."""

    def test_basic_loading(self):
        """Test loading from YAML string."""
        yaml_str = """
value: 100
message: "hello world"
"""
        config = SimpleConfig.from_yaml_string(yaml_str)
        assert config.value == 100
        assert config.message == "hello world"

    def test_with_name(self):
        """Test loading with explicit name."""
        yaml_str = """
name: my_config
value: 50
"""
        config = SimpleConfig.from_yaml_string(yaml_str)
        assert config.name == "my_config"
        assert config.value == 50


class TestFromYamlFile:
    """Tests for from_yaml_file factory method."""

    def test_loading_from_file(self, temp_dir):
        """Test loading from YAML file."""
        yaml_file = temp_dir / "config.yaml"
        yaml_file.write_text("value: 200\nmessage: from file\n")
        config = SimpleConfig.from_yaml_file(str(yaml_file))
        assert config.value == 200
        assert config.message == "from file"


class TestParentChildRelationships:
    """Tests for automatic parent-child relationships."""

    def test_singleton_child_parent(self):
        """Test parent is set for singleton child."""
        yaml_str = """
child:
  value: 10
"""
        parent = ParentConfig.from_yaml_string(yaml_str)
        assert parent.child is not None
        assert parent.child.parent is parent

    def test_list_children_parent(self):
        """Test parent is set for children in list."""
        yaml_str = """
children:
  - value: 1
  - value: 2
  - value: 3
"""
        parent = ParentConfig.from_yaml_string(yaml_str)
        assert len(parent.children) == 3
        for child in parent.children:
            assert child.parent is parent

    def test_dict_children_parent(self):
        """Test parent is set for children in dict."""
        yaml_str = """
child_dict:
  first:
    value: 1
  second:
    value: 2
"""
        parent = ParentConfig.from_yaml_string(yaml_str)
        assert len(parent.child_dict) == 2
        for child in parent.child_dict.values():
            assert child.parent is parent

    def test_dict_keys_become_names(self):
        """Test dictionary keys override child names."""
        yaml_str = """
child_dict:
  custom_name:
    value: 1
"""
        parent = ParentConfig.from_yaml_string(yaml_str)
        assert parent.child_dict["custom_name"].name == "custom_name"


class TestGetValue:
    """Tests for hierarchical get_value lookup."""

    def test_returns_own_value(self):
        """Test returns own value if present."""
        config = SimpleConfig(value=42)
        assert config.get_value("value") == 42

    def test_returns_default_when_not_found(self):
        """Test returns default when value not found."""
        config = SimpleConfig()
        assert config.get_value("nonexistent", "default") == "default"

    def test_searches_parent_chain(self):
        """Test searches up parent chain."""

        class Parent(PDYaml):
            timeout: int = 30
            child: SimpleConfig | None = None

        yaml_str = """
timeout: 60
child:
  value: 1
"""
        parent = Parent.from_yaml_string(yaml_str)
        # Child should find timeout from parent
        assert parent.child.get_value("timeout") == 60

    def test_uses_default_values_member(self):
        """Test uses default_values member for lookup."""
        yaml_str = """
default_values:
  value: 999
"""
        config = DefaultValuesConfig.from_yaml_string(yaml_str)
        # timeout is None on self, but value exists in default_values
        assert config.get_value("value") == 999

    def test_own_value_takes_precedence(self):
        """Test own value takes precedence over parent."""

        class Parent(PDYaml):
            timeout: int = 30
            child: SimpleConfig | None = None

        yaml_str = """
timeout: 60
child:
  value: 1
"""
        parent = Parent.from_yaml_string(yaml_str)
        # Child's own value takes precedence
        assert parent.child.get_value("value") == 1


class TestTreeInit:
    """Tests for tree_init functionality."""

    def test_tree_init_called(self):
        """Test tree_init is called after construction."""
        config = TreeInitConfig(value=5)
        assert config.computed == 10

    def test_tree_init_with_yaml(self):
        """Test tree_init is called when loading from YAML."""
        yaml_str = "value: 7"
        config = TreeInitConfig.from_yaml_string(yaml_str)
        assert config.computed == 14

    def test_tree_init_called_on_children(self):
        """Test tree_init is called on nested children."""

        class Parent(PDYaml):
            child: TreeInitConfig | None = None

        yaml_str = """
child:
  value: 3
"""
        parent = Parent.from_yaml_string(yaml_str)
        assert parent.child.computed == 6


class TestSerialization:
    """Tests for serialization methods."""

    def test_model_dump(self):
        """Test model_dump returns dict."""
        config = SimpleConfig(value=42, message="hello")
        data = config.model_dump()
        assert isinstance(data, dict)
        assert data["value"] == 42
        assert data["message"] == "hello"

    def test_model_dump_json(self):
        """Test model_dump_json returns JSON string."""
        config = SimpleConfig(value=42, message="hello")
        json_str = config.model_dump_json()
        assert isinstance(json_str, str)
        assert "42" in json_str
        assert "hello" in json_str

    def test_model_dump_yaml(self):
        """Test model_dump_yaml returns YAML string."""
        config = SimpleConfig(value=42, message="hello")
        yaml_str = config.model_dump_yaml()
        assert isinstance(yaml_str, str)
        assert "value: 42" in yaml_str
        assert "message: hello" in yaml_str

    def test_parent_excluded_from_dump(self):
        """Test parent is excluded from serialization."""
        yaml_str = """
child:
  value: 10
"""
        parent = ParentConfig.from_yaml_string(yaml_str)
        data = parent.child.model_dump()
        assert "parent" not in data


class TestCreate:
    """Tests for create factory method."""

    def test_create_equivalent_to_constructor(self):
        """Test create is equivalent to constructor."""
        config1 = SimpleConfig.create(value=42, message="hello")
        config2 = SimpleConfig(value=42, message="hello")
        assert config1.value == config2.value
        assert config1.message == config2.message


class TestReadYamlFile:
    """Tests for read_yaml_file class method."""

    def test_reads_local_file(self, temp_dir):
        """Test reading from local file."""
        yaml_file = temp_dir / "test.yaml"
        yaml_file.write_text("key: value\nnumber: 42\n")
        data = SimpleConfig.read_yaml_file(str(yaml_file))
        assert isinstance(data, dict)
        assert data["key"] == "value"
        assert data["number"] == 42
