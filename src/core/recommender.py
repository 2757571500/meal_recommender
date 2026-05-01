"""推荐引擎：菜品过滤、Prompt 组装、AI 返回解析、结果格式化。

核心函数：
    recommend(config,天气,温度,profile,enums)    — 推荐主流程
    discover_dishes(config,天气,温度,enums,profile) — 菜品发现主流程
    filter_dishes(dishes, profile)                — 根据画像硬过滤菜品
"""
import json
import re
from datetime import datetime
from core.ai_client import AIClient
from core.dish_manager import list_dish_names, add_new_dishes, load_dishes
from core.cache_manager import get_excluded_dishes, add_record


def get_season(month=None):
    """根据月份返回季节（春/夏/秋/冬）。month 为 None 时自动取当前月。"""
    if month is None:
        month = datetime.now().month
    if 3 <= month <= 5:
        return "春"
    elif 6 <= month <= 8:
        return "夏"
    elif 9 <= month <= 11:
        return "秋"
    else:
        return "冬"


def filter_dishes(dishes, profile):
    """根据用户画像对菜品库做硬过滤。

    过滤规则：
    1. diet_type：用户无限制则全部保留；有限制则保留"匹配类型 + 无限制"菜品
    2. difficulty：菜品难度不高于用户 skill_level（新手 < 普通 < 熟练）
    3. prep_time：菜品耗时不超过用户 max_cook_time

    参数：
        dishes: 菜品字典列表
        profile: 用户画像 SimpleNamespace
    返回：
        过滤后的菜品列表
    """
    # 难度等级映射，用于比较
    difficulty_order = {"新手": 0, "普通": 1, "熟练": 2}
    user_level = difficulty_order.get(profile.skill_level, 1)

    # diet_type 可保留的类型集合
    # 用户无限制时保留全部；有限制时保留"匹配 + 无限制"
    if profile.diet_type == "无限制":
        keep_diet_types = None  # None 表示全部保留
    else:
        keep_diet_types = {profile.diet_type, "无限制"}

    filtered = []
    for d in dishes:
        # diet_type 过滤
        if keep_diet_types is not None and d.get("diet_type") not in keep_diet_types:
            continue

        # 难度过滤：菜品难度不能高于用户水平
        if difficulty_order.get(d.get("difficulty", "普通"), 1) > user_level:
            continue

        # 耗时过滤
        if d.get("prep_time", 999) > profile.max_cook_time:
            continue

        filtered.append(d)

    return filtered


def _build_prompt(weather_city, weather_condition, weather_temp, no_repeat_days, profile, filtered_dishes):
    """组装发给 AI 的推荐 Prompt。

    包含当前天气城市名和用户常驻地两套地理信息，覆盖出差场景。
    菜品列表附带元数据（菜系、口味、难度、耗时），帮助 AI 精准匹配。
    """
    now = datetime.now()
    season = get_season(now.month)
    month = now.month

    # 菜品列表附带元数据，每行一道菜
    dish_lines = []
    for d in filtered_dishes:
        taste_str = "、".join(d.get("taste", []))
        tags = "、".join(d.get("dietary_tags", [])) or "无"
        dish_lines.append(f"  - {d['name']}（{d['cuisine']} | {d['difficulty']} | {d['prep_time']}分钟 | {taste_str} | {tags}）")
    dish_text = "\n".join(dish_lines) if dish_lines else "（暂无菜品库）"

    excluded = get_excluded_dishes(no_repeat_days)
    excluded_list = "、".join(sorted(excluded)) if excluded else "（无）"

    taste_str = "、".join(profile.taste) if profile.taste else "无特定偏好"
    cuisine_str = "、".join(profile.cuisine_preferences) if profile.cuisine_preferences else "无特定偏好"
    avoid_str = "、".join(profile.avoid_ingredients) if profile.avoid_ingredients else "无"

    prompt = f"""你是一名熟悉中国各地饮食的美食专家。

当前时令：{season}季（{month}月）
天气城市：{weather_city}
今日天气：{weather_condition} {weather_temp}

用户常驻地：{profile.hometown}
就餐人数：{profile.serving_size} 人
厨艺水平：{profile.skill_level}
每餐可接受烹饪时间：{profile.max_cook_time} 分钟
口味偏好：{taste_str}
菜系偏好：{cuisine_str}
忌口食材：{avoid_str}

已有菜品库（已根据饮食偏好筛选，附元数据）：
{dish_text}

最近{no_repeat_days}天内推荐过的菜品（请避开）：{excluded_list}

请从以上菜品库中选择适合今日的菜品，推荐午餐和晚餐，每餐两菜一汤，并为每道菜附上推荐理由。
要求：
1. 符合当前时令和用户常驻地的饮食习惯
2. 午餐和晚餐菜品不重复
3. 避开排除列表中的菜品
4. 仅从已有菜品库中选择，不要自行添加菜品库之外的菜
5. 优先推荐偏好菜系，避开忌口食材
6. 考虑厨艺水平和烹饪时间，不要推荐超出用户能力的菜品

返回格式：
午餐：
- 菜名1（理由：...）
- 菜名2（理由：...）
- 汤名1（理由：...）

晚餐：
- 菜名3（理由：...）
- 菜名4（理由：...）
- 汤名2（理由：...）"""
    return prompt


