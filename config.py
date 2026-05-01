import json
import os
from types import SimpleNamespace


def load_config(path=None):
    """读取 config.json，返回 SimpleNamespace 对象以支持 cfg.ai.model 式访问。"""
    if path is None:
        path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    cfg = SimpleNamespace()
    # 嵌套字典转 SimpleNamespace，保持属性访问一致性
    cfg.ai = SimpleNamespace(**data["ai"])
    cfg.city = data["city"]
    cfg.weather = SimpleNamespace(**data["weather"])
    cfg.cache = SimpleNamespace(**data["cache"])
    cfg.push = SimpleNamespace(**data["push"])
    return cfg
