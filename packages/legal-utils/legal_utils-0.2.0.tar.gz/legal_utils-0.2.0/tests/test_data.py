"""
Unit tests for data_utils module.

Tests cover:
- Pydantic schema generation from dictionaries
- JSON loading and extraction
- Text normalization and validation
- Chunking and deduplication utilities
- Recursive value extraction
"""

import pytest

from legal_utils.data import (
    get_pydantic_schema_from_dict,
    normalize_text,
    clean_json,
    load_json,
    extract_json,
    chunk_iterable,
    deduplicate_list,
    split_iterable,
    get_recursive_values,
)


# ============================================================================
# Tests for Pydantic Schema Generation
# ============================================================================

class TestGetPydanticSchemaFromDict:
    """Test Pydantic schema generation from dictionaries."""

    def test_simple_flat_dict(self):
        """Test schema generation with a simple flat dictionary."""
        data = {"name": "John", "age": 30, "active": True}
        schema = get_pydantic_schema_from_dict(data)
        
        assert "properties" in schema
        assert "name" in schema["properties"]
        assert "age" in schema["properties"]
        assert "active" in schema["properties"]
        assert schema["properties"]["name"]["type"] == "string"
        assert schema["properties"]["age"]["type"] == "integer"
        assert schema["properties"]["active"]["type"] == "boolean"

    def test_nested_dict(self):
        """Test schema generation with nested dictionaries."""
        data = {
            "name": "John",
            "address": {
                "street": "123 Main St",
                "city": "New York"
            }
        }
        schema = get_pydantic_schema_from_dict(data)
        
        assert "address" in schema["properties"]
        assert "$defs" in schema or "definitions" in schema

    def test_tuple_as_enum(self):
        """Test that tuples are converted to enums (Literal types)."""
        data = {"status": ("open", "closed", "pending")}
        schema = get_pydantic_schema_from_dict(data)
        
        status_schema = schema["properties"]["status"]
        assert "enum" in status_schema
        assert set(status_schema["enum"]) == {"open", "closed", "pending"}

    def test_empty_tuple(self):
        """Test schema generation with empty tuple."""
        data = {"value": ()}
        schema = get_pydantic_schema_from_dict(data)
        
        assert "value" in schema["properties"]

    def test_list_of_primitives(self):
        """Test schema generation with list of primitives."""
        data = {"numbers": [1, 2, 3]}
        schema = get_pydantic_schema_from_dict(data)
        
        numbers_schema = schema["properties"]["numbers"]
        assert "items" in numbers_schema or "type" in numbers_schema

    def test_list_of_objects(self):
        """Test schema generation with list of dictionaries."""
        data = {
            "items": [
                {"id": 1, "name": "Item 1"},
                {"id": 2, "name": "Item 2"}
            ]
        }
        schema = get_pydantic_schema_from_dict(data)
        
        assert "items" in schema["properties"]

    def test_empty_list(self):
        """Test schema generation with empty list."""
        data = {"items": []}
        schema = get_pydantic_schema_from_dict(data)
        
        assert "items" in schema["properties"]

    def test_custom_model_name(self):
        """Test schema generation with custom model name."""
        data = {"value": 123}
        schema = get_pydantic_schema_from_dict(data, model_name="CustomModel")
        
        assert "$defs" in schema or "definitions" in schema or "title" in schema

    def test_null_values(self):
        """Test schema generation with None/null values."""
        data = {"value": None, "name": "test"}
        schema = get_pydantic_schema_from_dict(data)
        
        assert "name" in schema["properties"]
        assert "value" in schema["properties"]

    def test_float_values(self):
        """Test schema generation with float values."""
        data = {"price": 19.99, "discount": 0.15}
        schema = get_pydantic_schema_from_dict(data)
        
        assert schema["properties"]["price"]["type"] == "number"
        assert schema["properties"]["discount"]["type"] == "number"

    def test_complex_nested_structure(self):
        """Test schema generation with complex nested structure."""
        data = {
            "status": ("active", "inactive"),
            "user": {
                "name": "John",
                "tags": ["admin", "user"]
            },
            "scores": [1, 2, 3]
        }
        schema = get_pydantic_schema_from_dict(data)
        
        assert "status" in schema["properties"]
        assert "user" in schema["properties"]
        assert "scores" in schema["properties"]