def _build_discover_prompt(weather_city, weather_condition, weather_temp, enums, profile):
    """组装发给 AI 的菜品发现 Prompt。

    包含用户常驻地、菜系偏好、口味、饮食限制等画像信息，
    确保 AI 推荐的菜品符合用户整体饮食风格。
    要求 AI 返回 JSON 数组，字段值必须严格从枚举中取值。
    """
    now = datetime.now()
    season = get_season(now.month)
    month = now.month

    dish_names = list_dish_names()
    dish_list = "、".join(dish_names) if dish_names else "（暂无菜品库）"

    cuisine_list = "、".join(enums.get("cuisine", []))
    taste_list = "、".join(enums.get("dish_taste", []))
    diet_type_list = "、".join(enums.get("diet_type", []))
    dietary_tags_list = "、".join(enums.get("dietary_tags", []))

    cuisine_pref_str = "、".join(profile.cuisine_preferences) if profile.cuisine_preferences else "无特定偏好，根据当地饮食特色推荐"
    taste_pref_str = "、".join(profile.taste) if profile.taste else "无特定偏好"
    avoid_str = "、".join(profile.avoid_ingredients) if profile.avoid_ingredients else "无"

    prompt = f"""你是一名熟悉中国各地饮食的美食专家。

当前时令：{season}季（{month}月）
所在地区：{weather_city}
今日天气：{weather_condition} {weather_temp}

用户常驻地：{profile.hometown}
用户菜系偏好：{cuisine_pref_str}
用户口味偏好：{taste_pref_str}
用户饮食类型：{profile.diet_type}
忌口食材：{avoid_str}
已有菜品库：{dish_list}

请推荐 5-8 道不在以上菜品库中的新菜，加入菜品库。每道菜附上推荐理由。
要求：
1. 符合当前时令和用户常驻地的饮食习惯
2. 优先推荐用户偏好菜系的菜品
3. 符合用户口味偏好和饮食类型
4. 避开忌口食材
5. 不能与已有菜品库中的菜重复
6. 推荐理由需结合时令、天气、地区饮食习惯
	7. **菜名必须是真实存在的菜品名称**，不能自行组合或编造菜名（例如不能将"毛峰茶"和"口水鸡"组合成"毛峰茶香口水鸡"，应直接使用"口水鸡"原名）

重要：请严格按以下 JSON 数组格式返回，不要包含其他内容，不要使用 markdown 代码块标记：

[
  {{
    "name": "菜名",
    "reason": "推荐理由",
    "cuisine": "菜系",
    "taste": ["口味标签"],
    "difficulty": "难度",
    "prep_time": 烹饪分钟数(整数),
    "ingredients": ["主要食材"],
    "diet_type": "饮食类型",
    "dietary_tags": ["特殊标签"]
  }}
]

字段值必须从以下范围中选择，不能使用范围之外的值：
- cuisine（选一）：{cuisine_list}
- taste（可多选）：{taste_list}
- difficulty（选一）：新手、普通、熟练
- diet_type（选一）：{diet_type_list}
- dietary_tags（可多选，无则留空数组）：{dietary_tags_list}"""
    return prompt


def _parse_response(text):
    """解析 AI 返回的三餐推荐文本。

    AI 返回格式示例：
        午餐：
        - 麻婆豆腐（麻辣下饭）
        - 蒜蓉空心菜（时令蔬菜）
    正则提取菜名和理由。
    """
    result = {"lunch": [], "dinner": []}
    current_meal = None

    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        if "午餐" in line:
            current_meal = "lunch"
            continue
        if "晚餐" in line:
            current_meal = "dinner"
            continue
        if current_meal and line.startswith("-"):
            match = re.match(r"-\s*([^（]+?)(?:（([^）]*)）)?\s*$", line)
            if match:
                name = match.group(1).strip()
                reason = match.group(2).strip() if match.group(2) else ""
                result[current_meal].append({"name": name, "reason": reason})

    return result


def _parse_json_dish_list(text):
    """解析 AI 返回的 JSON 数组格式菜品列表。

    用于菜品发现，AI 返回纯 JSON 数组（可能被 markdown 代码块包裹）。
    解析失败时尝试清理后重试。
    """
    text = text.strip()
    # 去除可能的 markdown 代码块标记 ```json ... ```
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    try:
        dishes = json.loads(text)
        if isinstance(dishes, list):
            return dishes
        return []
    except json.JSONDecodeError:
        print("AI 返回的 JSON 解析失败")
        return []


