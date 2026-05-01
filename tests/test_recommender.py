"""测试 recommender.py：过滤、季节、prompt 构建、解析、格式化。"""
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from recommender import (
    get_season, filter_dishes, _build_prompt,
    _build_discover_prompt, _parse_response,
    _parse_json_dish_list, _format_output,
)


class TestGetSeason:

    def test_spring(self):
        """3-5月为春。"""
        assert get_season(3) == "春"
        assert get_season(4) == "春"
        assert get_season(5) == "春"

    def test_summer(self):
        """6-8月为夏。"""
        assert get_season(6) == "夏"
        assert get_season(7) == "夏"
        assert get_season(8) == "夏"

    def test_autumn(self):
        """9-11月为秋。"""
        assert get_season(9) == "秋"
        assert get_season(10) == "秋"
        assert get_season(11) == "秋"

    def test_winter(self):
        """12-2月为冬。"""
        assert get_season(12) == "冬"
        assert get_season(1) == "冬"
        assert get_season(2) == "冬"

    def test_default_current_month(self):
        """不传参时使用当前月份，不会抛异常。"""
        season = get_season()
        assert season in ("春", "夏", "秋", "冬")


class TestFilterDishes:

    def _profile(self, **kwargs):
        defaults = {"diet_type": "无限制", "skill_level": "普通", "max_cook_time": 60}
        defaults.update(kwargs)
        return SimpleNamespace(**defaults)

    def test_diet_type_none_keeps_all(self, sample_dishes):
        """用户无限制时全部保留。"""
        profile = self._profile(diet_type="无限制", skill_level="熟练")
        result = filter_dishes(sample_dishes, profile)
        assert len(result) == len(sample_dishes)

    def test_diet_type_vegetarian(self, sample_dishes):
        """用户素食时保留素食+无限制。"""
        profile = self._profile(diet_type="素食", skill_level="熟练")
        result = filter_dishes(sample_dishes, profile)
        names = [d["name"] for d in result]
        assert "素炒青菜" in names    # 素食
        assert "凉拌黄瓜" in names     # 素食
        assert "番茄炒蛋" in names     # 无限制
        assert "红烧肉" in names       # 无限制
        assert "水煮鱼" in names       # 无限制

    def test_diet_type_only_keeps_matching_types(self, sample_dishes):
        """素食用户不应看到纯素、清真以外的菜。"""
        profile = self._profile(diet_type="素食")
        result = filter_dishes(sample_dishes, profile)
        for d in result:
            assert d["diet_type"] in ("素食", "无限制")

    def test_difficulty_filter(self, sample_dishes):
        """新手只能看到新手和普通难度的菜。"""
        profile = self._profile(skill_level="新手")
        result = filter_dishes(sample_dishes, profile)
        for d in result:
            assert d["difficulty"] in ("新手",)

    def test_difficulty_normal_sees_all_except_skilled(self):
        """普通用户只能看到新手和普通（不能看到熟练）。"""
        dishes = [
            {"name": "简单", "difficulty": "新手", "diet_type": "无限制", "prep_time": 5},
            {"name": "中等", "difficulty": "普通", "diet_type": "无限制", "prep_time": 5},
            {"name": "困难", "difficulty": "熟练", "diet_type": "无限制", "prep_time": 5},
        ]
        profile = self._profile(skill_level="普通")
        result = filter_dishes(dishes, profile)
        names = [d["name"] for d in result]
        assert "简单" in names
        assert "中等" in names
        assert "困难" not in names

    def test_prep_time_filter(self, sample_dishes):
        """超过 max_cook_time 的菜应被排除。"""
        profile = self._profile(max_cook_time=10)
        result = filter_dishes(sample_dishes, profile)
        for d in result:
            assert d["prep_time"] <= 10

    def test_combined_filters(self, sample_dishes):
        """多条件组合过滤。"""
        profile = self._profile(diet_type="素食", skill_level="新手", max_cook_time=10)
        result = filter_dishes(sample_dishes, profile)
        for d in result:
            assert d["diet_type"] in ("素食", "无限制")
            assert d["difficulty"] == "新手"
            assert d["prep_time"] <= 10

    def test_empty_diet_type_none(self):
        """diet_type=None 场景不抛异常。"""
        profile = self._profile(diet_type="无限制")
        dishes = [{"name": "x", "diet_type": None, "difficulty": "新手", "prep_time": 5}]
        result = filter_dishes(dishes, profile)
        assert len(result) == 1  # 无限制时不校验 diet_type

    def test_empty_dishes(self):
        """空列表返回空列表。"""
        profile = self._profile()
        result = filter_dishes([], profile)
        assert result == []


class TestBuildPrompt:

    def test_prompt_contains_city_and_weather(self):
        """prompt 包含天气城市和天气信息。"""
        from dish_manager import load_dishes
        profile = SimpleNamespace(
            hometown="合肥", serving_size=2, max_cook_time=30,
            skill_level="普通", taste=["偏辣"], cuisine_preferences=["川菜"],
            diet_type="无限制", avoid_ingredients=["羊肉"]
        )
        prompt = _build_prompt(
            weather_city="北京", weather_condition="晴",
            weather_temp="12~22°C", no_repeat_days=7,
            profile=profile, filtered_dishes=load_dishes()
        )
        assert "北京" in prompt
        assert "晴" in prompt
        assert "合肥" in prompt
        assert "偏辣" in prompt
        assert "川菜" in prompt
        assert "羊肉" in prompt
        assert "2 人" in prompt

    def test_prompt_contains_excluded_list(self):
        """prompt 包含排除列表。"""
        from dish_manager import load_dishes
        profile = SimpleNamespace(
            hometown="合肥", serving_size=1, max_cook_time=30,
            skill_level="新手", taste=[], cuisine_preferences=[],
            diet_type="无限制", avoid_ingredients=[]
        )
        prompt = _build_prompt(
            weather_city="合肥", weather_condition="多云",
            weather_temp="15°C", no_repeat_days=7,
            profile=profile, filtered_dishes=load_dishes()
        )
        assert "请避开" in prompt or "排除" in prompt

    def test_prompt_empty_filtered_dishes(self):
        """菜品库为空时 prompt 正常生成。"""
        profile = SimpleNamespace(
            hometown="合肥", serving_size=2, max_cook_time=30,
            skill_level="普通", taste=[], cuisine_preferences=[],
            diet_type="无限制", avoid_ingredients=[]
        )
        prompt = _build_prompt(
            weather_city="合肥", weather_condition="多云",
            weather_temp="15°C", no_repeat_days=7,
            profile=profile, filtered_dishes=[]
        )
        assert "暂无菜品库" in prompt