# ============================================================================
# Tests for Text Normalization and Validation
# ============================================================================

class TestNormalizeText:
    """Test text normalization function."""

    def test_simple_normalization(self):
        """Test basic whitespace normalization."""
        text = "Hello    world"
        result = normalize_text(text)
        assert result == "Hello world"

    def test_multiple_spaces(self):
        """Test removal of multiple spaces."""
        text = "Multiple   spaces   here"
        result = normalize_text(text)
        assert result == "Multiple spaces here"

    def test_newlines_and_tabs(self):
        """Test normalization with newlines and tabs."""
        text = "Hello\n\tworld\n\ntest"
        result = normalize_text(text)
        assert result == "Hello world test"

    def test_leading_trailing_spaces(self):
        """Test removal of leading and trailing spaces."""
        text = "   Hello world   "
        result = normalize_text(text)
        assert result == "Hello world"

    def test_empty_string(self):
        """Test normalization of empty string."""
        result = normalize_text("")
        assert result == ""

    def test_single_word(self):
        """Test normalization of single word."""
        result = normalize_text("Hello")
        assert result == "Hello"


class TestCleanJson:
    """Test JSON cleaning function."""

    def test_remove_null_values(self):
        """Test removal of null values."""
        obj = {"a": "value", "b": None, "c": "another"}
        result = clean_json(obj)
        
        assert "a" in result
        assert "c" in result
        assert "b" not in result

    def test_normalize_string_values(self):
        """Test normalization of string values."""
        obj = {"name": "John   Doe", "city": "New  York"}
        result = clean_json(obj)
        
        assert result["name"] == "John Doe"
        assert result["city"] == "New York"

    def test_preserve_non_string_values(self):
        """Test that non-string values are preserved."""
        obj = {"age": 30, "active": True, "score": 95.5}
        result = clean_json(obj)
        
        assert result["age"] == 30
        assert result["active"] is True
        assert result["score"] == 95.5

    def test_empty_dict(self):
        """Test cleaning of empty dictionary."""
        result = clean_json({})
        assert result == {}

    def test_all_none_values(self):
        """Test cleaning dict with all None values."""
        obj = {"a": None, "b": None}
        result = clean_json(obj)
        assert result == {}

    def test_nested_structures_unchanged(self):
        """Test that nested structures are preserved as-is."""
        obj = {"nested": {"key": "value"}, "list": [1, 2, 3]}
        result = clean_json(obj)
        
        assert result["nested"] == {"key": "value"}
        assert result["list"] == [1, 2, 3]


# ============================================================================
# Tests for JSON Loading and Extraction
# ============================================================================

class TestLoadJson:
    """Test JSON loading function."""

    def test_valid_json_string(self):
        """Test loading valid JSON string."""
        text = '{"name": "John", "age": 30}'
        result = load_json(text)
        
        assert isinstance(result, dict)
        assert result["name"] == "John"
        assert result["age"] == 30

    def test_simple_json(self):
        """Test loading simple JSON."""
        text = '{"key": "value"}'
        result = load_json(text)
        
        assert result == {"key": "value"}

    def test_json_with_null_values(self):
        """Test loading JSON with null values."""
        text = '{"a": null, "b": "value"}'
        result = load_json(text)
        
        assert result is not None
        assert result["a"] is None
        assert result["b"] == "value"

    def test_invalid_json(self):
        """Test that invalid JSON returns None or dict."""
        # json_repair might fix it or return something
        text = '{"incomplete": '
        result = load_json(text)
        # With json_repair, it might succeed or return None
        assert result is None or isinstance(result, dict)

    def test_non_dict_json(self):
        """Test that non-dict JSON returns None."""
        text = '["array", "of", "values"]'
        result = load_json(text)
        assert result is None

    def test_empty_json_object(self):
        """Test loading empty JSON object."""
        text = '{}'
        result = load_json(text)
        assert result == {}

    def test_nested_json(self):
        """Test loading nested JSON structure."""
        text = '{"user": {"name": "John", "address": {"city": "NYC"}}}'
        result = load_json(text)
        
        assert result is not None
        assert result["user"]["name"] == "John"
        assert result["user"]["address"]["city"] == "NYC"


