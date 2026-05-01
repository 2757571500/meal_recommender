"""菜品库管理：JSON 文件读写、去重、新增/更新、枚举校验。

核心函数：
    load_dishes() / save_dishes()    — JSON 文件读写
    add_new_dishes(dishes, enums)    — 新增或更新菜品，可选枚举校验
    validate_dish(dish, enums)       — 校验单条菜品字段值是否在枚举范围内
    list_dish_names()                — 返回所有菜名列表
    deduplicate()                    — 合并同名菜品（忽略大小写和空格）
"""
import json
import os


def _clean_name(name):
    """标准化菜名：去除首尾空格、转小写，用于去重比较。"""
    return name.strip().lower()


def _dishes_path():
    """返回 dishes.json 的绝对路径（与脚本同目录）。"""
    return os.path.join(os.path.dirname(__file__), "..", "..", "data", "dishes.json")


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


def validate_dish(dish, enums):
    """校验单条菜品字段值是否在 enums 允许范围内。

    校验字段：cuisine、taste、difficulty、diet_type、dietary_tags
    超范围的字段值会被记录并跳过，不阻塞其他有效菜品入库。

    参数：
        dish: 菜品字典
        enums: enums.json 加载后的字典
    返回：
        (is_valid, error_msg) 元组
    """
    # cuisine（单值枚举）
    if dish.get("cuisine") not in enums.get("cuisine", []):
        return False, f"cuisine '{dish.get('cuisine')}' 不在枚举范围内"

    # difficulty（单值枚举，复用 skill_level）
    if dish.get("difficulty") not in enums.get("skill_level", []):
        return False, f"difficulty '{dish.get('difficulty')}' 不在枚举范围内"

    # diet_type（单值枚举）
    if dish.get("diet_type") not in enums.get("diet_type", []):
        return False, f"diet_type '{dish.get('diet_type')}' 不在枚举范围内"

    # taste（多值枚举，从 dish_taste 取值）
    valid_tastes = enums.get("dish_taste", [])
    for t in dish.get("taste", []):
        if t not in valid_tastes:
            return False, f"taste '{t}' 不在枚举范围内"

    # dietary_tags（多值枚举，可选字段，为空时不校验）
    valid_tags = enums.get("dietary_tags", [])
    for tag in dish.get("dietary_tags", []):
        if tag not in valid_tags:
            return False, f"dietary_tag '{tag}' 不在枚举范围内"

    return True, ""


def validate_dish_list(dishes, enums):
    """校验菜品列表，过滤掉不合规的条目并打印告警。

    参数：
        dishes: 菜品字典列表
        enums: enums.json 加载后的字典
    返回：
        校验通过的菜品列表
    """
    valid = []
    for d in dishes:
        ok, err = validate_dish(d, enums)
        if ok:
            valid.append(d)
        else:
            print(f"校验未通过，已丢弃: {d.get('name', '未知')} - {err}")
    return valid


def deduplicate():
    """合并同名菜品，保留第一个出现的数据。

    按 _clean_name() 归并，忽略大小写和空格差异。
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


def add_new_dishes(new_dishes, enums=None):
    """新增或更新菜品。

    不存在的菜品 → 追加到菜品库
    已存在的菜品 → 更新 reason 字段
    入库前先做枚举校验（传入 enums 时），校验不通过的丢弃并告警。

    参数：
        new_dishes: 新菜品字典列表
        enums: 可选，enums.json 数据，传入时做枚举校验
    返回：
        (added, updated) 元组
    """
    if enums:
        new_dishes = validate_dish_list(new_dishes, enums)

    if not new_dishes:
        return [], []

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
            if d.get("reason") and existing_map[key].get("reason") != d["reason"]:
                existing_map[key]["reason"] = d["reason"]
                updated.append(d)
    changed = added or updated
    if changed:
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
