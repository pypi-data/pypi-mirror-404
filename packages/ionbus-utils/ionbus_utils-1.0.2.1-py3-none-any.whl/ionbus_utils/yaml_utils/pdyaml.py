"""
PDYaml - A Pydantic BaseModel extension with YAML support and
hierarchical value lookup.
"""

from __future__ import annotations

from typing import Any, ClassVar, TypeVar
from pydantic import (
    BaseModel,
    ConfigDict,
    model_validator,
    Field,
    PrivateAttr,
)
import yaml
import threading
from urllib.request import urlopen
from urllib.parse import urlparse

T = TypeVar("T", bound="PDYaml")

# Thread-local storage for tracking tree construction
_tree_construction = threading.local()


def _get_root() -> PDYaml | None:
    """Get the current root object being constructed in this thread."""
    return getattr(_tree_construction, "root", None)


def _set_root_this_thread(root: PDYaml | None) -> None:
    """Set the current root object being constructed (in this thread only)."""
    _tree_construction.root = root


class PDYaml(BaseModel):
    """
    Base class for YAML-backed Pydantic models with parent-child
    relationships.

    Features:
    - Automatic naming with class-based counter
    - Parent-child relationships with automatic parent setting
    - Hierarchical value lookup via get_value()
    - YAML file and string loading
    - Tree initialization support
    """

    # Class variable for instance counter
    # (shared across all PDYaml instances)
    instances: ClassVar[int] = 0

    # Private attributes for tracking tree_init state. Not included in object
    # schema.
    _tree_init_done: bool = PrivateAttr(default=False)

    # Instance fields
    name: str = ""
    parent: PDYaml | None = Field(default=None, exclude=True)

    # Pydantic v2 configuration
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self, **data):
        """
        Initialize and set up auto-naming if name is not provided.
        Marks this instance as root if no root is currently set.
        """
        # Auto-generate name if not provided or empty
        if not data.get("name"):
            PDYaml.instances += 1
            class_name = self.__class__.__name__
            data["name"] = f"{class_name}_{PDYaml.instances}"

        # Mark root before construction if not already set.
        root_already_set = _get_root() is not None
        if not root_already_set:
            # Setting this means that anything objects that come into existence
            # after this will be considered part of the same tree.
            #
            # This will be automatically unset in model_post_init after
            # tree_init is called.
            _set_root_this_thread(self)

        try:
            super().__init__(**data)
        except Exception:
            # Reset the root marker on failure to avoid leaking state
            if not root_already_set:
                _set_root_this_thread(None)
            raise

    @model_validator(mode="after")
    def set_children_parents(self) -> "PDYaml":
        """
        Automatically set parent references for all PDYaml children.
        Handles singletons, lists, and dictionaries.
        """
        for field_name, field_value in self.__dict__.items():
            # Skip special fields
            if field_name in ("name", "parent"):
                continue

            # Handle singleton PDYaml
            if isinstance(field_value, PDYaml):
                field_value.parent = self

            # Handle list of PDYaml objects
            elif isinstance(field_value, list):
                for item in field_value:
                    if isinstance(item, PDYaml):
                        item.parent = self

            # Handle dict of PDYaml objects
            elif isinstance(field_value, dict):
                for key, item in field_value.items():
                    if isinstance(item, PDYaml):
                        item.parent = self
                        # Override child's name with dictionary key
                        item.name = key

        return self

    def model_post_init(self, __context: Any) -> None:
        """
        Called after model initialization.
        Only the root object of a tree construction calls tree_init.
        """
        super().model_post_init(__context)

        # Check if we're the root of a tree construction
        is_root = _get_root() is self

        # Only call tree_init if this is the root object.
        # This section also resets the threading.local root to None
        # so that any objects objects created after this run will
        # be treated as new roots.
        if is_root:
            try:
                self._run_tree_init()
                self.call_children_tree_init()
            finally:
                _set_root_this_thread(None)

    def get_value(self, name: str, default: Any = None) -> Any:
        """
        Get a value with hierarchical lookup.

        Lookup order:
        1. Check if this object has the attribute and it's not None
        2. Check if this object has a 'default_values' member
           (PDYaml) with the attribute
        3. Recursively check parent
        4. Return default if no parent exists

        Args:
            name: The attribute name to look up
            default: Default value if not found anywhere in the
                     hierarchy

        Returns:
            The found value or default
        """
        # Check if this object has the attribute and it's not None
        if hasattr(self, name):
            value = getattr(self, name)
            if value is not None:
                return value

        # Check if we have a default_values member
        if hasattr(self, "default_values"):
            default_values = getattr(self, "default_values")
            if isinstance(default_values, PDYaml) and hasattr(
                default_values, name
            ):
                value = getattr(default_values, name)
                if value is not None:
                    return value

        # Recursively check parent
        if self.parent is not None:
            return self.parent.get_value(name, default)

        # No parent, return default
        return default

    def call_children_tree_init(self, _visited: set[int] | None = None) -> None:
        """
        Call tree_init() on all PDYaml children, followed by their
        children's tree_init recursively.
        Automatically detects PDYaml instances in singletons, lists,
        and dicts.

        Includes cycle protection to prevent infinite recursion if
        the same object is referenced multiple times.
        """
        if _visited is None:
            _visited = set()

        _visited.add(id(self))

        for field_name, field_value in self.__dict__.items():
            # Skip special fields
            if field_name in ("name", "parent"):
                continue

            # Handle singleton PDYaml
            if isinstance(field_value, PDYaml):
                if id(field_value) not in _visited:
                    _visited.add(id(field_value))
                    field_value._run_tree_init()
                    field_value.call_children_tree_init(_visited)

            # Handle list of PDYaml objects
            elif isinstance(field_value, list):
                for item in field_value:
                    if isinstance(item, PDYaml) and id(item) not in _visited:
                        _visited.add(id(item))
                        item._run_tree_init()
                        item.call_children_tree_init(_visited)

            # Handle dict of PDYaml objects
            elif isinstance(field_value, dict):
                for item in field_value.values():
                    if isinstance(item, PDYaml) and id(item) not in _visited:
                        _visited.add(id(item))
                        item._run_tree_init()
                        item.call_children_tree_init(_visited)

    def tree_init(self) -> None:
        """
        Called after the entire tree has been constructed and parent
        links are set.

        This method is called on the root object after
        model_post_init. The base implementation automatically calls
        tree_init on all children after the subclass's tree_init runs.

        Override this method in subclasses to perform initialization
        that requires the full tree structure to be available.
        Do NOT call super().tree_init() - the framework handles
        children automatically via call_children_tree_init().
        """
        # Subclasses override this for their custom logic
        pass

    def _run_tree_init(self) -> None:
        """
        Internal method to run tree_init once per instance.
        Prevents duplicate calls using _tree_init_done flag.
        """
        # Avoid duplicate work
        if self._tree_init_done:
            return

        self.tree_init()
        self._tree_init_done = True

    def initialize_tree(self) -> None:
        """
        Manually trigger tree_init on this object and all children.

        NOTE: This method is no longer needed for most use cases.
        Tree initialization happens automatically when you construct
        objects. Only use this if you need to manually re-trigger
        tree_init for some reason.

        Example:
            parent = Parent(
                children=[Child(value=1), Child(value=2)]
            )
            parent.initialize_tree()  # Usually not needed!
        """
        self._run_tree_init()
        self.call_children_tree_init()

    def model_dump_yaml(
        self,
        *,
        default_flow_style: bool = False,
        sort_keys: bool = False,
        **kwargs: Any,
    ) -> str:
        """
        Serialize the model to a YAML string.

        This is a convenience method that combines model_dump() with
        yaml.dump(). Note that parent references are automatically
        excluded from the output.

        Args:
            default_flow_style: If False, use block style (default).
                               If True, use flow style (inline).
            sort_keys: If True, sort dictionary keys alphabetically.
                      If False, preserve field order (default).
            **kwargs: Additional keyword arguments to pass to model_dump()
                     (e.g., exclude, include, exclude_none)

        Returns:
            YAML string representation of the model

        Example:
            yaml_str = config.model_dump_yaml()
            yaml_str = config.model_dump_yaml(exclude={'name'})
        """
        data = self.model_dump(**kwargs)
        return yaml.dump(
            data, default_flow_style=default_flow_style, sort_keys=sort_keys
        )

    @classmethod
    def create(cls: type[T], **kwargs) -> T:
        """
        Factory method to create an instance from keyword arguments.

        This method is equivalent to calling the constructor directly,
        as tree_init is called automatically in both cases.

        Args:
            **kwargs: Field values for the instance

        Returns:
            Instance of the class with tree_init called

        Example:
            config = Config.create(timeout=60, retries=5)
            # Equivalent to: config = Config(timeout=60, retries=5)
        """
        return cls(**kwargs)

    @classmethod
    def from_yaml_string(cls: type[T], yaml_str: str) -> T:
        """
        Factory method to create an instance from a YAML string.

        Args:
            yaml_str: YAML formatted string

        Returns:
            Instance of the class with tree_init called
        """
        data = yaml.safe_load(yaml_str)
        return cls(**data)

    @classmethod
    def from_yaml_file(cls: type[T], file_path: str) -> T:
        """
        Factory method to create an instance from a YAML file or URL.

        Args:
            file_path: Path to the YAML file or URL (http://, https://,
                      ftp://, etc.)

        Returns:
            Instance of the class with tree_init called
        """
        data = cls.read_yaml_file(file_path)
        return cls(**data)

    @classmethod
    def read_yaml_file(cls: type[T], file_path: str) -> dict:
        """Reads information from file (either local or URL)
        and returns dict of parsed YAML data."""
        # Check if file_path is a URL
        parsed = urlparse(file_path)
        if parsed.scheme in ("http", "https", "ftp", "ftps"):
            # Load from URL
            with urlopen(file_path) as response:
                return yaml.safe_load(response)
        else:
            # Load from local file
            with open(file_path, "r", encoding="utf-8") as file_source:
                return yaml.safe_load(file_source)