def _format_output(profile, result):
    """将推荐结果格式化为控制台输出的字符串。

    参数：
        profile: 用户画像 SimpleNamespace（用于标题中的城市名）
        result: 解析后的推荐结果字典
    """
    now = datetime.now().strftime("%Y-%m-%d")
    lines = [f"==== {now} {profile.hometown} 推荐 ====", ""]

    labels = {"lunch": "午餐", "dinner": "晚餐"}
    for meal_key in ["lunch", "dinner"]:
        lines.append(f"--- {labels[meal_key]} ---")
        for i, item in enumerate(result.get(meal_key, []), 1):
            if item.get("reason"):
                lines.append(f"{i}. {item['name']}（{item['reason']}）")
            else:
                lines.append(f"{i}. {item['name']}")
        lines.append("")

    return "\n".join(lines)


def recommend(config, weather_condition, weather_temp, profile, enums, weather_city):
    """推荐主流程：从已有菜品库中选菜推荐今日午餐和晚餐。

    流程：
    1. 加载菜品库
    2. 根据用户画像硬过滤
    3. 调用 AI 推荐
    4. 解析结果
    5. 更新缓存（排除列表）
    6. 格式化输出

    参数：
        config: 运行配置
        weather_condition: 天气状况
        weather_temp: 温度
        profile: 用户画像
        enums: 枚举定义
        weather_city: 天气城市名（用于 prompt 中的地理位置）
    返回：
        格式化后的推荐文本，AI 调用失败或菜品库为空时返回 None
    """
    all_dishes = load_dishes()
    if not all_dishes:
        print("菜品库为空，请先运行 update_library.py 填充菜品库")
        return None

    filtered = filter_dishes(all_dishes, profile)
    if not filtered:
        print("过滤后无可用菜品，请检查 profile 配置是否过于严格")
        return None

    print(f"菜品库共 {len(all_dishes)} 道菜，过滤后 {len(filtered)} 道可用")

    client = AIClient(config.ai.base_url, config.ai.api_key, config.ai.model)
    prompt = _build_prompt(weather_city, weather_condition, weather_temp,
                          profile.no_repeat_days, profile, filtered)

    print("正在获取 AI 推荐...")
    print("===== 推荐 Prompt =====")
    print(prompt)
    print("=======================")
    try:
        text = client.chat([
            {"role": "system", "content": "你是美食专家，只返回指定格式的结果。"},
            {"role": "user", "content": prompt}
        ], temperature=0.7, max_tokens=1024)
    except Exception as e:
        print(f"AI 调用失败: {e}")
        return None

    result = _parse_response(text)

    # 将本次推荐的菜品写入缓存，下次推荐时排除
    for meal_key, meal_label in [("lunch", "午餐"), ("dinner", "晚餐")]:
        names = [item["name"] for item in result.get(meal_key, [])]
        if names:
            add_record(names, meal_label)

    output = _format_output(profile, result)
    return output


def discover_dishes(config, weather_condition, weather_temp, enums, profile, weather_city):
    """菜品库更新：调用 AI 发现新菜，自动入库。

    流程：
    1. 调用 AI 按 JSON 数组格式生成菜品
    2. 解析 JSON
    3. 枚举校验
    4. 入库

    参数：
        config: 运行配置
        weather_condition: 天气状况
        weather_temp: 温度
        enums: 枚举定义
        profile: 用户画像
        weather_city: 天气城市名
    返回：
        (added, updated) 元组，AI 调用失败时返回 None
    """
    client = AIClient(config.ai.base_url, config.ai.api_key, config.ai.model)
    prompt = _build_discover_prompt(weather_city, weather_condition, weather_temp, enums, profile)

    print("正在获取 AI 新菜推荐...")
    print("===== 发现菜品 Prompt =====")
    print(prompt)
    print("============================")
    try:
        text = client.chat([
            {"role": "system", "content": "你是美食专家，只返回指定格式的 JSON 数组。"},
            {"role": "user", "content": prompt}
        ], temperature=0.7, max_tokens=2048)
    except Exception as e:
        print(f"AI 调用失败: {e}")
        return None

    dishes = _parse_json_dish_list(text)
    if not dishes:
        print("AI 未返回有效菜品")
        return None

    # 传入 enums 做字段值校验
    added, updated = add_new_dishes(dishes, enums=enums)
    if added:
        print(f"新增菜品 {len(added)} 个:")
        for d in added:
            print(f"  - {d['name']}（{d.get('cuisine', '')} | {d.get('difficulty', '')} | {d.get('prep_time', '')}分钟）")
    if updated:
        print(f"更新理由 {len(updated)} 个: {[d['name'] for d in updated]}")
    if not added and not updated:
        print("菜品库已包含推荐菜品，无新增")

    return added, updated
