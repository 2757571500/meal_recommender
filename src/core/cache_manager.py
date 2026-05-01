import json
import os
from datetime import datetime, timedelta


def _cache_path():
    """cache.json 的绝对路径（与脚本同目录）。"""
    return os.path.join(os.path.dirname(__file__), "..", "..", "data", "cache.json")


def _load_cache():
    """读取缓存 JSON 文件，文件不存在时返回空记录结构。"""
    path = _cache_path()
    if not os.path.exists(path):
        return {"records": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_cache(cache):
    """写入缓存 JSON 文件。"""
    with open(_cache_path(), "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def get_excluded_dishes(days):
    """返回指定天数内推荐过的菜品名称集合。

    用于推荐引擎排除短期内已出现过的菜品。
    days 对应配置中的 no_repeat_days。
    """
    cache = _load_cache()
    cutoff = datetime.now().date() - timedelta(days=days)
    excluded = set()
    for r in cache["records"]:
        record_date = datetime.strptime(r["date"], "%Y-%m-%d").date()
        if record_date >= cutoff:
            excluded.add(r["name"])
    return excluded


def add_record(dish_names, meal_type):
    """记录本次推荐的菜品到缓存。

    每条记录包含菜名、日期和餐段（午餐/晚餐）。
    后续 get_excluded_dishes() 据此判断是否在排除期内。
    """
    cache = _load_cache()
    today = datetime.now().strftime("%Y-%m-%d")
    for name in dish_names:
        cache["records"].append({"name": name, "date": today, "meal": meal_type})
    _save_cache(cache)


def cleanup(days):
    """清理超过 days 天的旧记录，防止缓存无限膨胀。"""
    cache = _load_cache()
    cutoff = datetime.now().date() - timedelta(days=days)
    cache["records"] = [
        r for r in cache["records"]
        if datetime.strptime(r["date"], "%Y-%m-%d").date() >= cutoff
    ]
    _save_cache(cache)
