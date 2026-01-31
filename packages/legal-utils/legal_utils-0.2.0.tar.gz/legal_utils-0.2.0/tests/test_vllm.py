"""
Unit tests for llm_utils module.

Tests cover:
- VLLMClient initialization and basic operations
- AsyncVLLMClient initialization and async operations
- Payload construction and error handling
"""

import pytest
from unittest.mock import patch, AsyncMock

from legal_utils.vllm import (
    VLLMClient,
    AsyncVLLMClient,
    call_openai,
)


# ============================================================================
# Tests for VLLMClient (Synchronous)
# ============================================================================

class TestVLLMClientInit:
    """Test VLLMClient initialization."""

    def test_init_default_params(self):
        """Test initialization with default parameters."""
        client = VLLMClient(model="test-model")
        assert client.model == "test-model"
        assert client.base_url == "http://localhost:8000"

    def test_init_custom_host_port(self):
        """Test initialization with custom host and port."""
        client = VLLMClient(
            model="test-model",
            host="192.168.1.1",
            port=9000
        )
        assert client.base_url == "http://192.168.1.1:9000"

    def test_init_with_auth_token(self):
        """Test initialization with authentication token."""
        client = VLLMClient(
            model="test-model",
            auth_token="secret-token"
        )
        assert "Authorization" in client.session.headers
        assert client.session.headers["Authorization"] == "Bearer secret-token"

    def test_init_with_custom_timeout(self):
        """Test initialization with custom timeout."""
        client = VLLMClient(model="test-model", timeout=60.0)
        assert client.timeout == 60.0

    def test_context_manager(self):
        """Test VLLMClient as context manager."""
        with VLLMClient(model="test-model") as client:
            assert client is not None
            assert client.model == "test-model"


