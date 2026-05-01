"""测试共用 fixture：临时文件、枚举、画像、示例菜品。"""
import json
import pytest
from pathlib import Path


@pytest.fixture
def enums():
    return {
        "taste": ["偏咸", "偏淡", "偏辣", "偏麻", "偏甜", "偏酸", "偏鲜"],
        "cuisine": ["川菜", "鲁菜", "粤菜", "苏菜", "徽菜"],
        "skill_level": ["新手", "普通", "熟练"],
        "diet_type": ["无限制", "素食", "纯素", "清真"],
        "dietary_tags": ["含辣", "含花生", "含海鲜", "含蛋", "含奶", "含麸质"],
        "dish_taste": ["咸", "淡", "辣", "麻", "甜", "酸", "鲜", "香", "清淡"]
    }


@pytest.fixture
def sample_dish():
    """标准合法菜品。"""
    return {
        "name": "麻婆豆腐",
        "reason": "麻辣鲜香",
        "cuisine": "川菜",
        "taste": ["辣", "麻"],
        "difficulty": "普通",
        "prep_time": 20,
        "ingredients": ["豆腐", "牛肉末"],
        "diet_type": "无限制",
        "dietary_tags": ["含辣"]
    }


@pytest.fixture
def sample_dishes():
    """多样化的菜品列表，用于过滤测试。"""
    return [
        {"name": "素炒青菜", "cuisine": "徽菜", "taste": ["清淡"], "difficulty": "新手", "prep_time": 5, "ingredients": ["青菜"], "diet_type": "素食", "dietary_tags": []},
        {"name": "红烧肉", "cuisine": "徽菜", "taste": ["咸", "香"], "difficulty": "熟练", "prep_time": 60, "ingredients": ["五花肉"], "diet_type": "无限制", "dietary_tags": []},
        {"name": "水煮鱼", "cuisine": "川菜", "taste": ["辣", "麻"], "difficulty": "普通", "prep_time": 30, "ingredients": ["鱼"], "diet_type": "无限制", "dietary_tags": ["含辣", "含海鲜"]},
        {"name": "番茄炒蛋", "cuisine": "鲁菜", "taste": ["咸"], "difficulty": "新手", "prep_time": 10, "ingredients": ["番茄", "鸡蛋"], "diet_type": "无限制", "dietary_tags": ["含蛋"]},
        {"name": "凉拌黄瓜", "cuisine": "川菜", "taste": ["酸", "辣"], "difficulty": "新手", "prep_time": 8, "ingredients": ["黄瓜"], "diet_type": "素食", "dietary_tags": ["含辣"]},
    ]


@pytest.fixture
def tmp_profile(tmp_path):
    """写入临时 profile.json 并返回路径。"""
    data = {
        "hometown": "合肥",
        "serving_size": 2,
        "max_cook_time": 30,
        "skill_level": "普通",
        "taste": ["偏咸", "偏辣"],
        "cuisine_preferences": ["川菜", "徽菜"],
        "diet_type": "无限制",
        "avoid_ingredients": ["羊肉", "内脏"]
    }
    path = tmp_path / "profile.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    return path


@pytest.fixture
def tmp_enums(tmp_path):
    """写入临时 enums.json 并返回路径。"""
    data = {
        "taste": ["偏咸", "偏淡", "偏辣", "偏麻", "偏甜", "偏酸", "偏鲜"],
        "cuisine": ["川菜", "鲁菜", "粤菜", "苏菜", "徽菜"],
        "skill_level": ["新手", "普通", "熟练"],
        "diet_type": ["无限制", "素食", "纯素", "清真"],
        "dietary_tags": ["含辣", "含花生", "含海鲜", "含蛋", "含奶", "含麸质"],
        "dish_taste": ["咸", "淡", "辣", "麻", "甜", "酸", "鲜", "香", "清淡"]
    }
    path = tmp_path / "enums.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    return path


@pytest.fixture
def tmp_dishes_file(tmp_path):
    """返回一个临时 dishes.json 路径（不创建文件）。"""
    return tmp_path / "dishes.json"


@pytest.fixture
def patch_dishes_path(monkeypatch, tmp_path):
    """将 _dishes_path 重定向到临时路径，避免修改真实文件。"""
    test_path = tmp_path / "dishes.json"
    monkeypatch.setattr("core.dish_manager._dishes_path", lambda: str(test_path))
    return test_path
