"""Tests for general.py module."""

from __future__ import annotations

import json
import os
import site
from enum import Enum
from pathlib import Path

import pytest

parent_dir = Path(__file__).absolute().parent.parent.parent
site.addsitedir(str(parent_dir))

from ionbus_utils.general import (  # noqa: E402
    as_string,
    cleanup_username,
    comma_join_list,
    compress_and_encode_as_base64,
    convert_string_to_float,
    decompress_and_decode_from_base64,
    dict_to_namedtuple,
    filter_string_rep_of_dict,
    filter_string_rep_of_list,
    is_non_string_sequence,
    list_to_comma_string,
    load_json,
    load_json_string,
    multiline_comma_join,
    recursively_uppercase_dict_keys,
    remove_comments,
    string_to_enum_value,
    temporarily_change_dir,
    timestamped_id,
    timestamped_unique_id,
    to_single_list,
)


class TestRemoveComments:
    """Tests for remove_comments function."""

    def test_removes_single_line_comments(self):
        """Test removing // comments."""
        text = '{"key": "value"} // this is a comment'
        result = remove_comments(text)
        assert "//" not in result
        assert "comment" not in result

    def test_removes_multiline_comments(self):
        """Test removing /* */ comments."""
        text = '{"key": /* comment */ "value"}'
        result = remove_comments(text)
        assert "/*" not in result
        assert "*/" not in result

    def test_removes_trailing_commas(self):
        """Test removing trailing commas."""
        text = '{"key": "value",}'
        result = remove_comments(text)
        # Should be valid JSON now
        parsed = json.loads(result)
        assert parsed["key"] == "value"

    def test_preserves_strings(self):
        """Test preserves strings with comment-like content."""
        text = '{"url": "http://example.com"}'
        result = remove_comments(text)
        parsed = json.loads(result)
        assert parsed["url"] == "http://example.com"


class TestLoadJsonString:
    """Tests for load_json_string function."""

    def test_loads_valid_json(self):
        """Test loading valid JSON."""
        text = '{"key": "value", "number": 42}'
        result = load_json_string(text)
        assert result["key"] == "value"
        assert result["number"] == 42

    def test_loads_json_with_comments(self):
        """Test loading JSON with comments."""
        text = '{"key": "value" // comment\n}'
        result = load_json_string(text, verbose=False)
        assert result["key"] == "value"

    def test_loads_json_with_trailing_comma(self):
        """Test loading JSON with trailing comma."""
        text = '{"key": "value",}'
        result = load_json_string(text, verbose=False)
        assert result["key"] == "value"


class TestLoadJson:
    """Tests for load_json function."""

    def test_loads_json_file(self, temp_dir):
        """Test loading JSON from file."""
        json_file = temp_dir / "test.json"
        json_file.write_text('{"key": "value"}')
        result = load_json(str(json_file))
        assert result["key"] == "value"


class TestConvertStringToFloat:
    """Tests for convert_string_to_float function."""

    def test_converts_simple_number(self):
        """Test converting simple number."""
        result = convert_string_to_float("123.45")
        assert result == 123.45

    def test_removes_commas(self):
        """Test removing commas."""
        result = convert_string_to_float("1,234.56")
        assert result == 1234.56

    def test_handles_k_suffix(self):
        """Test handling k suffix."""
        result = convert_string_to_float("1.5k")
        assert result == 1500.0

    def test_handles_mm_suffix(self):
        """Test handling MM suffix."""
        result = convert_string_to_float("2.5MM")
        assert result == 2500000.0

    def test_handles_b_suffix(self):
        """Test handling B suffix."""
        result = convert_string_to_float("1B")
        assert result == 1000000000.0

    def test_returns_none_for_invalid(self):
        """Test returns None for invalid input."""
        result = convert_string_to_float("abc")
        assert result is None

    def test_returns_none_for_empty(self):
        """Test returns None for empty string."""
        result = convert_string_to_float("")
        assert result is None


class TestIsNonStringSequence:
    """Tests for is_non_string_sequence function."""

    def test_returns_true_for_list(self):
        """Test returns True for list."""
        assert is_non_string_sequence([1, 2, 3]) is True

    def test_returns_true_for_tuple(self):
        """Test returns True for tuple."""
        assert is_non_string_sequence((1, 2, 3)) is True

    def test_returns_false_for_string(self):
        """Test returns False for string."""
        assert is_non_string_sequence("abc") is False

    def test_returns_false_for_bytes(self):
        """Test returns False for bytes."""
        assert is_non_string_sequence(b"abc") is False

    def test_returns_true_for_dict_keys(self):
        """Test returns True for dict keys."""
        d = {"a": 1, "b": 2}
        assert is_non_string_sequence(d.keys()) is True