class TestAsyncVLLMClientInit:
    """Test AsyncVLLMClient initialization."""

    def test_init_default_params(self):
        """Test initialization with default parameters."""
        client = AsyncVLLMClient(model="test-model")
        assert client.model == "test-model"
        assert client.base_url == "http://localhost:8000"

    def test_init_custom_host_port(self):
        """Test initialization with custom host and port."""
        client = AsyncVLLMClient(
            model="test-model",
            host="127.0.0.1",
            port=8001
        )
        assert client.base_url == "http://127.0.0.1:8001"

    def test_init_with_auth_token(self):
        """Test initialization with authentication token."""
        client = AsyncVLLMClient(
            model="test-model",
            auth_token="test-token"
        )
        assert "Authorization" in client.headers
        assert client.headers["Authorization"] == "Bearer test-token"

    def test_init_default_max_len(self):
        """Test initialization with default max length."""
        client = AsyncVLLMClient(model="test-model", default_max_len=4096)
        assert client._default_max_len == 4096

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test AsyncVLLMClient as async context manager."""
        async with AsyncVLLMClient(model="test-model") as client:
            assert client is not None
            assert client.model == "test-model"


# ============================================================================
# Tests for AsyncVLLMClient async methods
# ============================================================================

class TestAsyncVLLMClientMethods:
    """Test AsyncVLLMClient async methods."""

    @pytest.mark.asyncio
    async def test_tokenize_string_input(self):
        """Test tokenization with string input."""
        with patch.object(
            AsyncVLLMClient, '_post',
            new_callable=AsyncMock,
            return_value={
                'tokens': [1, 2, 3],
                'token_strs': ['<s>', 'test', 'token']
            }
        ):
            async with AsyncVLLMClient(model="test-model") as client:
                result = await client.tokenize("test")
                assert 'tokens' in result
                assert 'token_strs' in result

    @pytest.mark.asyncio
    async def test_tokenize_list_input(self):
        """Test tokenization with list input (parallel processing)."""
        mock_response = {
            'tokens': [1, 2, 3],
            'token_strs': ['<s>', 'test', 'token']
        }

        with patch.object(
            AsyncVLLMClient, '_post',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            async with AsyncVLLMClient(model="test-model") as client:
                results = await client.tokenize(["test1", "test2"])
                assert isinstance(results, list)
                assert len(results) == 2

    @pytest.mark.asyncio
    async def test_detokenize(self):
        """Test detokenization."""
        mock_response = {'prompt': 'decoded text'}

        with patch.object(
            AsyncVLLMClient, '_post',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            async with AsyncVLLMClient(model="test-model") as client:
                result = await client.detokenize([1, 2, 3])
                assert 'prompt' in result

    @pytest.mark.asyncio
    async def test_classify_string_input(self):
        """Test classification with string input."""
        mock_response = {
            'data': [{'probs': [0.1, 0.9]}]
        }

        with patch.object(
            AsyncVLLMClient, '_post',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            async with AsyncVLLMClient(model="test-model") as client:
                client._max_model_len = 2048
                result = await client.classify("test text")
                assert isinstance(result, list)
                assert len(result) == 1
                assert result[0] == [0.1, 0.9]

    @pytest.mark.asyncio
    async def test_classify_list_input(self):
        """Test classification with list input."""
        mock_response = {
            'data': [
                {'probs': [0.1, 0.9]},
                {'probs': [0.8, 0.2]}
            ]
        }

        with patch.object(
            AsyncVLLMClient, '_post',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            async with AsyncVLLMClient(model="test-model") as client:
                client._max_model_len = 2048
                result = await client.classify(["text1", "text2"])
                assert len(result) == 2

    @pytest.mark.asyncio
    async def test_embed(self):
        """Test embedding generation."""
        mock_response = {
            'data': [
                {'data': [0.1, 0.2, 0.3]},
                {'data': [0.4, 0.5, 0.6]}
            ]
        }

        with patch.object(
            AsyncVLLMClient, '_post',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            async with AsyncVLLMClient(model="test-model") as client:
                client._max_model_len = 2048
                result = await client.embed(["text1", "text2"])
                assert len(result) == 2
                assert result[0] == [0.1, 0.2, 0.3]

    @pytest.mark.asyncio
    async def test_rerank(self):
        """Test reranking."""
        mock_probs = [[0.3, 0.7], [0.6, 0.4]]

        with patch.object(
            AsyncVLLMClient, 'classify',
            new_callable=AsyncMock,
            return_value=mock_probs
        ):
            async with AsyncVLLMClient(model="test-model") as client:
                result = await client.rerank(["text1", "text2"])
                assert isinstance(result, list)
                assert len(result) == 2
                assert all(0.0 <= score <= 1.0 for score in result)

    @pytest.mark.asyncio
    async def test_token_classify_without_tokens(self):
        """Test token classification without returning token strings."""
        mock_response = {
            'data': [{'data': [[0.1, 0.9], [0.8, 0.2], [0.3, 0.7]]}]
        }

        with patch.object(
            AsyncVLLMClient, '_post',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            async with AsyncVLLMClient(model="test-model") as client:
                client._max_model_len = 2048
                result = await client.token_classify(
                    "test text",
                    return_tokens=False
                )
                assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_token_classify_with_tokens(self):
        """Test token classification with token alignment."""
        classify_response = {
            'data': [{'data': [[0.1, 0.9], [0.8, 0.2]]}]
        }
        tokenize_response = {
            'tokens': [1, 2],
            'token_strs': ['test', 'text']
        }

        with patch.object(
            AsyncVLLMClient, '_post',
            new_callable=AsyncMock,
            return_value=classify_response
        ):
            with patch.object(
                AsyncVLLMClient, 'tokenize',
                new_callable=AsyncMock,
                return_value=tokenize_response
            ):
                async with AsyncVLLMClient(model="test-model") as client:
                    client._max_model_len = 2048
                    result = await client.token_classify(
                        "test text",
                        return_tokens=True
                    )
                    assert isinstance(result, list)
                    assert len(result) > 0


# ============================================================================
# Tests for error handling
# ============================================================================

class TestErrorHandling:
    """Test error handling in clients."""

    def test_call_openai_not_implemented(self):
        """Test that call_openai raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            call_openai("test prompt")

    @pytest.mark.asyncio
    async def test_async_post_http_error(self):
        """Test handling of HTTP errors in async client."""
        with patch.object(
            AsyncVLLMClient, '_post',
            new_callable=AsyncMock,
            side_effect=Exception("Connection error")
        ):
            async with AsyncVLLMClient(model="test-model") as client:
                with pytest.raises(Exception):
                    await client.tokenize("test")


# ============================================================================
# Integration-style tests
# ============================================================================

class TestClientIntegration:
    """Integration tests for client workflows."""

    @pytest.mark.asyncio
    async def test_full_async_workflow(self):
        """Test a complete async workflow."""
        tokenize_response = {
            'tokens': [1, 2, 3],
            'token_strs': ['<s>', 'hello', 'world']
        }
        classify_response = {
            'data': [{'probs': [0.2, 0.8]}]
        }

        async with AsyncVLLMClient(model="test-model") as client:
            with patch.object(
                AsyncVLLMClient, '_post',
                new_callable=AsyncMock,
                side_effect=[tokenize_response, classify_response]
            ):
                tokens = await client.tokenize("hello world")
                assert tokens['tokens'] == [1, 2, 3]

    def test_client_headers_construction(self):
        """Test that headers are properly constructed."""
        client = VLLMClient(
            model="test-model",
            user_agent="CustomAgent/1.0"
        )
        assert "User-Agent" in client.session.headers
        assert "CustomAgent/1.0" in client.session.headers["User-Agent"]