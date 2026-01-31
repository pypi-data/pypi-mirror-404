"""Helpers for processing optimization (parallel execution, batching)."""
from typing import Iterable, Callable, List, Any
from concurrent.futures import ThreadPoolExecutor, as_completed


def parallel_map(func: Callable, items: Iterable, max_workers: int = 4) -> List[Any]:
    """Apply `func` to `items` in parallel using threads.

    Returns results in the same order as input when possible.
    """
    items = list(items)
    results = [None] * len(items)
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(func, item): idx for idx, item in enumerate(items)}
        for fut in as_completed(futures):
            idx = futures[fut]
            results[idx] = fut.result()
    return results