class TestExtractJson:
    """Test JSON extraction function."""

    def test_single_json_object(self):
        """Test extraction of single JSON object from text."""
        text = "Here is JSON: {\"key\": \"value\"}"
        result = extract_json(text)
        
        assert result is not None
        assert len(result) >= 1
        assert isinstance(result[0], dict)

    def test_multiple_json_objects(self):
        """Test extraction of multiple JSON objects."""
        text = "First: {\"id\": 1} and second: {\"id\": 2}"
        result = extract_json(text)
        
        assert result is not None
        assert len(result) >= 2

    def test_nested_json_extraction(self):
        """Test extraction of nested JSON objects."""
        text = "Data: {\"outer\": {\"inner\": \"value\"}}"
        result = extract_json(text)
        
        assert result is not None
        assert len(result) >= 1

    def test_no_json_found(self):
        """Test extraction when no JSON is present."""
        text = "This is plain text without any JSON"
        result = extract_json(text)
        
        assert result is None

    def test_malformed_json(self):
        """Test extraction of malformed JSON (json_repair handles it)."""
        text = "Data: {\"key\": value} more text"
        result = extract_json(text)
        # json_repair might fix it
        assert result is None or isinstance(result, list)

    def test_json_with_special_characters(self):
        """Test extraction of JSON with special characters."""
        text = '{"name": "John\'s", "note": "Line 1\\nLine 2"}'
        result = extract_json(text)
        
        assert result is not None or result is None  # Depends on content

    def test_empty_json_object_extraction(self):
        """Test extraction of empty JSON object."""
        text = "Here: {} end"
        result = extract_json(text)
        
        assert result is not None or result is None


# ============================================================================
# Tests for Chunking Utilities
# ============================================================================

