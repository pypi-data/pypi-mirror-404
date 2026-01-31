"""
vLLM Async Client Wrapper.

This module provides a high-performance, asynchronous client for interacting with 
vLLM (Versatile Large Language Model) API servers.

It is designed to be used in asynchronous frameworks like **FastAPI** or **MCP (Model Context Protocol)** servers,
where blocking the main event loop is strictly prohibited.

Dependencies:
    - httpx: For non-blocking HTTP requests.
    - numpy: For vectorized calculations (reranking/logits).

Key Features:
    1. **Asynchronous I/O**: Uses `httpx` to ensure the server remains responsive during LLM inference.
    2. **Connection Pooling**: Maintains a persistent HTTP session to reduce TCP handshake overhead.
    3. **Auto-Configuration**: Automatically fetches the model's `max_model_len` to optimize truncation.
    4. **Smart Batching**: Implements client-side parallelism for endpoints that do not support 
       native batching (specifically `/tokenize`), using `asyncio.gather`.

Usage Example:
    ```python
    import asyncio
    from client import AsyncVLLMClient

    async def main():
        # Context manager handles connection opening/closing and config loading
        async with AsyncVLLMClient(model="qwen-7b", host="localhost", port=8000) as client:
            
            # Tokenize text
            tokens = await client.tokenize("Hello world")
            
            # Classify text
            probs = await client.classify(["Text A", "Text B"])
            
    asyncio.run(main())
    ```
"""

import logging
import asyncio
from typing import Any, Dict, List, Union, Optional, TypeAlias, overload 

import httpx
import requests
import numpy as np

