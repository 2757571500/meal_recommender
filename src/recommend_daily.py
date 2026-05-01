#!/usr/bin/env python3
# -- coding: utf-8 --
# 青龙面板定时任务：每日三餐推荐
# cron "30 8 * * *" script-path=src/recommend_daily.py,tag=每日三餐推荐
# const $ = new Env('每日三餐推荐')
#
# 流程：加载配置 → 用户画像 → 检测菜品库 → 获取天气 → 硬过滤 → AI 推荐 → 推送

import sys

# 兼容 Windows 终端编码，避免 emoji 等字符打印报错
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from core.config import load_config, load_profile, load_enums
from core.weather import get_weather
from core.recommender import recommend
from core.push import send_push
from core.dish_manager import load_dishes


def main():
    # 加载运行配置、用户画像、枚举定义
    config = load_config()
    profile = load_profile()
    enums = load_enums()

    # 检测菜品库是否为空（首次使用需先跑 update_library.py 填充）
    dishes = load_dishes()
    if not dishes:
        print("菜品库为空，跳过今日推荐。请先运行 python update_library.py 填充菜品库。")
        return

    print(f"用户: {profile.hometown}")
    print(f"AI 模型: {config.ai.model}")
    print(f"不重复天数: {config.cache.no_repeat_days}")

    weather_condition, weather_temp, weather_city = get_weather(config.weather.city_code)
    print(f"天气: {weather_city} {weather_condition} {weather_temp}")
    print()

    output = recommend(config, weather_condition, weather_temp, profile, enums, weather_city)
    if output:
        print(output)
        send_push(
            config.push.push_url,
            title=f"三餐推荐 | {profile.hometown}",
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
