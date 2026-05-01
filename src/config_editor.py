#!/usr/bin/env python3
# -- coding: utf-8 --
"""配置网页编辑器：通过浏览器可视化编辑 config.json、profile.json、enums.json。

启动：
    python src/config_editor.py
    python src/config_editor.py -p 9090

自动在浏览器中打开编辑页面。
"""
import json
import os
import sys
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

PORT = 8089

# data/ 目录相对于此文件的路径
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _read_json(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(filename, data):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── 前端 HTML ──────────────────────────────────────────────────────
PAGE_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>配置编辑器</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, "Segoe UI", "Noto Sans SC", sans-serif; background: #f5f5f5; color: #333; padding: 20px; }
.header { max-width: 800px; margin: 0 auto 16px; display: flex; justify-content: space-between; align-items: center; }
.header h1 { font-size: 22px; }
.btn-save { background: #1677ff; color: #fff; border: none; padding: 8px 24px; border-radius: 6px; font-size: 14px; cursor: pointer; }
.btn-save:hover { background: #4096ff; }
.btn-save:disabled { background: #ccc; cursor: not-allowed; }
.container { max-width: 800px; margin: 0 auto; }
.panel { background: #fff; border-radius: 8px; margin-bottom: 12px; box-shadow: 0 1px 4px rgba(0,0,0,.08); overflow: hidden; }
.panel-header { display: flex; justify-content: space-between; align-items: center; padding: 14px 18px; cursor: pointer; user-select: none; font-size: 15px; font-weight: 600; background: #fafafa; border-bottom: 1px solid #eee; }
.panel-header .arrow { transition: transform .2s; font-size: 12px; }
.panel-header.collapsed .arrow { transform: rotate(-90deg); }
.panel-header.collapsed { border-bottom: none; }
.panel-body { padding: 18px; }
.panel-body.hidden { display: none; }
.form-row { display: flex; align-items: center; margin-bottom: 12px; gap: 10px; }
.form-row label { width: 110px; flex-shrink: 0; font-size: 13px; color: #555; text-align: right; }
.form-row input[type="text"],
.form-row input[type="number"],
.form-row input[type="password"] { flex: 1; padding: 7px 10px; border: 1px solid #d9d9d9; border-radius: 4px; font-size: 13px; outline: none; }
.form-row input:focus { border-color: #1677ff; box-shadow: 0 0 0 2px rgba(22,119,255,.15); }
.form-row select { flex: 1; padding: 7px 10px; border: 1px solid #d9d9d9; border-radius: 4px; font-size: 13px; background: #fff; outline: none; }
.form-hint { font-size: 12px; color: #999; margin-left: 120px; margin-top: -8px; margin-bottom: 12px; }
.checkbox-group { flex: 1; display: flex; flex-wrap: wrap; gap: 6px; }
.checkbox-group label { width: auto; display: flex; align-items: center; gap: 4px; font-size: 13px; cursor: pointer; padding: 4px 10px; border: 1px solid #d9d9d9; border-radius: 4px; background: #fff; }
.checkbox-group label.checked { border-color: #1677ff; color: #1677ff; background: #e6f4ff; }
.checkbox-group label input { display: none; }
.tag-input { flex: 1; display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.tag { display: inline-flex; align-items: center; gap: 4px; padding: 3px 10px; border-radius: 4px; font-size: 13px; background: #f0f0f0; }
.tag .del { cursor: pointer; font-size: 14px; color: #999; line-height: 1; }
.tag .del:hover { color: #ff4d4f; }
.tag-add { display: inline-flex; align-items: center; gap: 2px; padding: 3px 10px; border: 1px dashed #d9d9d9; border-radius: 4px; font-size: 13px; color: #999; cursor: pointer; background: none; }
.tag-add:hover { border-color: #1677ff; color: #1677ff; }
.toast { position: fixed; top: 20px; left: 50%; transform: translateX(-50%); padding: 10px 24px; border-radius: 6px; font-size: 14px; z-index: 999; display: none; }
.toast.ok { background: #f6ffed; border: 1px solid #b7eb8f; color: #389e0d; display: block; }
.toast.err { background: #fff2f0; border: 1px solid #ffccc7; color: #cf1322; display: block; }
.section-title { font-size: 14px; font-weight: 600; margin-bottom: 12px; padding-bottom: 6px; border-bottom: 1px solid #eee; color: #333; }
</style>
</head>
<body>
<div class="header">
  <h1>配置编辑器</h1>
  <button class="btn-save" id="btnSave" onclick="save()">保存配置</button>
</div>
<div id="toast" class="toast"></div>
<div class="container" id="app"></div>

<script>
const FIELDS = {
  config: {
    title: "运行配置",
    fields: [
      { key: "ai.base_url", label: "AI 接口地址", type: "text" },
      { key: "ai.api_key", label: "API Key", type: "password" },
      { key: "ai.model", label: "AI 模型", type: "text" },
      { key: "push.push_url", label: "推送地址", type: "text" },
    ]
  },
  profile: {
    title: "用户画像",
    fields: [
      { key: "hometown", label: "常驻地", type: "text" },
      { key: "weather_city_code", label: "天气城市码", type: "text" },
      { key: "no_repeat_days", label: "不重复天数", type: "number" },
      { key: "serving_size", label: "就餐人数", type: "number" },
      { key: "max_cook_time", label: "最大烹饪时长(分钟)", type: "number" },
      { key: "skill_level", label: "厨艺水平", type: "select", enumKey: "skill_level" },
      { key: "diet_type", label: "饮食类型", type: "select", enumKey: "diet_type" },
      { key: "taste", label: "口味偏好", type: "checkboxes", enumKey: "taste" },
      { key: "cuisine_preferences", label: "菜系偏好", type: "checkboxes", enumKey: "cuisine" },
      { key: "avoid_ingredients", label: "忌口食材", type: "tags" },
    ]
  },
  enums: {
    title: "可选值管理",
    hint: "修改后刷新页面，用户画像中的选项同步更新",
    fields: [
      { key: "taste", label: "口味选项" },
      { key: "cuisine", label: "菜系列表" },
      { key: "diet_type", label: "饮食类型" },
      { key: "dietary_tags", label: "菜品标签" },
      { key: "skill_level", label: "厨艺等级" },
      { key: "dish_taste", label: "菜品口味" },
    ]
  }
};

let data = null;

function getVal(obj, path) {
  return path.split(".").reduce((o, k) => o && o[k], obj);
}

function setVal(obj, path, val) {
  const keys = path.split(".");
  const last = keys.pop();
  const target = keys.reduce((o, k) => o[k], obj);
  target[last] = val;
}

async function load() {
  const r = await fetch("/api/config");
  data = await r.json();
  render();
}

function render() {
  const app = document.getElementById("app");
  app.innerHTML = "";

  for (const [section, def] of Object.entries(FIELDS)) {
    const panel = document.createElement("div");
    panel.className = "panel";

    const hdr = document.createElement("div");
    hdr.className = "panel-header";
    hdr.innerHTML = `<span>${def.title}</span><span class="arrow">▼</span>`;
    const body = document.createElement("div");
    body.className = "panel-body";

    if (def.hint) {
      const hint = document.createElement("div");
      hint.className = "form-hint";
      hint.style.marginLeft = "0";
      hint.textContent = def.hint;
      body.appendChild(hint);
    }

    for (const f of def.fields) {
      if (section === "enums") {
        body.appendChild(buildTagInput(section, f.key, f.label));
      } else if (f.type === "checkboxes") {
        body.appendChild(buildCheckboxes(section, f));
      } else if (f.type === "select") {
        body.appendChild(buildSelect(section, f));
      } else if (f.type === "tags") {
        body.appendChild(buildTagInput(section, f.key, f.label, true));
      } else {
        body.appendChild(buildInput(section, f));
      }
    }

    hdr.addEventListener("click", () => {
      hdr.classList.toggle("collapsed");
      body.classList.toggle("hidden");
    });

    panel.appendChild(hdr);
    panel.appendChild(body);
    app.appendChild(panel);
  }
}

function buildInput(section, f) {
  const row = document.createElement("div");
  row.className = "form-row";
  const val = getVal(data[section], f.key) ?? "";
  row.innerHTML = `<label>${f.label}</label><input type="${f.type}" value="${esc(val)}" data-section="${section}" data-key="${f.key}">`;
  row.querySelector("input").addEventListener("input", (e) => {
    const v = f.type === "number" ? Number(e.target.value) : e.target.value;
    setVal(data[section], f.key, v);
  });
  return row;
}

function buildSelect(section, f) {
  const row = document.createElement("div");
  row.className = "form-row";
  const opts = data.enums[f.enumKey] || [];
  const val = data[section][f.key] || opts[0] || "";
  let html = opts.map(o => `<option value="${esc(o)}"${o===val?" selected":""}>${esc(o)}</option>`).join("");
  row.innerHTML = `<label>${f.label}</label><select data-section="${section}" data-key="${f.key}">${html}</select>`;
  row.querySelector("select").addEventListener("change", (e) => {
    data[section][f.key] = e.target.value;
  });
  return row;
}

function buildCheckboxes(section, f) {
  const row = document.createElement("div");
  row.className = "form-row";
  row.innerHTML = `<label>${f.label}</label><div class="checkbox-group" data-section="${section}" data-key="${f.key}"></div>`;
  const grp = row.querySelector(".checkbox-group");
  const opts = data.enums[f.enumKey] || [];
  const selected = new Set(data[section][f.key] || []);
  for (const o of opts) {
    const lbl = document.createElement("label");
    lbl.className = selected.has(o) ? "checked" : "";
    lbl.innerHTML = `<input type="checkbox" value="${esc(o)}"${selected.has(o)?" checked":""}>${esc(o)}`;
    lbl.querySelector("input").addEventListener("change", (e) => {
      lbl.classList.toggle("checked", e.target.checked);
      const arr = data[section][f.key];
      if (e.target.checked) { if (!arr.includes(o)) arr.push(o); }
      else { data[section][f.key] = arr.filter(v => v !== o); }
    });
    grp.appendChild(lbl);
  }
  return row;
}

function buildTagInput(section, key, label, commaMode) {
  const row = document.createElement("div");
  row.className = "form-row";

  const val = data[section][key];
  const arr = Array.isArray(val) ? val : (typeof val === "string" && commaMode ? val.split(/[,，、 ]+/).filter(Boolean) : []);

  if (!Array.isArray(data[section][key])) {
    data[section][key] = arr;
  }

  row.innerHTML = `<label>${label}</label><div class="tag-input" data-section="${section}" data-key="${key}"></div>`;
  const wrap = row.querySelector(".tag-input");
  renderTags(wrap, section, key, arr, commaMode);
  return row;
}

function renderTags(wrap, section, key, arr, commaMode) {
  wrap.innerHTML = "";
  for (let i = 0; i < arr.length; i++) {
    const t = document.createElement("span");
    t.className = "tag";
    t.innerHTML = `${esc(arr[i])}<span class="del" data-idx="${i}">&times;</span>`;
    t.querySelector(".del").addEventListener("click", () => {
      arr.splice(i, 1);
      renderTags(wrap, section, key, arr, commaMode);
    });
    wrap.appendChild(t);
  }
  const btn = document.createElement("button");
  btn.className = "tag-add";
  btn.textContent = "+ 添加";
  btn.addEventListener("click", () => {
    const v = prompt("输入新值：");
    if (v && v.trim()) {
      arr.push(v.trim());
      renderTags(wrap, section, key, arr, commaMode);
    }
  });
  wrap.appendChild(btn);
}

async function save() {
  const btn = document.getElementById("btnSave");
  btn.disabled = true;
  btn.textContent = "保存中...";
  try {
    const r = await fetch("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    const result = await r.json();
    showToast(result.status === "ok" ? "保存成功" : "保存失败: " + (result.message || ""), result.status === "ok" ? "ok" : "err");
  } catch (e) {
    showToast("网络错误: " + e.message, "err");
  } finally {
    btn.disabled = false;
    btn.textContent = "保存配置";
  }
}

function showToast(msg, type) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.className = "toast " + type;
  setTimeout(() => { el.className = "toast"; }, 3000);
}

function esc(s) {
  return String(s).replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

load();
</script>
</body>
</html>"""


# ── HTTP Handler ────────────────────────────────────────────────────

class ConfigHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/api/config":
            self._send_json({
                "config": _read_json("config.json"),
                "profile": _read_json("profile.json"),
                "enums": _read_json("enums.json"),
            })
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(PAGE_HTML.encode("utf-8"))

    def do_POST(self):
        if self.path != "/api/config":
            self._send_json({"status": "error", "message": "Not Found"}, 404)
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            payload = json.loads(body)
        except json.JSONDecodeError as e:
            self._send_json({"status": "error", "message": f"JSON 解析失败: {e}"}, 400)
            return

        for filename in ("config", "profile", "enums"):
            if filename not in payload:
                self._send_json({"status": "error", "message": f"缺少 {filename} 字段"}, 400)
                return

        try:
            _write_json("config.json", payload["config"])
            _write_json("profile.json", payload["profile"])
            _write_json("enums.json", payload["enums"])
        except Exception as e:
            self._send_json({"status": "error", "message": f"写入失败: {e}"}, 500)
            return

        self._send_json({"status": "ok"})

    def _send_json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def log_message(self, format, *args):
        print(f"[{self.address_string()}] {args[0]} {args[1]} {args[2]}")


def main():
    global PORT
    args = sys.argv[1:]
    if len(args) >= 2 and args[0] == "-p":
        PORT = int(args[1])

    server = HTTPServer(("0.0.0.0", PORT), ConfigHandler)
    url = f"http://localhost:{PORT}"
    print(f"配置编辑器已启动: {url}")
    print("按 Ctrl+C 停止服务")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止")
        server.server_close()


if __name__ == "__main__":
    main()
