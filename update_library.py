#!/usr/bin/env python3
# -- coding: utf-8 --
# 青龙面板定时任务：扩充菜品库（与推荐分开调度）
# cron "30 6 * * 1" script-path=update_library.py,tag=更新菜品库
# const $ = new Env('更新菜品库')
#
# 流程：加载配置 → 用户画像 → 枚举定义 → 获取天气 → AI JSON 发现 → 枚举校验 → 入库 → 推送

import sys

# 兼容 Windows 终端编码，避免 emoji 等字符打印报错
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from config import load_config, load_profile, load_enums
from weather import get_weather
from recommender import discover_dishes
from push import send_push


def main():
    # 加载运行配置、用户画像、枚举定义
    config = load_config()
    profile = load_profile()
    enums = load_enums()

    print(f"用户: {profile.hometown}")
    print(f"AI 模型: {config.ai.model}")

    weather_condition, weather_temp, weather_city = get_weather(config.weather.city_code)
    print(f"天气: {weather_city} {weather_condition} {weather_temp}")
    print()

    # 传入 enums 用于校验 AI 返回的字段值，profile 用于地域口味提示
    result = discover_dishes(config, weather_condition, weather_temp, enums, profile, weather_city)
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
            title=f"菜品库更新 | {profile.hometown}",
            content=f"{summary}。\n\n{detail}" if detail else summary
        )


if __name__ == "__main__":
    main()
