"""测试 cache_manager.py：缓存读写、排除列表、清理。"""
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cache_manager import get_excluded_dishes, add_record, cleanup


class TestCacheManager:
    """注意：这些测试操作真实 cache.json。为了避免污染，
    会在测试前后保存/恢复原始内容。"""

    def setup_method(self):
        """保存原始缓存内容。"""
        from cache_manager import _load_cache
        self._original = _load_cache()

    def teardown_method(self):
        """恢复原始缓存内容。"""
        from cache_manager import _save_cache
        _save_cache(self._original)

    def test_add_and_get_excluded(self):
        """记录菜品后在新天数内应被排除。"""
        add_record(["测试菜"], "午餐")
        excluded = get_excluded_dishes(7)
        assert "测试菜" in excluded

    def test_record_with_meal_type(self):
        """记录包含餐段信息。"""
        from cache_manager import _load_cache
        add_record(["测试菜"], "午餐")
        cache = _load_cache()
        found = [r for r in cache["records"] if r["name"] == "测试菜"]
        assert any(r["meal"] == "午餐" for r in found)

    def test_get_excluded_beyond_days(self):
        """超出 no_repeat_days 的记录不被排除。"""
        from cache_manager import _load_cache, _save_cache
        # 插入一条 30 天前的记录
        cache = _load_cache()
        old_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        cache["records"].append({"name": "旧菜", "date": old_date, "meal": "午餐"})
        _save_cache(cache)

        excluded = get_excluded_dishes(7)
        assert "旧菜" not in excluded

        excluded_30 = get_excluded_dishes(30)
        assert "旧菜" in excluded_30

    def test_cleanup_removes_old_records(self):
        """清理超过指定天数的记录。"""
        from cache_manager import _load_cache, _save_cache
        cache = _load_cache()
        old_date = (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d")
        cache["records"].append({"name": "过期菜", "date": old_date, "meal": "午餐"})
        _save_cache(cache)

        cleanup(7)
        cache = _load_cache()
        found = [r for r in cache["records"] if r["name"] == "过期菜"]
        # 15天 > 7天，应被清理
        assert not found

    def test_cleanup_preserves_recent(self):
        """清理保留指定天数内的记录。"""
        from cache_manager import _load_cache, _save_cache
        cache = _load_cache()
        today = datetime.now().strftime("%Y-%m-%d")
        cache["records"].append({"name": "今日菜", "date": today, "meal": "午餐"})
        _save_cache(cache)

        cleanup(7)
        cache = _load_cache()
        found = [r for r in cache["records"] if r["name"] == "今日菜"]
        assert found

    def test_empty_cache_returns_empty(self):
        """缓存文件不存在时返回空集合。"""
        from cache_manager import _load_cache, _save_cache
        # 清空缓存
        _save_cache({"records": []})
        excluded = get_excluded_dishes(7)
        assert excluded == set()

    def test_multiple_dishes_excluded(self):
        """多道菜品同时排除。"""
        add_record(["菜A", "菜B", "菜C"], "午餐")
        excluded = get_excluded_dishes(7)
        assert "菜A" in excluded
        assert "菜B" in excluded
        assert "菜C" in excluded

    def test_duplicate_record(self):
        """同一菜品多次记录保留，排除列表只出现一次（set）。"""
        add_record(["鱼香肉丝"], "午餐")
        add_record(["鱼香肉丝"], "晚餐")
        excluded = get_excluded_dishes(7)
        assert "鱼香肉丝" in excluded
        # 返回的是 set，重复项不会导致两个条目
        assert isinstance(excluded, set)
