# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 全局语言规范

- 日常对话、需求沟通、逻辑解释、文字说明、总结回复、反问确认、流程指引全部使用简体中文
- 代码片段、编程语法、命令行指令、技术专有名词、报错原生信息、参数标识、官方术语、大小写变量，原样保留英文，不强行翻译
- 禁止中英混杂式闲聊，禁止无意义英文短句、英文默认提示、英文客套话术
- 所有确认问题、询问补充信息、权限提示，均使用中文提问
- 不因包含代码就整体切换英文模式，主体行文依旧中文

## 项目概述

基于 AI 的每日三餐推荐系统，运行在青龙面板定时任务平台。根据天气、季节、城市和菜品库，通过 LLM API 推荐午餐和晚餐（每餐两菜一汤），并支持自动发现新菜品扩充库。

## 架构

```
src/
├── recommend_daily.py       — 入口：获取天气 → AI 推荐 → 推送通知
├── update_library.py        — 独立入口：AI 发现新菜 → 自动入库
└── core/
    ├── recommender.py       — 核心：构建 prompt、解析 AI 返回、编排推荐流程
    ├── ai_client.py         — LLM 客户端封装（OpenAI Chat Completions 兼容）
    ├── dish_manager.py      — 菜品库 CRUD（dishes.json），去重、新增/更新
    ├── cache_manager.py     — 短期排除缓存（cache.json），防止 N 日内重复推荐
    ├── weather.py           — itboy 天气 API 客户端，失败降级返回
    ├── push.py              — ShowDoc 推送客户端（微信通知）
    └── config.py            — 加载 config.json 为 SimpleNamespace，支持点号访问
data/
├── config.json              — AI 提供商、城市、天气城市代码、缓存天数、推送地址
├── profile.json             — 用户画像（常驻地、口味、菜系偏好、饮食限制等）
├── enums.json               — 枚举定义（菜系、口味、饮食类型等可配置值）
├── dishes.json              — 菜品库，数组格式，每条含元数据
└── cache.json               — 推荐历史记录
```

## 数据文件

- `dishes.json` — 菜品库，数组格式 `{"name": "...", "reason": "..."}`
- `cache.json` — 推荐历史记录，`{"records": [{"name", "date", "meal"}]}`
- `config.json` — AI 提供商、城市、天气城市代码、缓存天数、推送地址
- `profile.json` — 用户画像（常驻地、口味、菜系偏好、饮食限制等）
- `enums.json` — 枚举定义（菜系、口味、饮食类型等可配置值）

## 关键行为

- **不重复逻辑**：`cache_manager.get_excluded_dishes(no_repeat_days)` 读取 cache.json，N 天内推荐过的菜品通过 prompt 告知 AI 避开
- **去重**：`dish_manager.deduplicate()` 合并同名菜品（忽略大小写和空格）；`add_new_dishes()` 新增或更新理由
- **优雅降级**：天气 API 失败返回 `("未知", "未知")`；AI 调用失败返回 None——推送失败通知
- **失败推送**：天气获取失败、AI 推荐失败、菜品库更新失败均推送通知

## 部署

青龙面板定时任务：

- `recommend_daily.py` — cron `30 8 * * *`（每天 8:30）：三餐推荐
- `update_library.py` — cron `30 6 * * 1`（每周一 6:30）：发现新菜

## Git 管理

```bash
# 初始化仓库
git init
git add .
git commit -m "初始提交：AI三餐推荐系统"
```

- `data/config.json` 已在 `.gitignore` 中（包含 API Key 和推送 Token），提交前确认不误传
- 所有文档文件（实施计划、设计文档、需求文档等）中的配置示例**必须使用占位符**，严禁写入真实凭据
- 提交前做敏感信息检查：`git diff --cached | grep -E 'api_key|push_url|sk-|token' | grep -v 'YOUR_' | grep -v '｛'`
- 提交信息用中文撰写，简明说明变更原因
- 功能变更后同步更新 `资料库/需求文档/` 中的变更记录

## 开发命令

```bash
# 首次使用：从模板复制配置文件
cp data/config.example.json data/config.json
cp data/profile.example.json data/profile.json

# 运行主推荐流程
python src/recommend_daily.py

# 运行菜品库更新
python src/update_library.py

# 手动去重
python -c "from core.dish_manager import deduplicate; deduplicate()"

# 清理旧缓存记录（例如保留最近30天）
python -c "from core.cache_manager import cleanup; cleanup(30)"
```

无包管理器，无测试框架，无 linter。依赖：`requests`。

## 敏感信息安全

- **真实凭据只能放在 `data/config.json`**（已 gitignore），其余任何文件禁止出现真实 API Key、Token、推送地址
- 文档、示例、实施计划中的配置示例统一使用占位符：`YOUR_API_KEY_HERE`、`YOUR_PUSH_URL_HERE`、`sk-...` 等
- 凡是在代码或文档中出现 `api_key`、`push_url`、`token` 等字段名时，先确认写入的是变量引用还是真实值
- 若不慎将凭据提交到 Git，立即告知团队成员，并：
  1. 轮换密钥（旧密钥作废）
  2. 用 `git filter-branch` 从全历史中清洗
  3. `git push --force` 覆盖远程
  4. 在 CLAUDE.md 中补充预防规则
- `data/config.json` 不在提交范围内，但**复制其内容到文档/计划/示例中时**必须替换为占位符

## 文档管理

- 每次需求功能变更后，需在 `资料库/需求文档/` 中添加对应的需求变更文档，记录变更内容、原因和影响范围
