"""测试 weather.py：天气 API 降级。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.weather import get_weather


class TestGetWeather:

    def test_known_city_code_returns_tuple(self):
        """有城市码返回 (condition, temperature, city_name) 三元组。"""
        result = get_weather("101220101")  # 合肥
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_unknown_city_code_returns_unknown(self):
        """无效城市码降级返回未知。"""
        condition, temp, city = get_weather("999999999")
        assert condition == "未知"
        assert temp == "未知"
        assert city == "未知"

    def test_empty_city_code_returns_unknown(self):
        """空城市码降级返回未知。"""
        condition, temp, city = get_weather("")
        assert condition == "未知"
        assert temp == "未知"
        assert city == "未知"

    def test_return_type_strings(self):
        """返回值都是字符串。"""
        condition, temp, city = get_weather("101220101")
        assert isinstance(condition, str)
        assert isinstance(temp, str)
        assert isinstance(city, str)
