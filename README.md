# AI 每日三餐推荐系统

每天早上 8:30 自动用 AI 给你推荐午餐和晚餐，每餐两菜一汤，推送到微信。

---

## 一、青龙面板部署（完整步骤）

> 以下操作全部在青龙面板网页上完成，不需要登录服务器。

### 第 1 步：拉取项目代码

1. 打开青龙面板 → **定时任务** → **新建任务**
2. 填入以下内容：

| 字段 | 值 |
|------|-----|
| 名称 | `拉取 meal_recommender` |
| 命令 | `git clone https://github.com/2757571500/meal_recommender.git /ql/scripts/meal_recommender` |
| 定时规则 | 留空或填 `0 0 1 1 *`（不会重复执行） |

3. 点击 **确定**，然后点击 **运行** 一次
4. 运行成功后，检查 `/ql/scripts/meal_recommender/` 目录是否存在

### 第 2 步：创建配置文件

> `profile.json`、`enums.json`、`dishes.json` 已有默认值，**只需创建 `config.json`**

1. 打开青龙面板 → **配置文件** → 左侧文件列表找到 `/ql/scripts/meal_recommender/data/` 目录
2. 如果看到 `config.example.json`，直接复制一份重命名为 `config.json`
   - 或者新建文件 `config.json`，填入以下内容：

```json
{
  "ai": {
    "provider": "longcat",
    "base_url": "https://api.longcat.chat/openai",
    "api_key": "在这里填你的API密钥",
    "model": "LongCat-Flash-Chat-2602-Exp"
  },
  "push": {
    "push_url": "在这里填你的推送地址"
  }
}
```

3. 把 `api_key` 换成你的真实密钥，`push_url` 换成你的 ShowDoc 推送地址
4. 点击 **保存**

### 第 3 步：安装依赖

1. 打开青龙面板 → **依赖管理** → **Python 依赖**
2. 在输入框输入 `requests`，点击 **安装**
3. 等待安装完成（显示"安装成功"）

### 第 4 步：创建定时任务

创建两个任务：

**任务 1：每日三餐推荐**

| 字段 | 值 |
|------|-----|
| 名称 | `三餐推荐` |
| 命令 | `cd /ql/scripts/meal_recommender && python src/recommend_daily.py` |
| 定时规则 | `30 8 * * *`（每天早上 8:30） |

**任务 2：每周扩充菜品库**

| 字段 | 值 |
|------|-----|
| 名称 | `菜品库更新` |
| 命令 | `cd /ql/scripts/meal_recommender && python src/update_library.py` |
| 定时规则 | `30 6 * * 1`（每周一早上 6:30） |

### 第 5 步：首次测试

1. 先手动运行一次 **菜品库更新**（生成菜品数据）
2. 再手动运行一次 **三餐推荐**
3. 查看运行日志，确认没有报错

---

## 二、配置文件说明

### config.json（必填，含密钥）

放在 `data/config.json`，**不要提交到 Git**。

| 字段 | 说明 | 去哪获取 |
|------|------|---------|
| `ai.api_key` | AI 模型的 API 密钥 | 去你的 AI 服务商后台申请 |
| `ai.base_url` | API 接口地址 | AI 服务商提供，通常不用改 |
| `ai.model` | 模型名称 | AI 服务商提供，通常不用改 |
| `push.push_url` | 微信推送地址 | 去 ShowDoc 官网注册获取 |

### profile.json（按需修改）

放在 `data/profile.json`，控制推荐的口味偏好。

| 字段 | 说明 | 可填什么 |
|------|------|---------|
| `hometown` | 你所在的城市 | 如 `合肥`、`上海` |
| `weather_city_code` | 天气城市代码 | 如 `101220101`（和风天气代码） |
| `no_repeat_days` | 多少天内不重复推荐同一道菜 | 建议 `7` |
| `serving_size` | 几个人吃 | `1`、`2`、`3`... |
| `max_cook_time` | 每餐最多做多久（分钟） | `30`（半小时）、`60`（1小时） |
| `skill_level` | 你的厨艺 | `新手` / `普通` / `熟练` |
| `diet_type` | 饮食限制 | `不限` / `蛋奶素` / `纯素` / `清真` |
| `taste` | 喜欢的口味 | `["偏咸", "偏辣"]`（从 enums.json 选择） |
| `cuisine_preferences` | 喜欢的菜系 | `["川菜", "徽菜"]`（从 enums.json 选择） |
| `avoid_ingredients` | 不吃的食材 | `["羊肉", "内脏"]` |

### enums.json（一般不用改）

`taste`（口味）、`cuisine`（菜系）、`diet_type`（饮食类型）等字段的可选值都定义在这个文件里。想加新菜系或新口味时直接编辑它就行。

---

## 三、运行原理

```
每日 8:30 → 获取今日天气 → 根据口味过滤菜品库
         → AI 从剩余菜品中选午餐+晚餐
         → 推送到微信通知你
```

- 推荐过的菜 N 天内不会重复出现（天数在 profile.json 设置）
- 天气 API 或 AI 调用失败时，会给微信推送失败通知
- 菜品库初始为空，**先跑一次「菜品库更新」任务**填充菜品

---

## 四、常见问题

**Q: 运行报错 "No module named requests"**

没装依赖，去青龙「依赖管理」安装 `requests`。

**Q: 运行报错 "config.json 未找到"**

没创建配置文件。按上面第 2 步创建 `data/config.json`。

**Q: 提示 "菜品库为空"**

没跑过菜品库更新任务。先手动运行一次 `update_library.py`。

**Q: AI 推荐失败**

检查 `config.json` 里的 `api_key` 是否填对了，模型服务是否可用。

**Q: 日志乱码或中文显示为问号**

青龙面板默认编码问题，不影响运行结果，可忽略。

---

## 五、项目结构

```
src/
├── recommend_daily.py       — 三餐推荐（定时任务入口）
├── update_library.py        — 菜品库更新（定时任务入口）
└── core/
    ├── config.py            — 读取 config.json / profile.json / enums.json
    ├── ai_client.py         — 调用 AI 模型 API
    ├── recommender.py       — 推荐逻辑（过滤 + prompt 组装 + 结果解析）
    ├── dish_manager.py      — 菜品库管理（新增、去重）
    ├── cache_manager.py     — 推荐历史缓存（防重复）
    ├── weather.py           — 获取天气
    └── push.py              — 微信推送
data/                        — JSON 数据文件
```
