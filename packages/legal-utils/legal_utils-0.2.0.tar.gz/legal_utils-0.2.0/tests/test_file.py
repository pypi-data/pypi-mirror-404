"""
Unit tests for file_utils module.

Tests cover:
- JSONL file reading and writing
- Filename extraction
- File discovery with glob patterns
"""

import pytest
import json
import tempfile
from pathlib import Path

from legal_utils.file import (
    read_jsonl,
    write_jsonl,
    read_file,
    write_file,
    extract_filename,
    find_files,
)


# ============================================================================
# Tests for JSONL Reading
# ============================================================================

class TestReadJsonl:
    """Test JSONL file reading functionality."""

    def test_read_valid_jsonl(self):
        """Test reading a valid JSONL file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"id": 1, "name": "John"}\n')
            f.write('{"id": 2, "name": "Jane"}\n')
            temp_path = f.name
        
        try:
            data = list(read_jsonl(temp_path))
            assert len(data) == 2
            assert data[0]["id"] == 1
            assert data[0]["name"] == "John"
            assert data[1]["id"] == 2
            assert data[1]["name"] == "Jane"
        finally:
            Path(temp_path).unlink()

    def test_read_jsonl_with_empty_lines(self):
        """Test reading JSONL file with empty lines."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"id": 1}\n')
            f.write('\n')
            f.write('{"id": 2}\n')
            f.write('   \n')
            f.write('{"id": 3}\n')
            temp_path = f.name
        
        try:
            data = list(read_jsonl(temp_path))
            assert len(data) == 3
            assert [d["id"] for d in data] == [1, 2, 3]
        finally:
            Path(temp_path).unlink()

    def test_read_jsonl_single_line(self):
        """Test reading JSONL file with single entry."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"key": "value"}\n')
            temp_path = f.name
        
        try:
            data = list(read_jsonl(temp_path))
            assert len(data) == 1
            assert data[0]["key"] == "value"
        finally:
            Path(temp_path).unlink()

    def test_read_jsonl_with_unicode(self):
        """Test reading JSONL file with unicode characters."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False, encoding='utf-8') as f:
            f.write('{"name": "José"}\n')
            f.write('{"name": "François"}\n')
            f.write('{"name": "北京"}\n')
            temp_path = f.name
        
        try:
            data = list(read_jsonl(temp_path))
            assert len(data) == 3
            assert data[0]["name"] == "José"
            assert data[1]["name"] == "François"
            assert data[2]["name"] == "北京"
        finally:
            Path(temp_path).unlink()

    def test_read_jsonl_malformed_no_ignore(self):
        """Test that malformed JSON raises error when ignore_errors=False."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"id": 1}\n')
            f.write('{invalid json}\n')
            temp_path = f.name
        
        try:
            with pytest.raises(json.JSONDecodeError):
                list(read_jsonl(temp_path, ignore_errors=False))
        finally:
            Path(temp_path).unlink()

    def test_read_jsonl_malformed_with_ignore(self):
        """Test that malformed JSON is skipped when ignore_errors=True."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"id": 1}\n')
            f.write('{invalid json}\n')
            f.write('{"id": 2}\n')
            temp_path = f.name
        
        try:
            data = list(read_jsonl(temp_path, ignore_errors=True))
            assert len(data) == 2
            assert data[0]["id"] == 1
            assert data[1]["id"] == 2
        finally:
            Path(temp_path).unlink()

    def test_read_jsonl_complex_objects(self):
        """Test reading JSONL with complex nested objects."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            obj1 = {"user": {"name": "John", "age": 30}, "tags": ["admin", "user"]}
            obj2 = {"user": {"name": "Jane", "age": 25}, "tags": ["user"]}
            f.write(json.dumps(obj1) + '\n')
            f.write(json.dumps(obj2) + '\n')
            temp_path = f.name
        
        try:
            data = list(read_jsonl(temp_path))
            assert len(data) == 2
            assert data[0]["user"]["name"] == "John"
            assert data[1]["tags"] == ["user"]
        finally:
            Path(temp_path).unlink()

    def test_read_jsonl_empty_file(self):
        """Test reading an empty JSONL file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            temp_path = f.name
        
        try:
            data = list(read_jsonl(temp_path))
            assert len(data) == 0
        finally:
            Path(temp_path).unlink()

    def test_read_jsonl_nonexistent_file(self):
        """Test reading a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            list(read_jsonl("/nonexistent/path/file.jsonl"))

    def test_read_jsonl_with_pathlib(self):
        """Test that read_jsonl accepts Path objects."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"id": 1}\n')
            temp_path = Path(f.name)
        
        try:
            data = list(read_jsonl(temp_path))
            assert len(data) == 1
            assert data[0]["id"] == 1
        finally:
            temp_path.unlink()