# --- Type Definitions ---
# Generic JSON dictionary type for API responses
JsonDict: TypeAlias = Dict[str, Any]
# List of probabilities (floats) corresponding to class labels
ClassProbs: TypeAlias = List[float]
# Dictionary representing a single token and its classification label
TokenLabel: TypeAlias = Dict[str, Union[str, int]]

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VLLMClient:
    """
    A synchronous client for vLLM API servers.

    This client uses `requests.Session` to maintain persistent connections.
    It implements the same "Lazy Loading" strategy for model configuration as the async version.

    Attributes:
        model (str): The model identifier used for API calls.
        base_url (str): The fully constructed base URL.
        session (requests.Session): The underlying HTTP session.
    """

    def __init__(
        self,
        model: str,
        host: str = "localhost",
        port: int = 8000,
        auth_token: Optional[str] = None,
        user_agent: str = "legal-utils SyncClient",
        timeout: float = 30.0,
        default_max_len: int = 8192
    ):
        """
        Initializes the VLLMClient.

        Args:
            model: The model name or path.
            host: The hostname or IP address of the vLLM server.
            port: The port number.
            auth_token: Optional Bearer token for authentication.
            user_agent: Custom User-Agent string.
            timeout: Request timeout in seconds.
            default_max_len: Fallback value for `max_model_len`.
        """
        self.model = model
        self.base_url = f"http://{host}:{port}"
        self.timeout = timeout
        
        # Initialize persistent session
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent,
            "Content-Type": "application/json"
        })
        if auth_token:
            self.session.headers["Authorization"] = f"Bearer {auth_token}"
        
        # Internal state for configuration caching
        self._max_model_len: Optional[int] = None
        self._default_max_len = default_max_len

    def close(self):
        """Closes the underlying HTTP session."""
        self.session.close()

    def __enter__(self):
        """
        Context Manager Entry.
        Triggers configuration fetching immediately.
        """
        self._refresh_model_config()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context Manager Exit. Closes the session."""
        self.close()

    def _post(self, endpoint: str, payload: JsonDict) -> JsonDict:
        """
        Internal helper to send synchronous POST requests.

        Raises:
            requests.exceptions.HTTPError: If the server returns 4xx/5xx.
            requests.exceptions.RequestException: For connection issues.
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error querying {url}: {e}")
            raise

    def _refresh_model_config(self):
        """Fetches and caches the model's configuration."""
        try:
            # Dummy request to probe server config
            response = self._post("/tokenize", {
                "model": self.model, 
                "prompt": "test", 
                "return_token_strs": False
            })
            self._max_model_len = response.get("max_model_len", self._default_max_len)
            logger.debug(f"Model config loaded: max_model_len={self._max_model_len}")
        except Exception as e:
            logger.warning(f"Could not fetch model config on init ({e}). Using default: {self._default_max_len}")
            self._max_model_len = self._default_max_len

    def _get_max_model_len(self) -> int:
        """Retrieves cached max_model_len or fetches it if missing."""
        if self._max_model_len is None:
            self._refresh_model_config()
        return self._max_model_len  # type: ignore

    @overload
    def tokenize(
        self,
        texts: str,
        add_special_tokens: bool = True,
        return_token_strs: bool = True,
    ) -> JsonDict: ...

    @overload
    def tokenize(
        self,
        texts: List[str],
        add_special_tokens: bool = True,
        return_token_strs: bool = True,
    ) -> List[JsonDict]: ...

    def tokenize(
        self,
        texts: Union[str, List[str]],
        add_special_tokens: bool = True,
        return_token_strs: bool = True,
    ) -> Union[JsonDict, List[JsonDict]]:
        """
        Tokenizes text(s) into token IDs.

        **Note:** Since vLLM's `/tokenize` does not support batching, this method
        iterates sequentially over the list if `texts` is a list.

        Args:
            texts: Single string or list of strings.
            add_special_tokens: Whether to add BOS/EOS tokens.
            return_token_strs: Whether to return token strings.

        Returns:
            Dict or List of Dicts containing token IDs.
        """
        # Handle client-side iteration for lists
        if isinstance(texts, list):
            return [
                self.tokenize(t, add_special_tokens, return_token_strs) 
                for t in texts
            ]

        payload = {
            "model": self.model,
            "prompt": texts,
            "add_special_tokens": add_special_tokens,
            "return_token_strs": return_token_strs,
        }
        return self._post("/tokenize", payload)

    def detokenize(self, tokens: List[int]) -> JsonDict:
        """Decodes token IDs back into a string."""
        payload = {"model": self.model, "tokens": tokens}
        return self._post("/detokenize", payload)

    def classify(
        self,
        texts: Union[str, List[str]],
        truncate_prompt_tokens: Optional[int] = None,
    ) -> List[ClassProbs]:
        """
        Performs sequence classification.

        Args:
            texts: Text or list of texts.
            truncate_prompt_tokens: Max tokens limit.

        Returns:
            List of probability lists.
        """
        if isinstance(texts, str):
            texts = [texts]

        if truncate_prompt_tokens is None:
            truncate_prompt_tokens = self._get_max_model_len()

        payload = {
            "model": self.model,
            "input": texts,
            "truncate_prompt_tokens": truncate_prompt_tokens
        }
        
        response = self._post("/classify", payload)
        return [r["probs"] for r in response.get("data", [])]

    def rerank(
        self,
        texts: Union[str, List[str]],
        truncate_prompt_tokens: Optional[int] = None,
    ) -> List[float]:
        """
        Computes reranking scores based on classification probabilities.
        """
        probs_list = self.classify(texts, truncate_prompt_tokens)
        
        if not probs_list:
            return []

        probs_array = np.array(probs_list)
        num_labels = probs_array.shape[1]
        
        if num_labels <= 1:
            return np.zeros(len(probs_list)).tolist()

        indexes = np.arange(num_labels)
        scores = (probs_array @ indexes) / (num_labels - 1)
        
        return scores.tolist()

    def embed(
        self,
        texts: Union[str, List[str]],
        truncate_prompt_tokens: Optional[int] = None,
    ) -> List[List[float]]:
        """Generates embeddings for text(s)."""
        if isinstance(texts, str):
            texts = [texts]

        if truncate_prompt_tokens is None:
            truncate_prompt_tokens = self._get_max_model_len()

        payload = {
            "model": self.model,
            "input": texts,
            "truncate_prompt_tokens": truncate_prompt_tokens,
        }

        response = self._post("/pooling", payload)
        return [r["data"] for r in response.get("data", [])]

    def token_classify(
        self,
        texts: Union[str, List[str]],
        truncate_prompt_tokens: Optional[int] = None,
        return_tokens: bool = False,
    ) -> List[Union[List[int], List[TokenLabel]]]:
        """
        Performs token-level classification.

        Args:
            texts: Input text(s).
            truncate_prompt_tokens: Max tokens limit.
            return_tokens: If True, returns dicts with {'token': str, 'label': int}.

        Returns:
            List of classification results.
        """
        if isinstance(texts, str):
            texts = [texts]

        if truncate_prompt_tokens is None:
            truncate_prompt_tokens = self._get_max_model_len()

        # 1. Fetch classifications (Batch supported)
        payload = {
            "model": self.model,
            "input": texts,
            "task": "token_classify",
            "truncate_prompt_tokens": truncate_prompt_tokens,
        }

        response = self._post("/pooling", payload)
        raw_data = response.get("data", [])
        
        label_indices_list = [
            np.array(r["data"]).argmax(axis=-1).tolist() 
            for r in raw_data
        ]

        if not return_tokens:
            return label_indices_list

        # 2. Fetch tokens (Sequential iteration)
        results = []
        for text, labels in zip(texts, label_indices_list):
            token_resp = self.tokenize(text, return_token_strs=True)
            # Ensure token_resp is a dict (tokenize returns list if input is list, dict if str)
            # Here input is str, so it returns dict.
            tokens = token_resp.get("token_strs", [])
            
            min_len = min(len(tokens), len(labels))
            
            results.append([
                {"token": token, "label": label} 
                for token, label in zip(tokens[:min_len], labels[:min_len])
            ])
            
        return results
    