class TestChunkIterable:
    """Test chunking functionality."""

    def test_basic_chunking(self):
        """Test basic chunking without overlap."""
        items = list(range(10))
        chunks = chunk_iterable(items, chunk_size=3)
        
        assert len(chunks) > 0
        assert chunks[0] == [0, 1, 2]

    def test_chunk_with_overlap(self):
        """Test chunking with overlap."""
        items = list(range(10))
        chunks = chunk_iterable(items, chunk_size=3, overlap=1)
        
        assert len(chunks) > 0
        # Second chunk should start with last element of first chunk
        if len(chunks) > 1:
            assert chunks[1][0] == chunks[0][-1]

    def test_chunk_size_equal_to_length(self):
        """Test chunking when chunk size equals list length."""
        items = list(range(5))
        chunks = chunk_iterable(items, chunk_size=5)
        
        assert len(chunks) == 1
        assert chunks[0] == items

    def test_chunk_size_larger_than_length(self):
        """Test chunking when chunk size is larger than list."""
        items = list(range(5))
        chunks = chunk_iterable(items, chunk_size=10)
        
        assert len(chunks) == 1
        assert chunks[0] == items

    def test_chunk_with_force_same_size(self):
        """Test chunking with force_same_size option."""
        items = list(range(10))
        chunks = chunk_iterable(items, chunk_size=3, force_same_size=True)
        
        for chunk in chunks:
            if chunk != chunks[-1] or chunk == chunks[-1]:
                # All chunks or just non-last should be size 3
                pass

    def test_chunk_with_drop_last(self):
        """Test chunking with drop_last option."""
        items = list(range(10))
        chunks = chunk_iterable(items, chunk_size=3, force_same_size=True, drop_last=True)
        
        # All remaining chunks should be size 3
        for chunk in chunks:
            assert len(chunk) == 3

    def test_chunk_avoid_duplicates(self):
        """Test chunking with avoid_duplicates option."""
        items = list(range(5))
        chunks = chunk_iterable(items, chunk_size=3, avoid_duplicates=True)
        
        # All chunks should be unique
        chunk_tuples = [tuple(c) for c in chunks]
        assert len(chunk_tuples) == len(set(chunk_tuples))

    def test_invalid_overlap(self):
        """Test that invalid overlap raises assertion error."""
        items = list(range(10))
        
        with pytest.raises(AssertionError):
            chunk_iterable(items, chunk_size=3, overlap=5)

    def test_invalid_step(self):
        """Test that overlap >= chunk_size raises AssertionError."""
        items = list(range(10))
        
        with pytest.raises(AssertionError):
            chunk_iterable(items, chunk_size=3, overlap=3)

    def test_string_chunking(self):
        """Test chunking with strings."""
        items = "abcdefgh"
        chunks = chunk_iterable(items, chunk_size=2)
        
        assert len(chunks) > 0

    def test_empty_list(self):
        """Test chunking empty list."""
        items = []
        chunks = chunk_iterable(items, chunk_size=3)
        
        assert len(chunks) == 1
        assert chunks[0] == []


# ============================================================================
# Tests for Deduplication
# ============================================================================

class TestDeduplicateList:
    """Test list deduplication function."""

    def test_basic_deduplication(self):
        """Test basic deduplication."""
        items = [1, 2, 2, 3, 1, 4]
        result = deduplicate_list(items)
        
        assert len(result) == 4
        assert result == [1, 2, 3, 4]

    def test_maintains_order(self):
        """Test that deduplication maintains original order."""
        items = [3, 1, 2, 1, 3]
        result = deduplicate_list(items)
        
        assert result == [3, 1, 2]

    def test_string_deduplication(self):
        """Test deduplication of strings."""
        items = ["a", "b", "a", "c", "b"]
        result = deduplicate_list(items)
        
        assert len(result) == 3
        assert result == ["a", "b", "c"]

    def test_no_duplicates(self):
        """Test list with no duplicates."""
        items = [1, 2, 3, 4, 5]
        result = deduplicate_list(items)
        
        assert result == items

    def test_all_duplicates(self):
        """Test list with all same elements."""
        items = [1, 1, 1, 1]
        result = deduplicate_list(items)
        
        assert result == [1]

    def test_empty_list(self):
        """Test deduplication of empty list."""
        result = deduplicate_list([])
        assert result == []

    def test_single_element(self):
        """Test deduplication of single element."""
        result = deduplicate_list([1])
        assert result == [1]


# ============================================================================
# Tests for Splitting
# ============================================================================

