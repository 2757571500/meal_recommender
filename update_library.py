#!/usr/bin/env python3
# -- coding: utf-8 --
# 青龙面板定时任务：扩充菜品库（与推荐分开调度）
# cron "30 6 * * 1" script-path=update_library.py,tag=更新菜品库
# const $ = new Env('更新菜品库')

import sys

# 兼容 Windows 终端编码，避免 emoji 等字符打印报错
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from config import load_config
from weather import get_weather
from recommender import discover_dishes
from push import send_push


def main():
    config = load_config()
    print(f"城市: {config.city}")
    print(f"AI 模型: {config.ai.model}")

    weather_condition, weather_temp = get_weather(config.weather.city_code)
    print(f"天气: {weather_condition} {weather_temp}")
    print()

    result = discover_dishes(config, weather_condition, weather_temp)
    if result is None:
        print("菜品库更新失败。")
        send_push(
            config.push.push_url,
            title="菜品库更新失败",
            content="AI 调用失败，请检查 API 配置和网络连接。"
        )
        exit(1)
    else:
        added, updated = result
        summary = f"新增 {len(added)} 道菜"
        if updated:
            summary += f"，更新 {len(updated)} 道菜的理由"
        detail = ""
        if added:
            detail += "新增菜品：\n" + "\n".join(f"  - {d['name']}" for d in added)
        print(f"\n更新完毕。{summary}。")
        send_push(
            config.push.push_url,
            title=f"菜品库更新 | {config.city}",
            content=f"{summary}。\n\n{detail}" if detail else summary
        )


if __name__ == "__main__":
    main()