class AsyncVLLMClient:
    """
    A robust, asynchronous client for vLLM API servers.

    This class manages the HTTP session lifecycle and abstracts the vLLM API endpoints.
    It implements a "Lazy Loading" strategy for model configuration: the model's maximum 
    context length is fetched either upon entering the context manager (`async with`) 
    or just before the first request that requires it.

    Attributes:
        model (str): The model identifier used for API calls (must match server config).
        base_url (str): The fully constructed base URL (e.g., "http://localhost:8000").
        client (httpx.AsyncClient): The underlying async HTTP client instance.
    """

    def __init__(
        self,
        model: str,
        host: str = "localhost",
        port: int = 8000,
        auth_token: Optional[str] = None,
        user_agent: str = "legal-utils AsyncClient",
        timeout: float = 30.0,
        default_max_len: int = 8192
    ):
        """
        Initializes the AsyncVLLMClient.

        Args:
            model: The model name or path (e.g., "meta-llama/Llama-2-7b").
            host: The hostname or IP address of the vLLM server.
            port: The port number the server is listening on.
            auth_token: Optional Bearer token if the server requires authentication.
            user_agent: Custom User-Agent string for request tracking.
            timeout: Request timeout in seconds. Defaults to 30.0s.
            default_max_len: Fallback value for `max_model_len` if the API fails 
                             to provide the model configuration.
        """
        self.model = model
        self.base_url = f"http://{host}:{port}"
        self.headers = {
            "User-Agent": user_agent,
            "Content-Type": "application/json"
        }
        if auth_token:
            self.headers["Authorization"] = f"Bearer {auth_token}"
        
        # Initialize the persistent async client
        self.client = httpx.AsyncClient(
            base_url=self.base_url, 
            headers=self.headers,
            timeout=timeout
        )
        
        # Internal state for configuration caching
        self._max_model_len: Optional[int] = None
        self._default_max_len = default_max_len

    async def close(self):
        """
        Closes the underlying HTTP client and releases network resources.
        Should be called when the client is no longer needed.
        """
        await self.client.aclose()

    async def __aenter__(self):
        """
        Async Context Manager Entry.
        
        Triggers the fetching of model configuration (max_model_len) immediately
        to ensure subsequent calls are fast.
        """
        await self._refresh_model_config()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async Context Manager Exit.
        Ensures the HTTP connection is closed properly.
        """
        await self.close()

    async def _post(self, endpoint: str, payload: JsonDict) -> JsonDict:
        """
        Internal helper to send asynchronous POST requests with error handling.

        Args:
            endpoint: The API endpoint path (e.g., "/tokenize").
            payload: The JSON payload to send.

        Returns:
            The parsed JSON response from the server.

        Raises:
            httpx.HTTPStatusError: If the server returns a 4xx or 5xx status code.
            httpx.RequestError: If a network connection error occurs.
        """
        try:
            response = await self.client.post(endpoint, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} on {endpoint}: {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Connection error on {endpoint}: {e}")
            raise

    async def _refresh_model_config(self):
        """
        Fetches and caches the model's configuration (specifically `max_model_len`).
        
        This is done by making a dummy request to the API, as vLLM typically returns
        configuration metadata in response headers or bodies.
        """
        try:
            # We use a lightweight request to probe the server config
            response = await self._post("/tokenize", {
                "model": self.model, 
                "prompt": "test", 
                "return_token_strs": False
            })
            self._max_model_len = response.get("max_model_len", self._default_max_len)
            logger.debug(f"Model config loaded: max_model_len={self._max_model_len}")
        except Exception as e:
            logger.warning(f"Could not fetch model config on init ({e}). Using default: {self._default_max_len}")
            self._max_model_len = self._default_max_len

    async def _get_max_model_len(self) -> int:
        """
        Retrieves the cached `max_model_len`. 
        If not yet cached, triggers a fetch (Lazy Loading pattern).
        """
        if self._max_model_len is None:
            await self._refresh_model_config()
        return self._max_model_len  # type: ignore

    @overload
    async def tokenize(
        self,
        texts: str,
        add_special_tokens: bool = True,
        return_token_strs: bool = True,
    ) -> JsonDict: ...

    @overload
    async def tokenize(
        self,
        texts: List[str],
        add_special_tokens: bool = True,
        return_token_strs: bool = True,
    ) -> List[JsonDict]: ...

    async def tokenize(
        self,
        texts: Union[str, List[str]],
        add_special_tokens: bool = True,
        return_token_strs: bool = True,
    ) -> Union[JsonDict, List[JsonDict]]:
        """
        Tokenizes text(s) into token IDs.

        **Performance Note:** 
        The vLLM `/tokenize` endpoint often does not support batching (list inputs).
        If `texts` is a list, this method uses `asyncio.gather` to send multiple 
        requests in parallel, which is significantly faster than sequential processing.

        Args:
            texts: A single string or a list of strings to tokenize.
            add_special_tokens: Whether to add BOS (Beginning of Sentence) / EOS tokens.
            return_token_strs: Whether to include the string representation of tokens in the response.

        Returns:
            If input is `str`: A dictionary containing `tokens` (IDs).
            If input is `List[str]`: A list of such dictionaries.

        Example:
            >>> await client.tokenize("Hello")
            {'tokens': [1, 15043], 'token_strs': ['<s>', 'Hello']}
        """
        # Handle client-side parallelism for lists
        if isinstance(texts, list):
            tasks = [
                self.tokenize(t, add_special_tokens, return_token_strs) 
                for t in texts
            ]
            return await asyncio.gather(*tasks)

        payload = {
            "model": self.model,
            "prompt": texts,
            "add_special_tokens": add_special_tokens,
            "return_token_strs": return_token_strs,
        }
        return await self._post("/tokenize", payload)

    async def detokenize(self, tokens: List[int]) -> JsonDict:
        """
        Decodes a list of token IDs back into a string.

        Args:
            tokens: A list of integer token IDs.

        Returns:
            A dictionary containing the decoded `prompt` (text).
        """
        payload = {"model": self.model, "tokens": tokens}
        return await self._post("/detokenize", payload)

    async def classify(
        self,
        texts: Union[str, List[str]],
        truncate_prompt_tokens: Optional[int] = None,
    ) -> List[ClassProbs]:
        """
        Performs sequence classification on the input texts.

        Args:
            texts: A single string or a list of strings.
            truncate_prompt_tokens: Max tokens to process. If None, uses the model's max length.

        Returns:
            A list of probability lists. 
            Example: `[[0.1, 0.9], [0.8, 0.2]]` (for 2 texts, binary classification).
        """
        if isinstance(texts, str):
            texts = [texts]

        if truncate_prompt_tokens is None:
            truncate_prompt_tokens = await self._get_max_model_len()

        payload = {
            "model": self.model,
            "input": texts,
            "truncate_prompt_tokens": truncate_prompt_tokens
        }
        
        response = await self._post("/classify", payload)
        # Assuming standard vLLM response structure for classification
        return [r["probs"] for r in response.get("data", [])]

    async def rerank(
        self,
        texts: Union[str, List[str]],
        truncate_prompt_tokens: Optional[int] = None,
    ) -> List[float]:
        """
        Computes a scalar score for each text based on classification probabilities.

        This is typically used for "Pointwise Reranking" where the model outputs 
        probabilities for labels like "Relevant" vs "Not Relevant".
        
        Formula: `Score = sum(prob[i] * i) / (num_labels - 1)`
        This calculates a normalized weighted average of the class indices.

        Args:
            texts: Texts to score.
            truncate_prompt_tokens: Token truncation limit.

        Returns:
            A list of float scores between 0.0 and 1.0.
        """
        probs_list = await self.classify(texts, truncate_prompt_tokens)
        
        if not probs_list:
            return []

        probs_array = np.array(probs_list)
        num_labels = probs_array.shape[1]
        
        if num_labels <= 1:
            return np.zeros(len(probs_list)).tolist()

        indexes = np.arange(num_labels)
        scores = (probs_array @ indexes) / (num_labels - 1)
        
        return scores.tolist()

    async def embed(
        self,
        texts: Union[str, List[str]],
        truncate_prompt_tokens: Optional[int] = None,
    ) -> List[List[float]]:
        """
        Generates vector embeddings for the input texts.

        Args:
            texts: Texts to embed.
            truncate_prompt_tokens: Token truncation limit.

        Returns:
            A list of embedding vectors (lists of floats).
        """
        if isinstance(texts, str):
            texts = [texts]

        if truncate_prompt_tokens is None:
            truncate_prompt_tokens = await self._get_max_model_len()

        payload = {
            "model": self.model,
            "input": texts,
            "truncate_prompt_tokens": truncate_prompt_tokens,
        }

        response = await self._post("/pooling", payload)
        return [r["data"] for r in response.get("data", [])]

    async def token_classify(
        self,
        texts: Union[str, List[str]],
        truncate_prompt_tokens: Optional[int] = None,
        return_tokens: bool = False,
    ) -> List[Union[List[int], List[TokenLabel]]]:
        """
        Performs token-level classification (e.g., NER, POS tagging).

        This method handles the complexity of mapping classification labels back 
        to the original tokens, which requires coordinating two different API endpoints.

        Args:
            texts: Input text(s).
            truncate_prompt_tokens: Max tokens limit.
            return_tokens: 
                - If `False`: Returns a list of integer labels (indices).
                - If `True`: Returns a list of dicts `{'token': str, 'label': int}`.
                  **Warning**: This triggers additional API calls to tokenize the text.

        Returns:
            A list (one per text) containing the classification results.
        """
        if isinstance(texts, str):
            texts = [texts]

        if truncate_prompt_tokens is None:
            truncate_prompt_tokens = await self._get_max_model_len()

        # Step 1: Fetch classification logits/probs via pooling endpoint
        # The /pooling endpoint typically supports batching, so we send all texts at once.
        payload = {
            "model": self.model,
            "input": texts,
            "task": "token_classify",
            "truncate_prompt_tokens": truncate_prompt_tokens,
        }

        response = await self._post("/pooling", payload)
        raw_data = response.get("data", [])
        
        # Convert logits/probs to label indices using argmax
        label_indices_list = [
            np.array(r["data"]).argmax(axis=-1).tolist() 
            for r in raw_data
        ]

        if not return_tokens:
            return label_indices_list

        # Step 2: If tokens are requested, we must tokenize the inputs to align them with labels.
        # We use asyncio.gather to perform these tokenization requests in parallel.
        token_tasks = [
            self.tokenize(text, return_token_strs=True) 
            for text in texts
        ]
        
        all_tokens_resp = await asyncio.gather(*token_tasks)
        
        results = []
        for labels, token_resp in zip(label_indices_list, all_tokens_resp):
            tokens = token_resp.get("token_strs", [])
            
            # Align lengths: Truncation might have occurred on the server side during classification.
            # We truncate our lists to the length of the shortest sequence to prevent index errors.
            min_len = min(len(tokens), len(labels))
            
            results.append([
                {"token": token, "label": label} 
                for token, label in zip(tokens[:min_len], labels[:min_len])
            ])
            
        return results


def call_openai(prompt: str, model: str = "gpt-4o", **kwargs) -> Dict[str, Any]:
    """
    Stub for OpenAI API call.
    
    This function is a placeholder. To use OpenAI, install the official library:
    `pip install openai` and use their `AsyncOpenAI` client.

    Raises:
        NotImplementedError: Always raised until implemented.
    """
    raise NotImplementedError("Please install 'openai' package and implement this wrapper.")