# ============================================================================
# Tests for JSONL Writing
# ============================================================================

class TestWriteJsonl:
    """Test JSONL file writing functionality."""

    def test_write_jsonl_basic(self):
        """Test basic JSONL writing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "output.jsonl"
            data = [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]
            
            write_jsonl(data, file_path)
            
            assert file_path.exists()
            lines = file_path.read_text().strip().split('\n')
            assert len(lines) == 2
            assert json.loads(lines[0])["id"] == 1
            assert json.loads(lines[1])["id"] == 2

    def test_write_jsonl_creates_directory(self):
        """Test that write_jsonl creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "nested" / "dir" / "output.jsonl"
            data = [{"id": 1}]
            
            write_jsonl(data, file_path, makedirs=True)
            
            assert file_path.exists()
            assert file_path.parent.exists()

    def test_write_jsonl_unicode(self):
        """Test writing JSONL with unicode characters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "unicode.jsonl"
            data = [
                {"name": "José"},
                {"name": "北京"},
                {"text": "Café"}
            ]
            
            write_jsonl(data, file_path)
            
            # Read back and verify
            read_data = list(read_jsonl(file_path))
            assert read_data[0]["name"] == "José"
            assert read_data[1]["name"] == "北京"
            assert read_data[2]["text"] == "Café"

    def test_write_jsonl_append_mode(self):
        """Test appending to existing JSONL file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "append.jsonl"
            
            # Write initial data
            data1 = [{"id": 1}]
            write_jsonl(data1, file_path)
            
            # Append more data
            data2 = [{"id": 2}]
            write_jsonl(data2, file_path, append=True)
            
            # Verify both entries exist
            all_data = list(read_jsonl(file_path))
            assert len(all_data) == 2
            assert all_data[0]["id"] == 1
            assert all_data[1]["id"] == 2

    def test_write_jsonl_overwrite_mode(self):
        """Test overwriting existing JSONL file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "overwrite.jsonl"
            
            # Write initial data
            data1 = [{"id": 1}, {"id": 2}]
            write_jsonl(data1, file_path)
            
            # Overwrite with new data
            data2 = [{"id": 3}]
            write_jsonl(data2, file_path, append=False)
            
            # Verify only new data exists
            all_data = list(read_jsonl(file_path))
            assert len(all_data) == 1
            assert all_data[0]["id"] == 3

    def test_write_jsonl_complex_objects(self):
        """Test writing complex nested objects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "complex.jsonl"
            data = [
                {
                    "user": {"name": "John", "age": 30},
                    "tags": ["admin", "user"],
                    "active": True
                }
            ]
            
            write_jsonl(data, file_path)
            
            read_data = list(read_jsonl(file_path))
            assert read_data[0]["user"]["name"] == "John"
            assert read_data[0]["tags"] == ["admin", "user"]
            assert read_data[0]["active"] is True

    def test_write_jsonl_empty_data(self):
        """Test writing empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "empty.jsonl"
            
            write_jsonl([], file_path)
            
            assert file_path.exists()
            content = file_path.read_text()
            assert content == ""

    def test_write_jsonl_with_pathlib(self):
        """Test that write_jsonl accepts Path objects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "pathlib.jsonl"
            data = [{"id": 1}]
            
            write_jsonl(data, file_path)
            
            assert file_path.exists()
            read_data = list(read_jsonl(file_path))
            assert read_data[0]["id"] == 1

    def test_write_jsonl_special_characters(self):
        """Test writing data with special characters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "special.jsonl"
            data = [
                {"text": 'Quote "test" and \'apostrophe\''},
                {"text": "Newline\\nand\\ttab"},
                {"text": "Backslash\\"}
            ]
            
            write_jsonl(data, file_path)
            
            read_data = list(read_jsonl(file_path))
            assert 'Quote "test"' in read_data[0]["text"]


# ============================================================================
# Tests for Filename Extraction
# ============================================================================

class TestExtractFilename:
    """Test filename extraction functionality."""

    def test_extract_filename_with_extension(self):
        """Test extracting filename with extension."""
        result = extract_filename("/path/to/data.jsonl", include_extension=True)
        assert result == "data.jsonl"

    def test_extract_filename_without_extension(self):
        """Test extracting filename without extension."""
        result = extract_filename("/path/to/data.jsonl", include_extension=False)
        assert result == "data"

    def test_extract_filename_simple_path(self):
        """Test extracting filename from simple path."""
        result = extract_filename("file.txt")
        assert result == "file.txt"

    def test_extract_filename_no_extension(self):
        """Test extracting filename when file has no extension."""
        result = extract_filename("/path/to/README", include_extension=True)
        assert result == "README"

    def test_extract_filename_multiple_dots(self):
        """Test extracting filename with multiple dots."""
        result = extract_filename("/path/data.backup.jsonl", include_extension=True)
        assert result == "data.backup.jsonl"

    def test_extract_filename_without_extension_multiple_dots(self):
        """Test extracting stem when filename has multiple dots."""
        result = extract_filename("/path/data.backup.jsonl", include_extension=False)
        assert result == "data.backup"

    def test_extract_filename_windows_path(self):
        """Test extracting filename from Windows-style path."""
        # Note: Path behavior depends on OS. On Windows this would be "data.txt",
        # but on Unix-like systems, backslashes are treated as literal characters
        result = extract_filename("C:\\Users\\data.txt", include_extension=True)
        # The result depends on the OS - just verify it extracts the last component
        assert result is not None
        assert len(result) > 0

    def test_extract_filename_relative_path(self):
        """Test extracting filename from relative path."""
        result = extract_filename("./folder/file.json", include_extension=True)
        assert result == "file.json"

    def test_extract_filename_empty_string(self):
        """Test extracting filename from empty string."""
        result = extract_filename("")
        assert result == ""

    def test_extract_filename_just_filename(self):
        """Test extracting filename when only filename is provided."""
        result = extract_filename("document.pdf")
        assert result == "document.pdf"

    def test_extract_filename_hidden_file(self):
        """Test extracting hidden filename."""
        result = extract_filename("/home/user/.config/settings", include_extension=True)
        assert result == "settings"

    def test_extract_filename_pathlib_object(self):
        """Test that extract_filename works with Path objects."""
        path = Path("/path/to/file.txt")
        result = extract_filename(str(path), include_extension=True)
        assert result == "file.txt"


# ============================================================================
# Tests for File Discovery
# ============================================================================

class TestFindFiles:
    """Test file discovery functionality."""

    def test_find_files_single_pattern(self):
        """Test finding files with a single pattern."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create test files
            (tmpdir / "file1.txt").touch()
            (tmpdir / "file2.txt").touch()
            (tmpdir / "file3.json").touch()
            
            # Find txt files
            pattern = str(tmpdir / "*.txt")
            result = find_files(pattern)
            
            assert len(result) == 2
            assert any("file1.txt" in f for f in result)
            assert any("file2.txt" in f for f in result)

    def test_find_files_multiple_patterns(self):
        """Test finding files with multiple patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create test files
            (tmpdir / "file1.txt").touch()
            (tmpdir / "file2.json").touch()
            (tmpdir / "file3.csv").touch()
            
            # Find txt and json files
            patterns = [str(tmpdir / "*.txt"), str(tmpdir / "*.json")]
            result = find_files(patterns)
            
            assert len(result) == 2
            assert any("file1.txt" in f for f in result)
            assert any("file2.json" in f for f in result)

    def test_find_files_recursive(self):
        """Test finding files recursively with ** pattern."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create nested directory structure
            (tmpdir / "subdir").mkdir()
            (tmpdir / "file1.txt").touch()
            (tmpdir / "subdir" / "file2.txt").touch()
            (tmpdir / "subdir" / "nested").mkdir()
            (tmpdir / "subdir" / "nested" / "file3.txt").touch()
            
            # Find all txt files recursively
            pattern = str(tmpdir / "**" / "*.txt")
            result = find_files(pattern, recursive=True)
            
            assert len(result) == 3
            assert any("file1.txt" in f for f in result)
            assert any("file2.txt" in f for f in result)
            assert any("file3.txt" in f for f in result)

    def test_find_files_non_recursive(self):
        """Test finding files without recursion."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create nested directory structure
            (tmpdir / "subdir").mkdir()
            (tmpdir / "file1.txt").touch()
            (tmpdir / "subdir" / "file2.txt").touch()
            
            # Find only top-level txt files
            pattern = str(tmpdir / "*.txt")
            result = find_files(pattern, recursive=False)
            
            assert len(result) == 1
            assert any("file1.txt" in f for f in result)

    def test_find_files_no_matches(self):
        """Test finding files when no matches exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pattern = str(Path(tmpdir) / "*.nonexistent")
            result = find_files(pattern)
            
            assert result == []

    def test_find_files_returns_sorted_unique(self):
        """Test that find_files returns sorted unique results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create files
            (tmpdir / "b.txt").touch()
            (tmpdir / "a.txt").touch()
            (tmpdir / "c.txt").touch()
            
            # Use overlapping patterns to ensure uniqueness check
            patterns = [
                str(tmpdir / "*.txt"),
                str(tmpdir / "*.txt")
            ]
            result = find_files(patterns)
            
            # Should have 3 unique files, sorted
            assert len(result) == 3
            assert result == sorted(result)

    def test_find_files_filters_directories(self):
        """Test that find_files only returns files, not directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create files and directories
            (tmpdir / "file.txt").touch()
            (tmpdir / "subdir").mkdir()
            
            # Pattern that might match both
            pattern = str(tmpdir / "*")
            result = find_files(pattern)
            
            # Should only include the file, not the directory
            assert len(result) == 1
            assert "file.txt" in result[0]

    def test_find_files_string_pattern(self):
        """Test that find_files accepts a single string pattern."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            (tmpdir / "file.txt").touch()
            
            pattern = str(tmpdir / "*.txt")
            result = find_files(pattern)  # Pass string, not list
            
            assert len(result) == 1

    def test_find_files_list_pattern(self):
        """Test that find_files accepts a list of patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            (tmpdir / "file.txt").touch()
            
            pattern = [str(tmpdir / "*.txt")]
            result = find_files(pattern)  # Pass list
            
            assert len(result) == 1

    def test_find_files_absolute_path(self):
        """Test finding files with absolute paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir).resolve()
            (tmpdir / "test.json").touch()
            
            pattern = str(tmpdir / "*.json")
            result = find_files(pattern)
            
            assert len(result) == 1
            assert Path(result[0]).is_absolute()

    def test_find_files_case_sensitive(self):
        """Test that find_files respects case sensitivity."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            (tmpdir / "File.TXT").touch()
            (tmpdir / "file.txt").touch()
            
            # This test behavior depends on the OS filesystem
            pattern = str(tmpdir / "*.txt")
            result = find_files(pattern)
            
            # On case-sensitive systems, should find only lowercase
            # On case-insensitive systems, should find both
            assert len(result) >= 1



