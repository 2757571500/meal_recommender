import json
import os


def _clean_name(name):
    """标准化菜名：去除首尾空格、转小写，用于去重比较。"""
    return name.strip().lower()


def _dishes_path():
    """dishes.json 的绝对路径（与脚本同目录）。"""
    return os.path.join(os.path.dirname(__file__), "dishes.json")


def load_dishes():
    """读取菜品库 JSON 文件。文件不存在时返回空列表。"""
    path = _dishes_path()
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_dishes(dishes):
    """写入菜品库 JSON 文件。"""
    with open(_dishes_path(), "w", encoding="utf-8") as f:
        json.dump(dishes, f, ensure_ascii=False, indent=2)


def deduplicate():
    """合并同名菜品，保留第一个出现的数据。

    按 _clean_name() 归并，忽略大小写和空格差异。
    例如 '麻婆豆腐 ' 和 '麻婆豆腐' 视为同一菜品。
    有重复时自动写回文件。
    """
    dishes = load_dishes()
    seen = {}
    for d in dishes:
        key = _clean_name(d["name"])
        if key not in seen:
            seen[key] = d
    if len(seen) < len(dishes):
        save_dishes(list(seen.values()))
    return list(seen.values())


def add_new_dishes(new_dishes):
    """新增或更新菜品。

    - 不存在的菜品 → 追加到菜品库（返回 added）
    - 已存在的菜品 → 更新 reason 字段（返回 updated）
    保持原有菜品顺序，同名只保留一份。
    """
    existing = load_dishes()
    existing_map = {_clean_name(d["name"]): d for d in existing}
    added = []
    updated = []
    for d in new_dishes:
        key = _clean_name(d["name"])
        if key not in existing_map:
            existing.append(d)
            existing_map[key] = d
            added.append(d)
        else:
            # 新推荐的菜品理由可能更丰富，覆盖旧理由
            if d.get("reason") and existing_map[key].get("reason") != d["reason"]:
                existing_map[key]["reason"] = d["reason"]
                updated.append(d)
    changed = added or updated
    if changed:
        # 用有序 dict 重建，保持原顺序同时去重
        seen = set()
        ordered = []
        for d in existing:
            k = _clean_name(d["name"])
            if k not in seen:
                seen.add(k)
                ordered.append(existing_map[k])
        save_dishes(ordered)
    return added, updated


def list_dish_names():
    """返回所有菜品名列表，供 AI Prompt 组装使用。"""
    return [d["name"] for d in load_dishes()]
