import re
from datetime import datetime
from ai_client import AIClient
from dish_manager import list_dish_names, add_new_dishes
from cache_manager import get_excluded_dishes, add_record


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


def _build_prompt(city, weather_condition, weather_temp, no_repeat_days):
    """组装发给 AI 的推荐 Prompt。

    输入：城市、天气、时令、菜品库、排除列表
    输出：要求 AI 从已有菜品库中选择适合今日的推荐。
    """
    now = datetime.now()
    season = get_season(now.month)
    month = now.month

    dish_names = list_dish_names()
    dish_list = "、".join(dish_names) if dish_names else "（暂无菜品库）"

    excluded = get_excluded_dishes(no_repeat_days)
    excluded_list = "、".join(sorted(excluded)) if excluded else "（无）"

    prompt = f"""你是一名熟悉中国各地饮食的美食专家。

当前时令：{season}季（{month}月）
所在地区：{city}
今日天气：{weather_condition} {weather_temp}

已有菜品库：{dish_list}

最近{no_repeat_days}天内推荐过的菜品（请避开）：{excluded_list}

请从以上菜品库中选择适合今日的菜品，推荐午餐和晚餐，每餐两菜一汤，并为每道菜附上推荐理由。
要求：
1. 符合当前时令和地区饮食习惯
2. 午餐和晚餐菜品不重复
3. 避开排除列表中的菜品
4. 仅从已有菜品库中选择，不要自行添加菜品库之外的菜
5. 推荐理由需结合时令、天气、地区饮食习惯等

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


def _build_discover_prompt(city, weather_condition, weather_temp):
    """组装发给 AI 的菜品发现 Prompt。

    要求 AI 根据时令、天气、地区推荐新菜品，用于扩充菜品库。
    """
    now = datetime.now()
    season = get_season(now.month)
    month = now.month

    dish_names = list_dish_names()
    dish_list = "、".join(dish_names) if dish_names else "（暂无菜品库）"

    prompt = f"""你是一名熟悉中国各地饮食的美食专家。

当前时令：{season}季（{month}月）
所在地区：{city}
今日天气：{weather_condition} {weather_temp}

已有菜品库：{dish_list}

请推荐 5-8 道不在以上菜品库中的新菜，加入菜品库。每道菜附上推荐理由。
要求：
1. 符合当前时令和地区饮食习惯
2. 不能与已有菜品库中的菜重复
3. 推荐理由需结合时令、天气、地区饮食习惯

返回格式（不要输出其他内容）：
- 菜名（推荐理由）
- 菜名（推荐理由）"""
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
            # 匹配格式: - 菜名（理由）
            match = re.match(r"-\s*([^（]+?)(?:（([^）]*)）)?\s*$", line)
            if match:
                name = match.group(1).strip()
                reason = match.group(2).strip() if match.group(2) else ""
                result[current_meal].append({
                    "name": name,
                    "reason": reason
                })

    return result


def _parse_dish_list(text):
    """解析 AI 返回的菜品列表（不含三餐分类），用于菜品发现。

    输入格式：
        - 菜名（推荐理由）
        - 菜名（推荐理由）
    """
    dishes = []
    for line in text.strip().split("\n"):
        line = line.strip()
        if line.startswith("-"):
            match = re.match(r"-\s*([^（]+?)(?:（([^）]*)）)?\s*$", line)
            if match:
                name = match.group(1).strip()
                reason = match.group(2).strip() if match.group(2) else ""
                dishes.append({"name": name, "reason": reason})
    return dishes


def _format_output(city, result):
    """将推荐结果格式化为控制台输出的字符串。"""
    now = datetime.now().strftime("%Y-%m-%d")
    lines = [f"==== {now} {city} 推荐 ====", ""]

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


def recommend(config, weather_condition, weather_temp):
    """推荐主流程：从已有菜品库中选菜推荐今日午餐和晚餐。

    返回格式化后的推荐文本，AI 调用失败时返回 None。
    不涉及新菜发现和入库，只更新缓存用于短期不重复。
    """
    client = AIClient(config.ai.base_url, config.ai.api_key, config.ai.model)
    prompt = _build_prompt(config.city, weather_condition, weather_temp, config.cache.no_repeat_days)

    print("正在获取 AI 推荐...")
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

    output = _format_output(config.city, result)
    return output


def discover_dishes(config, weather_condition, weather_temp):
    """菜品库更新：调用 AI 发现新菜，自动入库。

    用于青龙面板独立定时任务，与推荐分开执行。
    """
    client = AIClient(config.ai.base_url, config.ai.api_key, config.ai.model)
    prompt = _build_discover_prompt(config.city, weather_condition, weather_temp)

    print("正在获取 AI 新菜推荐...")
    try:
        text = client.chat([
            {"role": "system", "content": "你是美食专家，只返回指定格式的菜品列表。"},
            {"role": "user", "content": prompt}
        ], temperature=0.7, max_tokens=1024)
    except Exception as e:
        print(f"AI 调用失败: {e}")
        return None

    dishes = _parse_dish_list(text)
    if not dishes:
        print("AI 未返回有效菜品")
        return None

    added, updated = add_new_dishes(dishes)
    if added:
        print(f"新增菜品 {len(added)} 个:")
        for d in added:
            print(f"  - {d['name']}（{d.get('reason', '')}）")
    if updated:
        print(f"更新理由 {len(updated)} 个: {[d['name'] for d in updated]}")
    if not added and not updated:
        print("菜品库已包含推荐菜品，无新增")

    return added, updated