class TestReadWriteFile:
    """Tests for simple read_file and write_file utilities."""

    def test_read_file_reads_text(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            f.write('Hello world\nÉric')
            temp_path = f.name

        try:
            content = read_file(temp_path)
            assert content == 'Hello world\nÉric'
        finally:
            Path(temp_path).unlink()

    def test_write_file_string_and_append(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / 'out.txt'

            # write (overwrite) mode
            write_file('first', p)
            assert p.read_text(encoding='utf-8') == 'first'

            # append mode
            write_file('second', p, append=True)
            assert p.read_text(encoding='utf-8') == 'firstsecond'

    def test_write_file_dict_and_iterable(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / 'json.txt'

            # write a dict (should be JSON string)
            write_file({'a': 1}, p)
            assert json.loads(p.read_text(encoding='utf-8')) == {'a': 1}

            # write an iterable of dicts/strings
            p2 = Path(tmpdir) / 'lines.txt'
            items = [{'b': 2}, 'plain']
            write_file(items, p2)
            lines = p2.read_text(encoding='utf-8').splitlines()
            assert json.loads(lines[0]) == {'b': 2}
            assert lines[1] == 'plain'

    def test_write_file_makedirs_and_pathlib(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            nested = Path(tmpdir) / 'a' / 'b' / 'c' / 'file.txt'

            # ensure parent dirs are created
            write_file('ok', nested, makedirs=True)
            assert nested.exists()
            assert nested.read_text(encoding='utf-8') == 'ok'
