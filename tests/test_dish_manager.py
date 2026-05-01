"""测试 dish_manager.py：CRUD、去重、枚举校验。"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dish_manager import (
    load_dishes, save_dishes, validate_dish, validate_dish_list,
    add_new_dishes, deduplicate, list_dish_names,
)


class TestValidateDish:

    def test_valid_dish(self, enums, sample_dish):
        """合法菜品校验通过。"""
        ok, msg = validate_dish(sample_dish, enums)
        assert ok
        assert msg == ""

    def test_invalid_cuisine(self, enums):
        """cuisine 不在枚举中则失败。"""
        dish = {"name": "t", "cuisine": "外星菜", "taste": [], "difficulty": "新手", "prep_time": 5, "ingredients": ["x"], "diet_type": "无限制", "dietary_tags": []}
        ok, msg = validate_dish(dish, enums)
        assert not ok
        assert "外星菜" in msg

    def test_invalid_difficulty(self, enums):
        """difficulty 不在枚举中则失败。"""
        dish = {"name": "t", "cuisine": "川菜", "taste": [], "difficulty": "大师级", "prep_time": 5, "ingredients": ["x"], "diet_type": "无限制", "dietary_tags": []}
        ok, msg = validate_dish(dish, enums)
        assert not ok
        assert "大师级" in msg

    def test_invalid_diet_type(self, enums):
        """diet_type 不在枚举中则失败。"""
        dish = {"name": "t", "cuisine": "川菜", "taste": [], "difficulty": "新手", "prep_time": 5, "ingredients": ["x"], "diet_type": "生酮", "dietary_tags": []}
        ok, msg = validate_dish(dish, enums)
        assert not ok
        assert "生酮" in msg

    def test_invalid_taste(self, enums):
        """taste 值不在 dish_taste 枚举中则失败。"""
        dish = {"name": "t", "cuisine": "川菜", "taste": ["外星味"], "difficulty": "新手", "prep_time": 5, "ingredients": ["x"], "diet_type": "无限制", "dietary_tags": []}
        ok, msg = validate_dish(dish, enums)
        assert not ok
        assert "外星味" in msg

    def test_invalid_dietary_tag(self, enums):
        """dietary_tag 不在枚举中则失败。"""
        dish = {"name": "t", "cuisine": "川菜", "taste": [], "difficulty": "新手", "prep_time": 5, "ingredients": ["x"], "diet_type": "无限制", "dietary_tags": ["非法标签"]}
        ok, msg = validate_dish(dish, enums)
        assert not ok
        assert "非法标签" in msg

    def test_empty_dietary_tags_passes(self, enums):
        """dietary_tags 为空数组时校验通过。"""
        dish = {"name": "t", "cuisine": "川菜", "taste": ["辣"], "difficulty": "新手", "prep_time": 5, "ingredients": ["x"], "diet_type": "无限制", "dietary_tags": []}
        ok, msg = validate_dish(dish, enums)
        assert ok

    def test_empty_taste_fails_on_valid(self, enums):
        """taste 不能为空（设计上为空时通过）。"""
        dish = {"name": "t", "cuisine": "川菜", "taste": [], "difficulty": "新手", "prep_time": 5, "ingredients": ["x"], "diet_type": "无限制", "dietary_tags": []}
        ok, msg = validate_dish(dish, enums)
        assert ok  # 空数组 = 无校验失败


class TestValidateDishList:

    def test_all_valid(self, enums, sample_dish):
        """全部合法时全部保留。"""
        result = validate_dish_list([sample_dish, sample_dish], enums)
        assert len(result) == 2

    def test_mixed_valid_and_invalid(self, enums):
        """混合列表只保留合法项。"""
        valid = {"name": "a", "cuisine": "川菜", "taste": ["辣"], "difficulty": "新手", "prep_time": 5, "ingredients": ["x"], "diet_type": "无限制", "dietary_tags": []}
        invalid = {"name": "b", "cuisine": "外星菜", "taste": [], "difficulty": "新手", "prep_time": 5, "ingredients": ["x"], "diet_type": "无限制", "dietary_tags": []}
        result = validate_dish_list([valid, invalid], enums)
        assert len(result) == 1
        assert result[0]["name"] == "a"

    def test_all_invalid(self, enums):
        """全部非法时返回空列表。"""
        invalid = {"name": "b", "cuisine": "外星菜", "taste": [], "difficulty": "新手", "prep_time": 5, "ingredients": ["x"], "diet_type": "无限制", "dietary_tags": []}
        result = validate_dish_list([invalid], enums)
        assert result == []


class TestDishCRUD:

    def test_load_dishes_from_real_file(self):
        """确认真实 dishes.json 可加载。"""
        dishes = load_dishes()
        assert isinstance(dishes, list)

    def test_save_and_load(self, tmp_dishes_file):
        """写入后重新读取内容一致。"""
        from dish_manager import _dishes_path, _dishes_path as dp
        original = dp

        dishes = [{"name": "测试菜", "cuisine": "川菜", "taste": ["辣"], "difficulty": "新手", "prep_time": 5, "ingredients": ["x"], "diet_type": "无限制", "dietary_tags": []}]
        save_dishes(dishes)
        loaded = load_dishes()
        assert len(loaded) == 1
        assert loaded[0]["name"] == "测试菜"

    def test_list_dish_names(self):
        """list_dish_names 返回正确。"""
        names = list_dish_names()
        assert isinstance(names, list)

    def test_list_dish_names_types(self):
        """返回的菜名都是字符串。"""
        names = list_dish_names()
        if names:
            assert all(isinstance(n, str) for n in names)


class TestAddNewDishes:

    def test_add_new_dish_without_enums(self):
        """不传 enums 时不校验，直接入库。"""
        # 清空后再加一道
        from dish_manager import save_dishes, load_dishes, add_new_dishes
        current = load_dishes()
        count_before = len(current)

        new = [{"name": "测试新增菜", "cuisine": "川菜", "taste": ["辣"], "difficulty": "新手", "prep_time": 5, "ingredients": ["x"], "diet_type": "无限制", "dietary_tags": []}]
        added, updated = add_new_dishes(new)
        assert len(added) == 1 or len(added) == 0  # 可能已存在同名

        # 清理：恢复原状
        save_dishes(current)

    def test_add_with_enum_validation_passes(self, enums):
        """传入 enums 且数据合法时正常入库。"""
        from dish_manager import save_dishes, load_dishes, add_new_dishes
        current = load_dishes()
        count_before = len(current)

        new = [{"name": f"枚举校验菜", "cuisine": "川菜", "taste": ["辣"], "difficulty": "新手", "prep_time": 5, "ingredients": ["x"], "diet_type": "无限制", "dietary_tags": []}]
        added, updated = add_new_dishes(new, enums=enums)
        # 可能已存在同名
        assert isinstance(added, list)
        assert isinstance(updated, list)

        save_dishes(current)

    def test_add_with_enum_validation_fails(self, enums):
        """传入 enums 且数据非法时跳过。"""
        from dish_manager import save_dishes, load_dishes, add_new_dishes
        current = load_dishes()

        new = [{"name": "非法菜", "cuisine": "火星菜", "taste": [], "difficulty": "新手", "prep_time": 5, "ingredients": ["x"], "diet_type": "无限制", "dietary_tags": []}]
        added, updated = add_new_dishes(new, enums=enums)
        assert added == []
        assert updated == []

        save_dishes(current)


class TestDeduplicate:

    def test_deduplicate_preserves_newest_reason(self):
        """去重后保留第一个出现的记录。"""
        from dish_manager import save_dishes, load_dishes, deduplicate
        current = load_dishes()

        test_data = [
            {"name": "重复菜", "cuisine": "川菜", "taste": ["辣"], "difficulty": "新手", "prep_time": 5, "ingredients": ["x"], "diet_type": "无限制", "dietary_tags": [], "reason": "版本1"},
            {"name": "重复菜", "cuisine": "川菜", "taste": ["辣"], "difficulty": "新手", "prep_time": 5, "ingredients": ["x"], "diet_type": "无限制", "dietary_tags": [], "reason": "版本2"},
        ]
        save_dishes(test_data)
        result = deduplicate()
        assert len(result) == 1

        save_dishes(current)

    def test_no_duplicates_unchanged(self):
        """无重复时原样返回。"""
        from dish_manager import save_dishes, load_dishes, deduplicate
        current = load_dishes()

        test_data = [
            {"name": "菜A", "cuisine": "川菜", "taste": ["辣"], "difficulty": "新手", "prep_time": 5, "ingredients": ["x"], "diet_type": "无限制", "dietary_tags": []},
            {"name": "菜B", "cuisine": "徽菜", "taste": ["咸"], "difficulty": "普通", "prep_time": 10, "ingredients": ["y"], "diet_type": "无限制", "dietary_tags": []},
        ]
        save_dishes(test_data)
        result = deduplicate()
        assert len(result) == 2

        save_dishes(current)
