import pytest


def test_import_package():
    import legal_utils

    # Basic smoke test: ensure top-level names exist
    assert hasattr(legal_utils, "read_jsonl")
    assert hasattr(legal_utils, "parallel_map")
