"""legal_utils package

Exporte les modules principaux pour usage direct.
"""
from .data import (
    chunk_iterable, 
    clean_json, 
    create_model, 
    deduplicate_list, 
    extract_json, 
    get_pydantic_schema_from_dict, 
    get_recursive_values, 
    load_json, 
    split_iterable, 
    validate_json
    )
from .file import (
    extract_filename, 
    find_files, 
    read_file,
    read_jsonl, 
    write_file,
    write_jsonl
    )
from .processing import parallel_map
from .vllm import AsyncVLLMClient, VLLMClient
