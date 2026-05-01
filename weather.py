import requests
import json


def get_weather(city_code):
    """调用 itboy 天气 API，返回 (天气状况, 温度范围, 城市名)。

    接口: http://t.weather.itboy.net/api/weather/city/{city_code}
    返回示例: ("晴", "12~22°C", "北京")
    城市代码示例: 北京 101010100（与天气网城市代码一致）。
    API 异常时降级返回 ("未知", "未知", "未知")，不影响推荐主流程。
    """
    try:
        url = f"http://t.weather.itboy.net/api/weather/city/{city_code}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        d = json.loads(resp.text)

        city_name = d["cityInfo"]["city"]
        forecast = d["data"]["forecast"][0]
        condition = forecast["type"]
        high = forecast["high"].replace("高温 ", "").replace("℃", "")
        low = forecast["low"].replace("低温 ", "").replace("℃", "")
        temperature = f"{low}~{high}°C"

        print(f"城市: {city_name}")
        return condition, temperature, city_name
    except Exception as e:
        print(f"天气获取失败: {e}")
        return "未知", "未知", "未知"
