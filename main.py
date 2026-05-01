#!/usr/bin/env python3
# -- coding: utf-8 --
# 青龙面板定时任务：每日三餐推荐
# cron "30 8 * * *" script-path=main.py,tag=每日三餐推荐
# const $ = new Env('每日三餐推荐')

import sys

# 兼容 Windows 终端编码，避免 emoji 等字符打印报错
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from config import load_config
from weather import get_weather
from recommender import recommend
from push import send_push


def main():
    config = load_config()
    print(f"城市: {config.city}")
    print(f"AI 模型: {config.ai.model}")
    print(f"不重复天数: {config.cache.no_repeat_days}")

    weather_condition, weather_temp = get_weather(config.weather.city_code)
    print(f"天气: {weather_condition} {weather_temp}")
    print()

    output = recommend(config, weather_condition, weather_temp)
    if output:
        print(output)
        send_push(
            config.push.push_url,
            title=f"三餐推荐 | {config.city}",
            content=output
        )
    else:
        print("推荐失败，请检查配置和网络连接。")
        send_push(
            config.push.push_url,
            title="三餐推荐失败",
            content="AI 调用失败，请检查 API 配置和网络连接。"
        )
        exit(1)


if __name__ == "__main__":
    main()
