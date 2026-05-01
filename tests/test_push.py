"""测试 push.py：推送逻辑。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from push import send_push
from unittest.mock import patch, MagicMock


class TestSendPush:

    def test_empty_url_skips(self):
        """push_url 为空时跳过推送，不抛异常。"""
        send_push("", "title", "content")  # 不应抛异常

    def test_none_url_skips(self):
        """push_url 为 None 时跳过推送。"""
        send_push(None, "title", "content")

    def test_successful_push(self):
        """推送成功时返回正常。"""
        with patch("push.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"error_code": 0}
            mock_post.return_value = mock_response

            send_push("https://push.example.com/api", "title", "content")
            mock_post.assert_called_once()

    def test_failed_push(self):
        """推送失败时打印错误不抛异常。"""
        with patch("push.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"error_code": 1, "error_message": "token error"}
            mock_post.return_value = mock_response

            # 不应抛异常
            send_push("https://push.example.com/api", "title", "content")

    def test_network_error(self):
        """网络异常时打印错误不抛异常。"""
        with patch("push.requests.post", side_effect=Exception("timeout")):
            send_push("https://push.example.com/api", "title", "content")
