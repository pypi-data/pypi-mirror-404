"""
Utilities for file handling, including JSONL processing and file discovery.
"""

import json
import logging
import glob
from pathlib import Path
from typing import Iterable, List, Dict, Any, Union

# Configure logging
logger = logging.getLogger(__name__)

def read_file(file_path: str, encoding: str = "utf-8") -> str:
    """
    Simple function to read a file.

    Args:
        file_path (str): Path to the file to read
        encoding (str, optional): Encoding format. Defaults to "utf-8".

    Returns:
        str: Content of the file
    """
    with open(file_path, "r", encoding=encoding) as f:
        text = f.read()
    return text


def read_jsonl(file_path: Union[str, Path], ignore_errors: bool = False) -> Iterable[Dict[str, Any]]:
    """
    Read a .jsonl file and yield each line as a dictionary.

    Args:
        file_path (str, Path): Path to the .jsonl file.
        ignore_errors (bool, optional): If True, skips malformed JSON lines instead of raising an error. Defaults to False.

    Yields:
        dict: Parsed JSON objects.
    """
    path = Path(file_path)
    
    with path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                if ignore_errors:
                    logger.warning(f"Skipping malformed JSON at {path}:{line_number}")
                    continue
                raise


def write_file(
    data: Union[str, Dict[str, Any], Iterable[Any]], 
    file_path: Union[str, Path], 
    append: bool = False,
    makedirs: bool = False,
    encoding: str = "utf-8"
) -> None:
    """
    Writes data to a file. Handles strings, dictionaries (as JSON), 
    or iterables of strings/dicts.

    Args:
        data (Union[str, Dict[str, Any], Iterable[Any]]): The content to write. 
            - If str: written as-is.
            - If dict: converted to a JSON string.
            - If iterable: each element is written (strings are joined by newlines).
        file_path (str): Path to the destination file.
        append (bool, optional): If True, appends to the file; otherwise overwrites. Defaults to False.
        makedirs (bool, optional): If True, creates parent directories if they don't exist. Defaults to False.
        encoding (str, optional): File encoding. Defaults to "utf-8".
    """
    path = Path(file_path)
    
    if makedirs:
        path.parent.mkdir(parents=True, exist_ok=True)

    mode = "a" if append else "w"
    
    with path.open(mode, encoding=encoding) as f:
        if isinstance(data, str):
            f.write(data)
        elif isinstance(data, dict):
            f.write(json.dumps(data, ensure_ascii=False))
        elif isinstance(data, Iterable):
            for item in data:
                if isinstance(item, dict):
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")
                else:
                    f.write(str(item) + "\n")
        else:
            f.write(str(data))


def write_jsonl(
    data: Union[Dict, Iterable[Dict]], 
    file_path: Union[str, Path], 
    append: bool = False,
    makedirs: bool = False,
    encoding: str = "utf-8",
    ensure_ascii: bool = False
) -> None:
    """
    Writes a dictionary or an iterable of dictionaries to a .jsonl file.

    Args:
        data (Union[Dict, Iterable[Dict]]): A single dictionary or an iterable of JSON-serializable dictionaries.
        file_path (str): Path where the file will be saved.
        append (bool, optional): If True, appends to the file; otherwise overwrites. Defaults to False.
        makedirs (bool, optional): If True, creates parent directories if they don't exist. Defaults to False.
        encoding (bool, str): File encoding. Defaults to "utf-8".
        ensure_ascii (bool, optional): Pass ensure_ascii to json.dump. Defaults to False.
    """
    path = Path(file_path)
    
    if makedirs:
        path.parent.mkdir(parents=True, exist_ok=True)
    
    # If data is a single dict, wrap it in a list to treat it as an iterable
    if isinstance(data, dict):
        data = [data]
    
    mode = "a" if append else "w"
    with path.open(mode, encoding=encoding) as f:
        for entry in data:
            f.write(json.dumps(entry, ensure_ascii=ensure_ascii) + "\n")


def extract_filename(file_path: str, include_extension: bool = True) -> str:
    """
    Extract the file name from a path string.

    Args:
        file_path (str): The string containing the path.
        include_extension (bool, optional): If False, returns the name without the extension (stem). Defaults to True.

    Returns:
        str: The extracted filename (e.g., "data.jsonl" or "data").
    """
    if not file_path:
        return ""
    
    path_obj = Path(file_path)
    return path_obj.name if include_extension else path_obj.stem


def find_files(patterns: Union[str, List[str]], recursive: bool = True) -> List[str]:
    """
    Find files matching one or more glob patterns.

    Args:
        patterns (str, List[str]): A single pattern (str) or a list of patterns (e.g., ["data/*.jsonl"]).
        recursive (bool, optional): Whether to search subdirectories (requires '**' in the pattern). Defaults to True.

    Returns:
        List[str]: A sorted list of unique file paths matching the patterns.
    """
    if isinstance(patterns, str):
        patterns = [patterns]

    found_files = set()
    for pattern in patterns:
        # glob.glob handles the expansion; recursive=True enables '**' logic
        matches = glob.glob(pattern, recursive=recursive)
        for match in matches:
            if Path(match).is_file():
                found_files.add(match)

    return sorted(list(found_files))