class TestBuildDiscoverPrompt:

    def test_prompt_contains_enum_constraints(self, enums):
        """菜品发现 prompt 包含枚举约束。"""
        profile = SimpleNamespace(
            hometown="合肥", serving_size=2, max_cook_time=30,
            skill_level="普通", taste=["偏辣"], cuisine_preferences=["川菜", "徽菜"],
            diet_type="无限制", avoid_ingredients=[]
        )
        prompt = _build_discover_prompt(
            weather_city="合肥", weather_condition="多云",
            weather_temp="15°C", enums=enums, profile=profile
        )
        assert "川菜" in prompt
        assert "徽菜" in prompt
        assert "合肥" in prompt
        assert "JSON 数组" in prompt or "json" in prompt.lower()


class TestParseResponse:

    def test_parse_lunch_and_dinner(self):
        """正确解析三餐分开的格式。"""
        text = """午餐：
- 麻婆豆腐（麻辣下饭）
- 番茄炒蛋（酸甜开胃）
- 紫菜蛋花汤（清淡可口）

晚餐：
- 回锅肉（肥而不腻）
- 清炒西兰花（清爽解腻）
- 冬瓜排骨汤（鲜香暖胃）"""
        result = _parse_response(text)
        assert len(result["lunch"]) == 3
        assert len(result["dinner"]) == 3
        assert result["lunch"][0]["name"] == "麻婆豆腐"
        assert result["lunch"][0]["reason"] == "麻辣下饭"
        assert result["dinner"][1]["name"] == "清炒西兰花"

    def test_parse_without_reason(self):
        """菜名后无理由也能解析。"""
        text = """午餐：
- 麻婆豆腐
- 番茄炒蛋"""
        result = _parse_response(text)
        assert result["lunch"][0]["name"] == "麻婆豆腐"
        assert result["lunch"][0]["reason"] == ""

    def test_empty_text(self):
        """空文本返回空结果。"""
        result = _parse_response("")
        assert result == {"lunch": [], "dinner": []}

    def test_no_meal_labels(self):
        """没有午餐/晚餐标签时返回空。"""
        result = _parse_response("- 菜名（理由）")
        assert result == {"lunch": [], "dinner": []}


class TestParseJsonDishList:

    def test_plain_json_array(self):
        """纯 JSON 数组直接解析。"""
        text = '[{"name": "麻婆豆腐", "cuisine": "川菜", "taste": ["辣"], "difficulty": "新手", "prep_time": 10, "ingredients": ["x"], "diet_type": "无限制", "dietary_tags": [], "reason": "好吃"}]'
        result = _parse_json_dish_list(text)
        assert len(result) == 1
        assert result[0]["name"] == "麻婆豆腐"

    def test_json_with_markdown_fence(self):
        """markdown 代码块包裹的 JSON。"""
        text = """```json
[{"name": "回锅肉", "cuisine": "川菜", "taste": ["辣"], "difficulty": "普通", "prep_time": 20, "ingredients": ["肉"], "diet_type": "无限制", "dietary_tags": [], "reason": "香"}]
```"""
        result = _parse_json_dish_list(text)
        assert len(result) == 1
        assert result[0]["name"] == "回锅肉"

    def test_json_markdown_without_lang(self):
        """``` 不带 json 标记。"""
        text = """```
[{"name": "t", "cuisine": "川菜", "taste": [], "difficulty": "新手", "prep_time": 5, "ingredients": ["x"], "diet_type": "无限制", "dietary_tags": [], "reason": ""}]
```"""
        result = _parse_json_dish_list(text)
        assert len(result) == 1

    def test_invalid_json(self):
        """非法 JSON 返回空列表。"""
        result = _parse_json_dish_list("这不是 JSON")
        assert result == []

    def test_not_a_list(self):
        """JSON 是字典而非列表则返回空。"""
        result = _parse_json_dish_list('{"name": "test"}')
        assert result == []


class TestFormatOutput:

    def test_format_with_reasons(self):
        """格式化输出包含理由。"""
        profile = SimpleNamespace(hometown="合肥", serving_size=2)
        result = {
            "lunch": [{"name": "麻婆豆腐", "reason": "麻辣下饭"}],
            "dinner": [{"name": "清蒸鱼", "reason": "鲜嫩"}]
        }
        output = _format_output(profile, result)
        assert "合肥" in output
        assert "麻婆豆腐" in output
        assert "麻辣下饭" in output
        assert "午餐" in output
        assert "晚餐" in output

    def test_format_without_reasons(self):
        """无理由时只显示菜名。"""
        profile = SimpleNamespace(hometown="北京", serving_size=1)
        result = {
            "lunch": [{"name": "炒饭", "reason": ""}],
            "dinner": []
        }
        output = _format_output(profile, result)
        assert "炒饭" in output
        # 不应包含"理由"关键词尾缀
        assert "炒饭（）" not in output
