"""Utilities for data normalization and validation."""
from typing import Any, Dict, Type, Literal, Union, List, Optional
from pydantic import create_model, BaseModel
import regex
import json_repair

def get_pydantic_schema_from_dict(data: Dict[str, Any], model_name: str = "DynamicModel") -> Dict[str, Any]:
    """
    Generates a Pydantic JSON schema by inferring types from a sample dictionary.

    This function performs a deep inspection of the provided dictionary to build 
    a dynamic Pydantic model. It handles nested dictionaries, lists, and 
    special tuple-to-enum conversion.

    Args:
        data (Dict[str, Any]): The sample dictionary to infer the schema from.
        model_name (str, optional): The name of the root model. Defaults to "DynamicModel".

    Returns:
        Dict: A dictionary representing the Pydantic JSON schema.

    Example:
        >>> sample = {"status": ("open", "closed"), "count": 1}
        >>> schema = get_pydantic_schema_from_dict(sample)
        >>> print(schema['properties']['status']['enum'])
        ['open', 'closed']
    """
    dynamic_model = _build_dynamic_model(data, model_name)
    return dynamic_model.model_json_schema()


def _build_dynamic_model(data: Dict[str, Any], model_name: str) -> Type[BaseModel]:
    """
    Recursively builds a Pydantic model class based on dictionary structure.

    Logic for type inference:
    - dict: Recursively creates a nested Pydantic model.
    - tuple: Converts to `typing.Literal`, forcing the value to be one of the 
      tuple elements (renders as an 'enum' in JSON schema).
    - list: Infers the type from the first element. If empty, defaults to `List[Any]`.
    - other: Uses the standard Python `type()` of the value.

    Args:
        data (Dict[str, Any]): The data to inspect.
        model_name (str): The class name for the generated model.

    Returns:
        Type[BaseModel]: A dynamically generated Pydantic model class.
    """
    fields = {}
    
    for key, value in data.items():
        # 1. Handle Nested Dictionaries
        if isinstance(value, dict):
            nested_model = _build_dynamic_model(value, key.capitalize())
            fields[key] = (nested_model, ...)
            
        # 2. Handle Tuples (Converted to Enums/Literals)
        elif isinstance(value, tuple):
            if not value:
                fields[key] = (Any, ...)
            else:
                # Programmatically create a Literal type from the tuple values
                # Literal[*value] is valid in Python 3.11+
                # Literal.__getitem__(value) is the dynamic equivalent for older versions
                fields[key] = (Literal[*value], ...) 
                
        # 3. Handle Lists
        elif isinstance(value, list):
            if value:
                first_item = value[0]
                if isinstance(first_item, dict):
                    # List of objects
                    inner_model = _build_dynamic_model(first_item, f"{key}Item")
                    fields[key] = (List[inner_model], ...)
                else:
                    # List of primitives
                    fields[key] = (List[type(first_item)], ...)
            else:
                fields[key] = (List[Any], ...)
                
        # 4. Handle Primitives (int, str, float, bool, None)
        else:
            fields[key] = (type(value) if value is not None else Any, ...)

    # Use Pydantic's factory function to create the class
    return create_model(model_name, **fields)


def normalize_text(text: str) -> str:
    """Normalize whitespace and common punctuation for legal text."""
    return " ".join(text.split())


def validate_json(obj: Dict[str, Any]) -> bool:
    """Basic JSON validation stub. Extend with schema checks later."""
    return isinstance(obj, dict)


def clean_json(obj: Dict[str, Any]) -> Dict[str, Any]:
    """Return a cleaned copy of `obj` (remove nulls, normalize strings)."""
    cleaned = {}
    for k, v in obj.items():
        if v is None:
            continue
        if isinstance(v, str):
            cleaned[k] = normalize_text(v)
        else:
            cleaned[k] = v
    return cleaned


def load_json(text: str) -> Union[Dict, None]:
    """
    Extract JSON from string, returns None if fails.

    Args:
        text (str): String to convert to JSON.

    Returns:
        Dict: A dict or None if it fails.
    """
    decoded_object = json_repair.loads(text)
    return decoded_object if isinstance(decoded_object, dict) else None


def extract_json(text: str) -> Union[List, None]:
    """
    Extract JSON from string, returns None if fails.

    Args:
        text (str): String to process.

    Returns:
        List: A list of JSON objects, None if epmty.
    """
    pattern = regex.compile(r'\{(?:[^{}]|(?R))*\}')
    outputs = pattern.findall(text)
    
    output_list = []
    for o in outputs:
        json_dict = load_json(o)
        if json_dict is not None:
            output_list += [load_json(o)]

    if len(output_list) == 0:
        output_list = None
    return output_list


def chunk_iterable(
        iterable, 
        chunk_size: int, 
        overlap: int = 0, 
        avoid_duplicates: bool = False, 
        force_same_size: bool = False,
        drop_last: bool = False
        ) -> List:
    """
    Chunk list into overlapping chunks.

    Args:
        iterable (list): List to chunk.
        chunk_size (int): Size of chunks.
        overlap (int): Size of overlap.
        avoid_duplicates (bool, optional): Avoid having outputs[-1] in outputs[-2]. Defaults to False.
        force_same_size (bool, optional): Force the last chunk to have chunk_size elements. Defaults to False.
        drop_last (bool, optional): Drop last if size is different. Defaults to False.

    Returns:
        List: The list of chunks
    """
    assert overlap >= 0 and overlap < chunk_size, "overlap should be 0 <= overlap < chunksize"

    # Conversion
    items = list(iterable)

    # No chunk
    if len(iterable) <= chunk_size:
        return [iterable]
    
    step = chunk_size - overlap
    if step <= 0:
        raise ValueError("Size must be greater than overlap.")

    chunks = []
    seen = set()

    for i in range(0, len(items), step):
        chunk = items[i : i + chunk_size]
        
        if force_same_size and len(chunk) < chunk_size:
            if drop_last:
                continue
            else:
                chunk = items[-chunk_size:]
        if avoid_duplicates:
            chunk_tuple = tuple(chunk)
            if chunk_tuple in seen:
                continue
            seen.add(chunk_tuple)
            
        chunks.append(chunk)
        
    return chunks


def deduplicate_list(items: List) -> List:
    """
    Removes duplicates from a list while maintaining the original order.
    
    Args:
        items (list): List to deduplicate.

    Returns:
        List: The list without duplicates.
    """
    return list(dict.fromkeys(items))


def split_iterable(iterable, index: Optional[int] = None) -> tuple:
    """
    Splits an iterable into two lists. 
    If index is None, splits exactly in the middle.

    Args:
        iterable (list): Iterable to split.
        index (bool, optional): Size of the first chunk. Defaults to None.

    Returns:
        Tuple: The two chunks of the iterable.
    """
    items = list(iterable)
    idx = index if index is not None else len(items) // 2
    return (items[:idx], items[idx:])


def get_recursive_values(data, target_key: str, recursive: bool = True) -> List:
    """
    Recursively searches for 'target_key' in a dictionary or list of dictionaries.
    Returns a list of all values associated with that key.

    Args:
        data (dict): Dict to search values from.
        target_key (str): The key to search recursively.
        recursive (bool, optional): Do it recursively. Defaults to True.

    Returns:
        List: The list of values of target_key.

    """
    results = []
    
    if isinstance(data, dict):
        for key, value in data.items():
            if key == target_key:
                results.append(value)
            elif recursive:
                results.extend(get_recursive_values(value, target_key))
                
    elif isinstance(data, list):
        for item in data:
            results.extend(get_recursive_values(item, target_key))
            
    return results