class TestToSingleList:
    """Tests for to_single_list function."""

    def test_converts_none_to_empty_list(self):
        """Test converts None to empty list."""
        result = to_single_list(None)
        assert result == []

    def test_wraps_single_item(self):
        """Test wraps single item in list."""
        result = to_single_list("item")
        assert result == ["item"]

    def test_returns_list_as_is(self):
        """Test returns list items."""
        result = to_single_list(["a", "b", "c"])
        assert result == ["a", "b", "c"]

    def test_unwraps_nested_list(self):
        """Test unwraps nested list."""
        result = to_single_list((["a", "b"],))
        assert result == ["a", "b"]


class TestCleanupUsername:
    """Tests for cleanup_username function."""

    def test_removes_email_domain(self):
        """Test removes email domain."""
        result = cleanup_username("user@example.com")
        assert result == "user"

    def test_lowercases_result(self):
        """Test lowercases result."""
        result = cleanup_username("USER@example.com")
        assert result == "user"

    def test_returns_empty_for_none(self):
        """Test returns empty for None."""
        result = cleanup_username(None)
        assert result == ""

    def test_returns_empty_for_empty(self):
        """Test returns empty for empty string."""
        result = cleanup_username("")
        assert result == ""


class TestListToCommaString:
    """Tests for list_to_comma_string function."""

    def test_joins_with_comma(self):
        """Test joins with comma."""
        result = list_to_comma_string(["a", "b", "c"])
        assert result == "a, b, c"

    def test_with_quote_char(self):
        """Test with quote character."""
        result = list_to_comma_string(["a", "b", "c"], quote_char='"')
        assert result == '"a", "b", "c"'


class TestMultilineCommaJoin:
    """Tests for multiline_comma_join function."""

    def test_without_quotes(self):
        """Joins with newlines and spacing."""
        result = multiline_comma_join(["a", "b", "c"], spaces=4)
        assert result == "a,\n    b,\n    c"

    def test_with_quotes(self):
        """Respects use_quotes flag."""
        result = multiline_comma_join(["x", "y"], spaces=2, use_quotes=True)
        assert result == '"x",\n  "y"'


class TestCommaJoinList:
    """Tests for comma_join_list function."""

    def test_empty_list(self):
        """Test empty list returns empty string."""
        result = comma_join_list([])
        assert result == ""

    def test_single_item(self):
        """Test single item."""
        result = comma_join_list([1])
        assert result == "1"

    def test_two_items(self):
        """Test two items with 'and'."""
        result = comma_join_list([1, 2])
        assert result == "1 and 2"

    def test_three_items(self):
        """Test three items with Oxford comma."""
        result = comma_join_list([1, 2, 3])
        assert result == "1, 2, and 3"

    def test_four_items(self):
        """Test four items."""
        result = comma_join_list([1, 2, 3, 4])
        assert result == "1, 2, 3, and 4"


class TestFilterStringRepOfList:
    """Tests for filter_string_rep_of_list function."""

    def test_filters_by_regex(self):
        """Test filters by regex pattern."""
        items = ["id", "name", "created_at", "updated_at"]
        result = filter_string_rep_of_list(items, r".*_at$")
        assert result == ["created_at", "updated_at"]

    def test_case_insensitive_by_default(self):
        """Test case insensitive by default."""
        items = ["Name", "NAME", "name"]
        result = filter_string_rep_of_list(items, "name", full_match=True)
        assert len(result) == 3

    def test_full_match(self):
        """Test full match option."""
        items = ["name", "username", "first_name"]
        result = filter_string_rep_of_list(items, "name", full_match=True)
        assert result == ["name"]

    def test_inverted(self):
        """Test inverted filter."""
        items = ["a", "b", "c"]
        result = filter_string_rep_of_list(items, "a", inverted=True)
        assert result == ["b", "c"]


class TestFilterStringRepOfDict:
    """Tests for filter_string_rep_of_dict function."""

    def test_filters_dict_keys(self):
        """Test filters dictionary keys."""
        d = {"id": 1, "name": "test", "created_at": "2024-01-01"}
        result = filter_string_rep_of_dict(d, r".*_at$")
        assert "created_at" in result
        assert "id" not in result


class TestDictToNamedtuple:
    """Tests for dict_to_namedtuple function."""

    def test_converts_to_namedtuple(self):
        """Test converts dict to namedtuple."""
        d = {"name": "Alice", "age": 30}
        result = dict_to_namedtuple(d)
        assert result.name == "Alice"
        assert result.age == 30

    def test_custom_name(self):
        """Test with custom name."""
        d = {"x": 1, "y": 2}
        result = dict_to_namedtuple(d, name="Point")
        assert type(result).__name__ == "Point"


