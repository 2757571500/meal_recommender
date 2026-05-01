"""测试 ai_client.py：AI 客户端异常处理。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ai_client import AIClient
from unittest.mock import patch, MagicMock


class TestAIClient:

    def test_chat_network_error(self):
        """网络异常向上抛出。"""
        client = AIClient("https://api.example.com", "sk-test", "test-model")
        with patch("ai_client.requests.post", side_effect=Exception("connection error")):
            import pytest
            with pytest.raises(Exception):
                client.chat([{"role": "user", "content": "hi"}])

    def test_chat_http_error(self):
        """HTTP 状态码异常向上抛出。"""
        client = AIClient("https://api.example.com", "sk-test", "test-model")
        with patch("ai_client.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = Exception("HTTP 401")
            mock_post.return_value = mock_response

            import pytest
            with pytest.raises(Exception):
                client.chat([{"role": "user", "content": "hi"}])

    def test_chat_success(self):
        """正常返回文本。"""
        client = AIClient("https://api.example.com", "sk-test", "test-model")
        with patch("ai_client.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "你好"}}]
            }
            mock_post.return_value = mock_response

            result = client.chat([{"role": "user", "content": "hi"}])
            assert result == "你好"

    def test_chat_empty_choices(self):
        """空 choices 抛异常。"""
        client = AIClient("https://api.example.com", "sk-test", "test-model")
        with patch("ai_client.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"choices": []}
            mock_post.return_value = mock_response

            with patch("ai_client.requests.post") as mp:
                mp.return_value = mock_response
                import pytest
                with pytest.raises(Exception):
                    client.chat([{"role": "user", "content": "hi"}])

    def test_custom_timeout(self):
        """自定义超时时间。"""
        client = AIClient("https://api.example.com", "sk-test", "test-model", timeout=60)
        assert client.timeout == 60

    def test_base_url_trailing_slash_stripped(self):
        """结尾斜杠被移除。"""
        client = AIClient("https://api.example.com/", "sk-test", "test-model")
        assert client.base_url == "https://api.example.com"