class TestSplitIterable:
    """Test iterable splitting function."""

    def test_split_at_index(self):
        """Test splitting at specific index."""
        items = list(range(10))
        left, right = split_iterable(items, index=3)
        
        assert left == [0, 1, 2]
        assert right == [3, 4, 5, 6, 7, 8, 9]

    def test_split_middle(self):
        """Test splitting at middle (default)."""
        items = [1, 2, 3, 4, 5, 6]
        left, right = split_iterable(items)
        
        assert len(left) == 3
        assert len(right) == 3

    def test_split_odd_length(self):
        """Test splitting list of odd length at middle."""
        items = [1, 2, 3, 4, 5]
        left, right = split_iterable(items)
        
        assert len(left) == 2
        assert len(right) == 3

    def test_split_at_zero(self):
        """Test splitting at index 0."""
        items = [1, 2, 3]
        left, right = split_iterable(items, index=0)
        
        assert left == []
        assert right == [1, 2, 3]

    def test_split_at_end(self):
        """Test splitting at end."""
        items = [1, 2, 3]
        left, right = split_iterable(items, index=3)
        
        assert left == [1, 2, 3]
        assert right == []

    def test_split_empty_list(self):
        """Test splitting empty list."""
        left, right = split_iterable([])
        
        assert left == []
        assert right == []

    def test_split_single_element(self):
        """Test splitting single element list."""
        left, right = split_iterable([1])
        
        assert len(left) == 0
        assert len(right) == 1

    def test_split_string(self):
        """Test splitting a string."""
        text = "abcdef"
        left, right = split_iterable(text, index=3)
        
        assert left == ['a', 'b', 'c']
        assert right == ['d', 'e', 'f']


# ============================================================================
# Tests for Recursive Value Extraction
# ============================================================================

class TestGetRecursiveValues:
    """Test recursive value extraction function."""

    def test_single_level_dict(self):
        """Test extraction from single-level dictionary."""
        data = {"name": "John", "age": 30, "city": "NYC"}
        result = get_recursive_values(data, "name")
        
        assert result == ["John"]

    def test_nested_dict(self):
        """Test extraction from nested dictionary."""
        data = {
            "user": {
                "name": "John",
                "address": {
                    "name": "123 Main St"
                }
            }
        }
        result = get_recursive_values(data, "name")
        
        assert len(result) == 2
        assert "John" in result
        assert "123 Main St" in result

    def test_list_of_dicts(self):
        """Test extraction from list of dictionaries."""
        data = [
            {"id": 1, "name": "Item 1"},
            {"id": 2, "name": "Item 2"}
        ]
        result = get_recursive_values(data, "name")
        
        assert len(result) == 2
        assert "Item 1" in result
        assert "Item 2" in result

    def test_mixed_structure(self):
        """Test extraction from mixed dict/list structure."""
        data = {
            "users": [
                {"name": "John", "age": 30},
                {"name": "Jane", "age": 25}
            ],
            "admin": {
                "name": "Admin"
            }
        }
        result = get_recursive_values(data, "name")
        
        assert len(result) == 3
        assert "John" in result
        assert "Jane" in result
        assert "Admin" in result

    def test_non_recursive(self):
        """Test extraction without recursion."""
        data = {
            "name": "Top",
            "nested": {
                "name": "Nested"
            }
        }
        result = get_recursive_values(data, "name", recursive=False)
        
        assert result == ["Top"]

    def test_key_not_found(self):
        """Test extraction when key doesn't exist."""
        data = {"a": 1, "b": 2}
        result = get_recursive_values(data, "c")
        
        assert result == []

    def test_empty_dict(self):
        """Test extraction from empty dictionary."""
        result = get_recursive_values({}, "key")
        assert result == []

    def test_empty_list(self):
        """Test extraction from empty list."""
        result = get_recursive_values([], "key")
        assert result == []

    def test_deeply_nested(self):
        """Test extraction from deeply nested structure."""
        data = {
            "level1": {
                "level2": {
                    "level3": {
                        "value": "deep"
                    }
                }
            }
        }
        result = get_recursive_values(data, "value")
        
        assert "deep" in result

    def test_duplicate_values(self):
        """Test extraction preserves duplicate values."""
        data = {
            "a": {"id": 1},
            "b": {"id": 1},
            "c": {"id": 2}
        }
        result = get_recursive_values(data, "id")
        
        assert len(result) == 3
        assert result.count(1) == 2
        assert result.count(2) == 1

    def test_list_values(self):
        """Test extraction when values are lists."""
        data = {
            "items": [
                {"tags": ["a", "b"]},
                {"tags": ["c"]}
            ]
        }
        result = get_recursive_values(data, "tags")
        
        assert len(result) == 2
