"""配置加载：运行配置、用户画像、枚举定义三文件分离加载。

load_config()   — config.json，运行配置（AI、天气、缓存、推送）
load_profile()  — profile.json，用户画像（口味、菜系、饮食限制等）
load_enums()    — enums.json，枚举值定义（可配置，加枚举无需改代码）
"""
import json
import os
from types import SimpleNamespace


def _data_path(filename):
    """返回 data/ 下某文件的绝对路径。"""
    return os.path.join(os.path.dirname(__file__), "..", "..", "data", filename)


def _check_example(filename):
    """配置文件缺失时打印引导信息，提示用户从 example 模板复制。"""
    path = _data_path(filename)
    example = _data_path(filename.replace(".json", ".example.json"))
    print(f"[配置缺失] 未找到 {path}")
    if os.path.exists(example):
        print(f"  请复制模板文件并填入真实凭据：")
        print(f"    cp {example} {path}")


def load_config(path=None):
    """读取 config.json，返回 SimpleNamespace 对象以支持 cfg.ai.model 式访问。

    参数：
        path: 配置文件路径，为 None 时默认为脚本同目录下的 config.json
    返回：
        包含运行配置的 SimpleNamespace 对象
    """
    if path is None:
        path = _data_path("config.json")
    if not os.path.exists(path):
        _check_example("config.json")
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    cfg = SimpleNamespace()
    cfg.ai = SimpleNamespace(**data["ai"])
    cfg.push = SimpleNamespace(**data["push"])
    return cfg


def load_profile(path=None):
    """读取 profile.json（用户画像），返回 SimpleNamespace。

    参数：
        path: 画像文件路径，为 None 时默认为脚本同目录下的 profile.json
    返回：
        包含用户偏好信息的 SimpleNamespace 对象
    """
    if path is None:
        path = _data_path("profile.json")
    if not os.path.exists(path):
        _check_example("profile.json")
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return SimpleNamespace(**data)


def load_enums(path=None):
    """读取 enums.json（枚举定义），返回原始字典。

    参数：
        path: 枚举文件路径，为 None 时默认为脚本同目录下的 enums.json
    返回：
        包含所有枚举值定义的字典
    """
    if path is None:
        path = _data_path("enums.json")
    if not os.path.exists(path):
        print(f"[配置缺失] 未找到 {path}")
        print(f"  enums.json 是系统运行必需的枚举定义文件，无法自动生成。")
        print(f"  请确保 data/ 目录完整，或从 Git 仓库拉取最新版本。")
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
