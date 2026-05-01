"""测试 config.py：配置加载、用户画像加载、枚举加载。"""
import sys
from pathlib import Path

# 确保能导入项目模块
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.config import load_config, load_profile, load_enums


class TestLoadConfig:
    """config.json 加载测试。"""

    def test_load_real_config(self):
        """加载真实 config.json，确认能正常读取。"""
        cfg = load_config()
        assert hasattr(cfg, "ai")
        assert hasattr(cfg, "weather")
        assert hasattr(cfg, "cache")
        assert hasattr(cfg, "push")
        assert hasattr(cfg.ai, "base_url")
        assert hasattr(cfg.ai, "model")
        assert hasattr(cfg.ai, "api_key")
        # city 字段已移除
        assert not hasattr(cfg, "city")

    def test_load_ai_config(self):
        """AI 段配置点号访问正常。"""
        cfg = load_config()
        assert cfg.ai.model == "LongCat-Flash-Chat-2602-Exp"

    def test_load_with_custom_path(self, tmp_path):
        """通过自定义路径加载。"""
        path = tmp_path / "config.json"
        path.write_text('{"ai": {"base_url": "x", "api_key": "y", "model": "z"}, "weather": {"provider": "itboy", "city_code": "101220101"}, "cache": {"no_repeat_days": 7}, "push": {"push_url": ""}}')
        cfg = load_config(str(path))
        assert cfg.ai.model == "z"


class TestLoadProfile:

    def test_load_real_profile(self):
        """加载真实 profile.json 确认字段完整。"""
        p = load_profile()
        assert p.hometown == "合肥"
        assert p.serving_size == 2
        assert p.max_cook_time == 30
        assert p.skill_level == "普通"
        assert p.taste == ["偏咸", "偏辣"]
        assert p.cuisine_preferences == ["川菜", "徽菜"]
        assert p.diet_type == "无限制"
        assert p.avoid_ingredients == ["羊肉", "内脏"]

    def test_load_with_custom_path(self, tmp_path, tmp_profile):
        """通过自定义路径加载。"""
        p = load_profile(str(tmp_profile))
        assert p.hometown == "合肥"

    def test_profile_types(self):
        """字段类型正确。"""
        p = load_profile()
        assert isinstance(p.serving_size, int)
        assert isinstance(p.max_cook_time, int)
        assert isinstance(p.taste, list)
        assert isinstance(p.cuisine_preferences, list)
        assert isinstance(p.avoid_ingredients, list)

    def test_file_not_found(self):
        """文件不存在应抛异常。"""
        import pytest
        with pytest.raises(FileNotFoundError):
            load_profile("/nonexistent/profile.json")


class TestLoadEnums:

    def test_load_real_enums(self):
        """加载真实 enums.json 确认枚举完整。"""
        e = load_enums()
        assert "川菜" in e["cuisine"]
        assert "新手" in e["skill_level"]
        assert "无限制" in e["diet_type"]
        assert "偏辣" in e["taste"]
        assert "含辣" in e["dietary_tags"]
        assert "辣" in e["dish_taste"]

    def test_load_with_custom_path(self, tmp_path, tmp_enums):
        """通过自定义路径加载。"""
        e = load_enums(str(tmp_enums))
        assert "川菜" in e["cuisine"]

    def test_file_not_found(self):
        """文件不存在应抛异常。"""
        import pytest
        with pytest.raises(FileNotFoundError):
            load_enums("/nonexistent/enums.json")