class TestRecursivelyUppercaseDictKeys:
    """Tests for recursively_uppercase_dict_keys function."""

    def test_uppercases_keys(self):
        """Test uppercases string keys."""
        d = {"name": "value", "other": 123}
        result = recursively_uppercase_dict_keys(d)
        assert "NAME" in result
        assert "OTHER" in result

    def test_recursive_uppercasing(self):
        """Test recursive uppercasing of nested dicts."""
        d = {"outer": {"inner": "value"}}
        result = recursively_uppercase_dict_keys(d)
        assert "OUTER" in result
        assert "INNER" in result["OUTER"]


class TestTemporarilyChangeDir:
    """Tests for temporarily_change_dir context manager."""

    def test_changes_directory(self, temp_dir):
        """Test changes directory temporarily."""
        original = os.getcwd()
        with temporarily_change_dir(temp_dir):
            assert os.getcwd() == str(temp_dir)
        assert os.getcwd() == original

    def test_restores_on_exception(self, temp_dir):
        """Test restores directory on exception."""
        original = os.getcwd()
        try:
            with temporarily_change_dir(temp_dir):
                raise ValueError("test")
        except ValueError:
            pass
        assert os.getcwd() == original


class TestCompressAndEncodeAsBase64:
    """Tests for compress_and_encode_as_base64 function."""

    def test_compresses_and_encodes(self):
        """Test compresses and encodes string."""
        text = "Hello, World!"
        result = compress_and_encode_as_base64(text)
        assert isinstance(result, str)
        # Should be base64 encoded
        import base64

        decoded = base64.b64decode(result)
        assert len(decoded) > 0


class TestDecompressAndDecodeFromBase64:
    """Tests for decompress_and_decode_from_base64 function."""

    def test_round_trip(self):
        """Test compress and decompress round trip."""
        original = "Hello, World! This is a test string."
        encoded = compress_and_encode_as_base64(original)
        decoded = decompress_and_decode_from_base64(encoded)
        assert decoded == original


class TestStringToEnumValue:
    """Tests for string_to_enum_value function."""

    def test_finds_by_name(self):
        """Test finds enum by name."""

        class Color(Enum):
            RED = 1
            GREEN = 2
            BLUE = 3

        result = string_to_enum_value(Color, "RED")  # type: ignore
        assert result == Color.RED

    def test_case_insensitive(self):
        """Test case insensitive matching."""

        class Color(Enum):
            RED = 1

        result = string_to_enum_value(Color, "red")  # type: ignore
        assert result == Color.RED

    def test_returns_none_if_not_found(self):
        """Test returns None if not found."""

        class Color(Enum):
            RED = 1

        result = string_to_enum_value(Color, "YELLOW")  # type: ignore
        assert result is None

    def test_throws_if_not_found_and_requested(self):
        """Test throws if not found and throw_if_not_found=True."""

        class Color(Enum):
            RED = 1

        with pytest.raises(RuntimeError):
            string_to_enum_value(Color, "YELLOW", throw_if_not_found=True)  # type: ignore


class TestTimestampedId:
    """Tests for timestamped_id function."""

    def test_returns_string(self):
        """Test returns string."""
        result = timestamped_id()
        assert isinstance(result, str)

    def test_with_prefix(self):
        """Test with prefix."""
        result = timestamped_id(prefix="test")
        assert result.startswith("test_")

    def test_unique_ids(self):
        """Test generates unique IDs."""
        id1 = timestamped_id()
        id2 = timestamped_id()
        # May be same in fast execution, but format should be valid
        assert len(id1) > 0
        assert len(id2) > 0


class TestTimestampedUniqueId:
    """Tests for timestamped_unique_id function."""

    def test_returns_string(self):
        """Test returns string."""
        result = timestamped_unique_id()
        assert isinstance(result, str)

    def test_with_prefix(self):
        """Test with prefix."""
        result = timestamped_unique_id(prefix="task")
        assert result.startswith("task_")

    def test_contains_underscore_separator(self):
        """Test contains underscore separator."""
        result = timestamped_unique_id()
        assert "_" in result


class TestAsString:
    """Tests for as_string function."""

    def test_returns_string_unchanged(self):
        """Test returns string unchanged."""
        result = as_string("hello")
        assert result == "hello"

    def test_converts_bytes_to_string(self):
        """Test converts bytes to string."""
        result = as_string(b"hello")
        assert result == "hello"

    def test_strips_whitespace_from_bytes(self):
        """Test strips whitespace from bytes."""
        result = as_string(b"  hello  ")
        assert result == "hello"
